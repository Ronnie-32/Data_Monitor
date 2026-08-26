"""Compatibility import for the course-owned timetable-scheme repository."""

from deskboard.repositories.course_repository import CourseRepository


class TimetableSchemeRepository(CourseRepository):
    """Expose scheme operations without creating a second SQLite owner."""
