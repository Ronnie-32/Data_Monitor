"""Profile management rules independent of Settings and Dashboard UI."""

from __future__ import annotations

from dataclasses import replace

from deskboard.infrastructure.clock import Clock
from deskboard.models.profile import (
    DEFAULT_PROFILE_NAME,
    MAX_USER_PROFILES,
    PROFILE_FONT_KEYS,
    PROFILE_THEME_KEYS,
    Profile,
    ProfileState,
)
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository

ACTIVE_PROFILE_SETTING = "active_profile_id"
PROFILE_ONE_NAMES = frozenset({"1", "方案1", "1方案", "方案一", "一方案", "profile1"})


class ProfileError(ValueError):
    """Base class for user-facing Profile rule violations."""


class BuiltinProfileError(ProfileError):
    """Raised when a caller tries to mutate or delete built-in Default."""


class ProfileLimitError(ProfileError):
    """Raised when the maximum number of user Profiles has been reached."""


class ProfileService:
    def __init__(
        self,
        repository: ProfileRepository,
        clock: Clock,
        settings_repository: SettingsRepository | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._settings = settings_repository or SettingsRepository(repository.connection)
        default = self._repository.ensure_default(ProfileState(), self._clock.now())
        self._active_profile_id = self._load_active_profile_id(default.id)
        self._restore_default_from_profile_one(default.id)

    @property
    def active_profile_id(self) -> int:
        return self._active_profile_id

    @property
    def current_profile(self) -> Profile:
        return self._repository.require(self._active_profile_id)

    @property
    def default_profile(self) -> Profile:
        default = self._repository.get_builtin()
        if default is None:
            raise LookupError("Built-in Default Profile does not exist")
        return default

    def list_profiles(self) -> list[Profile]:
        return self._repository.list_profiles()

    def get(self, profile_id: int) -> Profile:
        return self._repository.require(profile_id)

    def switch(self, profile_id: int) -> ProfileState:
        profile = self._repository.require(profile_id)
        self._set_active_profile(profile.id)
        return profile.state

    def save_current(self, state: ProfileState) -> None:
        profile = self.current_profile
        if profile.is_builtin:
            raise BuiltinProfileError("Default Profile cannot be overwritten; use Save As")
        self._repository.save_state(profile.id, state, self._clock.now())

    def save_as(self, name: str, state: ProfileState) -> Profile:
        name = self._validate_name(name)
        self._ensure_user_capacity()
        try:
            profile = self._repository.create(name, state, self._clock.now())
        except Exception as error:
            if "UNIQUE constraint failed" in str(error):
                raise ProfileError(f"Profile name already exists: {name}") from error
            raise
        self._set_active_profile(profile.id)
        return profile

    def rename(self, profile_id: int, name: str) -> None:
        profile = self._repository.require(profile_id)
        if profile.is_builtin:
            raise BuiltinProfileError("Default Profile cannot be renamed")
        name = self._validate_name(name, exclude_profile_id=profile_id)
        try:
            self._repository.rename(profile_id, name, self._clock.now())
        except Exception as error:
            if "UNIQUE constraint failed" in str(error):
                raise ProfileError(f"Profile name already exists: {name}") from error
            raise

    def delete(self, profile_id: int) -> None:
        profile = self._repository.require(profile_id)
        if profile.is_builtin:
            raise BuiltinProfileError("Default Profile cannot be deleted")
        self._repository.delete(profile_id)
        if profile_id == self._active_profile_id:
            self._set_active_profile(self.default_profile.id)

    def restore_default(self) -> ProfileState:
        return self.switch(self.default_profile.id)

    @staticmethod
    def supported_themes() -> tuple[str, ...]:
        return PROFILE_THEME_KEYS

    @staticmethod
    def list_supported_themes() -> tuple[str, ...]:
        return PROFILE_THEME_KEYS

    @staticmethod
    def supported_fonts() -> tuple[str, ...]:
        return PROFILE_FONT_KEYS

    @staticmethod
    def list_supported_fonts() -> tuple[str, ...]:
        return PROFILE_FONT_KEYS

    def _ensure_user_capacity(self) -> None:
        user_count = sum(not profile.is_builtin for profile in self._repository.list_profiles())
        if user_count >= MAX_USER_PROFILES:
            raise ProfileLimitError(
                f"At most {MAX_USER_PROFILES} user Profiles may exist in addition to Default"
            )

    def _validate_name(self, name: str, *, exclude_profile_id: int | None = None) -> str:
        if not isinstance(name, str):
            raise TypeError("Profile name must be a string")
        normalized = name.strip()
        if not normalized:
            raise ValueError("Profile name must not be empty")
        if normalized.casefold() == DEFAULT_PROFILE_NAME.casefold():
            raise BuiltinProfileError("Default is reserved for the built-in Profile")
        for profile in self._repository.list_profiles():
            same_name = profile.name.casefold() == normalized.casefold()
            if profile.id != exclude_profile_id and same_name:
                raise ProfileError(f"Profile name already exists: {normalized}")
        return normalized

    def _load_active_profile_id(self, default_id: int) -> int:
        stored = self._settings.get(ACTIVE_PROFILE_SETTING)
        try:
            profile_id = int(stored) if stored is not None else default_id
        except (TypeError, ValueError):
            profile_id = default_id
        if self._repository.get(profile_id) is None:
            profile_id = default_id
        self._settings.set(ACTIVE_PROFILE_SETTING, str(profile_id))
        return profile_id

    def _set_active_profile(self, profile_id: int) -> None:
        self._repository.require(profile_id)
        self._active_profile_id = profile_id
        self._settings.set(ACTIVE_PROFILE_SETTING, str(profile_id))

    def _restore_default_from_profile_one(self, default_id: int) -> None:
        """Synchronize Default's Dashboard layout from the user's Profile 1.

        Default remains a protected built-in Profile; this startup repair only
        replaces its window/widget layout so an incomplete template cannot hide
        widgets or use stale geometry. Default's appearance remains untouched;
        the source Profile is never modified and remains editable.
        """

        candidates = [
            profile
            for profile in self._repository.list_profiles()
            if not profile.is_builtin and _is_profile_one_name(profile.name)
        ]
        if not candidates:
            return
        source = next(
            (profile for profile in candidates if profile.id == self._active_profile_id),
            candidates[0],
        )
        default = self._repository.require(default_id)
        restored_state = replace(
            default.state,
            window_x=source.state.window_x,
            window_y=source.state.window_y,
            window_width=source.state.window_width,
            window_height=source.state.window_height,
            widgets=source.state.widgets,
        )
        if default.state != restored_state:
            self._repository.save_state(default.id, restored_state, self._clock.now())


def _is_profile_one_name(name: str) -> bool:
    normalized = "".join(name.casefold().split())
    return normalized in PROFILE_ONE_NAMES
