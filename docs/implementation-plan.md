# DeskBoard V1 Implementation Plan

> **For agentic workers:** Execute **one numbered task per session**. Read `AGENTS.md`, this task, and only the relevant parts of `docs/spec.md`. Do not start the next task automatically. Use TDD where applicable, systematic debugging for unexpected failures, and fresh verification evidence before any completion claim.

**Goal:** Build a stable personal-use Windows DeskBoard V1 with Todo, semester/course scheduling, Today Agenda, current-week timetable, flexible Profile-based dashboard layout, weather, validated lightweight financial reference data, native Settings, tray integration, caching/status, and a standard Windows installer.

**Architecture:** PySide6 owns the Windows shell, one QWebEngineView hosts a local HTML/CSS/ES Modules/GridStack Dashboard, QWebChannel carries commands/events, application services own business rules, thin repositories own SQLite, direct-HTTP Providers normalize external data, and native PySide6 Settings reuses the same services.

**Tech Stack:** Python 3.12.x, PySide6, Qt WebEngine, QWebChannel, requests, stdlib sqlite3/dataclasses, optional BeautifulSoup4 only if a validated source requires it, local GridStack, pytest, ruff, PyInstaller onedir, Inno Setup.

**Spec:** `docs/spec.md`

---

## Global Constraints

This section is a convenience summary only. `docs/spec.md` remains authoritative for product semantics, and `AGENTS.md` remains authoritative for agent execution behavior.

- Windows 10/11 64-bit only.
- Personal-use stability before GitHub release.
- One QWebEngineView only.
- Native PySide6 Settings; no second WebEngine.
- Local HTML/CSS/ES Modules; no CDN and no Node build pipeline.
- SQLite is the only persistent database.
- No AKShare.
- No cloud/account/sync/reminders/notifications/auto-update/portable/plugin system/multi-monitor/edge auto-hide in V1.
- All shipped network sources must work on ordinary mainland-China internet without VPN/proxy/Clash/end-user API key.
- Fixed 60-minute network refresh.
- Refresh failures preserve last successful cache.
- No short-interval automatic retry.
- One global Dashboard network-status dot.
- Dashboard layout uses 12 GridStack columns.
- Maximum 8 user Profiles plus one built-in Default.
- Python 3.12.x baseline.
- PyInstaller onedir + Inno Setup.
- Each numbered task ends in `COMPLETE`, `AWAITING_MANUAL_ACCEPTANCE`, or `BLOCKED`, then stops.

---

## Target Repository Structure

```text
DeskBoard/
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ docs/
│  ├─ spec.md
│  └─ implementation-plan.md
├─ src/deskboard/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ main.py
│  ├─ app/
│  │  ├─ application.py
│  │  ├─ modes.py
│  │  └─ startup.py
│  ├─ infrastructure/
│  │  ├─ paths.py
│  │  ├─ logging_setup.py
│  │  ├─ clock.py
│  │  ├─ workers.py
│  │  └─ autostart.py
│  ├─ database/
│  │  ├─ connection.py
│  │  ├─ schema.py
│  │  └─ migrations/
│  ├─ models/
│  │  ├─ todo.py
│  │  ├─ course.py
│  │  ├─ profile.py
│  │  ├─ weather.py
│  │  └─ finance.py
│  ├─ repositories/
│  │  ├─ todo_repository.py
│  │  ├─ course_repository.py
│  │  ├─ profile_repository.py
│  │  ├─ weather_repository.py
│  │  ├─ finance_repository.py
│  │  ├─ settings_repository.py
│  │  └─ network_repository.py
│  ├─ services/
│  │  ├─ todo_service.py
│  │  ├─ course_service.py
│  │  ├─ agenda_service.py
│  │  ├─ timetable_service.py
│  │  ├─ profile_service.py
│  │  ├─ weather_service.py
│  │  ├─ finance_service.py
│  │  ├─ settings_service.py
│  │  ├─ refresh_service.py
│  │  └─ status_service.py
│  ├─ providers/
│  │  ├─ base.py
│  │  ├─ http_client.py
│  │  ├─ errors.py
│  │  ├─ catalog.py
│  │  ├─ weather/
│  │  ├─ gold/
│  │  ├─ fx/
│  │  ├─ china_index/
│  │  └─ us_index/
│  ├─ presentation/
│  │  ├─ dashboard_state.py
│  │  ├─ todo_presenter.py
│  │  ├─ agenda_presenter.py
│  │  ├─ timetable_presenter.py
│  │  ├─ weather_presenter.py
│  │  └─ finance_presenter.py
│  └─ ui/
│     ├─ dashboard/
│     │  ├─ window.py
│     │  ├─ bridge.py
│     │  └─ web/
│     │     ├─ index.html
│     │     ├─ js/
│     │     ├─ css/
│     │     └─ vendor/gridstack/
│     ├─ settings/
│     ├─ dialogs/
│     └─ tray/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ fixtures/providers/
├─ spikes/
├─ scripts/
└─ installer/
```

The structure is a target, not permission to create empty placeholder files. Create files only when their task needs them.

---

# Phase 0 — Risk Gate

Feature implementation must not begin until Tasks 0 and 1 have sufficient acceptance evidence.

---

## Task 0: Windows / QWebEngine / Packaging Risk Spike

**Goal:** Prove the desktop-shell architecture before business-feature implementation.

### References

- `docs/spec.md`: §3 High-Level Architecture; §5 Dashboard Window Behavior; §8 Grid Layout; §24 Performance; §26 Packaging; §27.2–27.3 Manual/Phase-0 Acceptance.
- `docs/quality/requirements-traceability.md`: search `Task 0`.
- `docs/quality/test-matrix.md`: search `Task 0`.

**Files:**
- Create: `spikes/desktop_shell/main.py`
- Create: `spikes/desktop_shell/index.html`
- Create: `spikes/desktop_shell/README.md`
- Create: `spikes/desktop_shell/spike.spec`

**Produces:**
- documented Z-order behavior;
- documented pointer pass-through behavior;
- one QWebEngineView + QWebChannel + GridStack proof;
- native Settings-window coexistence proof;
- minimal PyInstaller onedir proof;
- baseline CPU/RAM observations.

**Interfaces:**
- No production interface is created. Spike code is throwaway evidence.

### Verification IDs

`MAN-PACK-01`, `MAN-PERF-01`, `MAN-PERF-02`, `MAN-WIN-01..05`, `MAN-WIN-07`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Create the minimal PySide6 shell**

Implement one frameless Dashboard window containing one QWebEngineView, one native Settings `QMainWindow`, and a simple mode toggle.

The Dashboard must be capable of applying/removing pointer pass-through and the candidate bottommost behavior.

- [ ] **Step 2: Add local WebEngine content**

Bundle a local HTML page that renders three fake widgets in a 12-column GridStack and loads QWebChannel locally.

JavaScript must send one command to Python and display one Python-originated value.

- [ ] **Step 3: Verify Dashboard topology behavior**

Resize the outer Dashboard window and confirm the fake widgets keep the same GridStack coordinates while their pixel dimensions change.

- [ ] **Step 4: Perform real Windows Z-order acceptance**

On Windows 10/11 test:

1. launch the spike;
2. open Notepad and Explorer;
3. click the desktop;
4. use Win+D and restore windows;
5. toggle pointer pass-through;
6. restart Explorer if practical;
7. verify ordinary app windows cover the Dashboard while the Dashboard remains above the desktop.

Record exact observations in `spikes/desktop_shell/README.md`.

If the required layer model cannot be achieved reliably, return `BLOCKED` and stop the project before feature tasks.

- [ ] **Step 5: Measure baseline performance**

With only three fake widgets, record:

- total DeskBoard/QtWebEngine working memory;
- idle CPU in Locked;
- idle CPU in Interaction;
- hidden-window CPU;
- number of QtWebEngine-related child processes.

Memory under roughly 200 MB is preferred but not a hard pass/fail number. Persistent non-idle CPU or continuous memory growth is a failure requiring investigation.

- [ ] **Step 6: Build the spike with PyInstaller onedir**

Build a minimal onedir package and launch the built executable.

Expected:

- WebEngine subprocess/resources resolve;
- local HTML/GridStack loads;
- QWebChannel works;
- native Settings opens;
- no runtime CDN/network dependency exists for the UI.

- [ ] **Step 7: Verify and stop**

Run focused static/lint checks if configured, preserve the spike evidence, and report:

```text
Task: 0 Windows / QWebEngine / Packaging Risk Spike
Status: COMPLETE | AWAITING_MANUAL_ACCEPTANCE | BLOCKED
Evidence: <Windows + packaging + performance evidence>
Next:
- if COMPLETE: Task 1 only;
- if AWAITING_MANUAL_ACCEPTANCE: Task 0 remains open until the required manual evidence is supplied and accepted;
- if BLOCKED: none — resolve the blocker/spec decision first.
```

Do not turn the spike into production code.

---

## Task 1: Mainland-China Provider Source Gate

**Goal:** Select viable sources before production Provider implementation.

### References

- `docs/spec.md`: §16 Finance; §17 Network Source Requirements; §27.2–27.3 Manual/Phase-0 Acceptance; §29 Public Release Gate.
- `docs/quality/requirements-traceability.md`: search `Task 1`.
- `docs/quality/test-matrix.md`: search `Task 1`.

**Files:**
- Create: `spikes/providers/check_sources.py`
- Create: `spikes/providers/README.md`
- Create: `tests/fixtures/providers/<validated-fixtures>`
- Optionally Create: `spikes/providers/check_sources.ps1`

**Produces:**
- one selected source strategy per mandatory V1 category;
- saved representative raw fixtures;
- a candidate FinanceCatalog list containing only validated items;
- explicit mainland-China direct-access evidence.

**Mandatory categories:**
- weather for mainland-China cities;
- gold;
- CNY FX;
- major A-share indices.

**Conditional category:**
- U.S. indices, only if a source passes all V1 access constraints.

**Source gate fields:**

```text
mainland direct access
no VPN/proxy/Clash dependency
no end-user API key/account
required fields available
field meaning understood
parser feasibility
error behavior
source attribution/terms note for later release review
```

### Verification IDs

`MAN-PROV-01..06`, `REV-PROV-02`, `REV-SCOPE-01`, `REV-SCOPE-06`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Implement a bounded source-check script**

The script must query only explicit candidate endpoints/pages. It must not crawl the web or dynamically discover arbitrary sources.

Print bounded normalized samples and concise errors.

- [ ] **Step 2: Validate weather**

Prove a source can provide at least:

```text
condition
current temperature
high
low
wind
```

for representative mainland-China cities.

- [ ] **Step 3: Validate gold**

Prove a selected source can provide Au99.99 or the approved V1 gold reference item with clear units.

- [ ] **Step 4: Validate FX**

Prove the selected source can provide the approved CNY reference fields and document any upstream quotation basis such as per-100-unit values.

- [ ] **Step 5: Validate A-share indices**

Prove selected source(s) can provide the intended major index items and meaningful value/change fields.

- [ ] **Step 6: Validate U.S. indices conditionally**

Attempt a mainland-China-direct source for Dow/S&P 500/Nasdaq candidate items.

If no source meets V1 constraints, mark U.S. items deferred; do not add proxy support and do not block the rest of V1.

- [ ] **Step 7: Save fixtures**

Save representative raw response fixtures for every selected parser path. Fixtures must allow normal parser tests without live internet.

- [ ] **Step 8: Perform real mainland-China access acceptance**

Run source checks on ordinary mainland-China internet with VPN/proxy/Clash disabled.

If the agent environment cannot truthfully prove this, return `AWAITING_MANUAL_ACCEPTANCE` with exact commands and expected evidence.

- [ ] **Step 9: Verify and stop**

Write the selected-source matrix to `spikes/providers/README.md`.

Report:

```text
Task: 1 Mainland-China Provider Source Gate
Status: COMPLETE | AWAITING_MANUAL_ACCEPTANCE | BLOCKED
Selected sources: <groups/items>
Deferred items: <if any>
Next:
- if COMPLETE: Task 2 only;
- if AWAITING_MANUAL_ACCEPTANCE: Task 1 remains open until mainland-China direct-access evidence is supplied and accepted;
- if BLOCKED: none — resolve the blocker/spec decision first.
```

---

# Phase 1 — Application Foundation

---

## Task 2: Project Skeleton, Modes, Paths, and Logging

**Goal:** Establish a minimal importable/runnable DeskBoard package plus deterministic project metadata, application modes, local paths, and bounded logging before creating GUI lifecycle code.

### References

- `docs/spec.md`: §2 V1 Scope; §3 High-Level Architecture; §4 Runtime Files and Persistence; §5.3 Operating Modes; §23 Logging; §25 Dependencies.
- `docs/quality/requirements-traceability.md`: search `Task 2`.
- `docs/quality/test-matrix.md`: search `Task 2`.

**Files:**
- Create/Modify: `pyproject.toml`
- Create: `src/deskboard/__init__.py`
- Create: `src/deskboard/__main__.py`
- Create: `src/deskboard/main.py`
- Create: `src/deskboard/app/modes.py`
- Create: `src/deskboard/infrastructure/paths.py`
- Create: `src/deskboard/infrastructure/logging_setup.py`
- Create: `tests/unit/app/test_modes.py`
- Create: `tests/unit/infrastructure/test_paths.py`
- Create: `tests/unit/infrastructure/test_logging_setup.py`

**Produces:**
- `AppMode = LOCKED | INTERACTION | LAYOUT_EDIT`;
- `%LOCALAPPDATA%\DeskBoard` path helpers;
- bounded rotating-log bootstrap;
- package entry point that can initialize infrastructure without implementing product features.

**Interfaces:**

```python
class AppMode(Enum):
    LOCKED = "locked"
    INTERACTION = "interaction"
    LAYOUT_EDIT = "layout_edit"
```

### Verification IDs

`AUT-APP-01`, `AUT-INFRA-01..04`, `REV-ARCH-01`, `REV-DEP-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tests for legal modes, LOCALAPPDATA path construction, directory creation, and bounded log-file placement**
- [ ] **Step 2: Run focused tests and confirm expected red state**
- [ ] **Step 3: Implement package metadata, package entry points, modes, paths, and logging bootstrap only**
- [ ] **Step 4: Run focused tests**
- [ ] **Step 5: Run `ruff check` on touched Python**
- [ ] **Step 6: Stop**

Acceptance:

- no Dashboard, Settings, tray, Todo, Course, Provider, or database feature is implemented yet;
- logs resolve under `%LOCALAPPDATA%\DeskBoard\logs`;
- application data paths are centralized rather than reconstructed throughout the codebase.


---

## Task 3: Application Shell, Dashboard Window, and Native Settings Window

**Goal:** Create the production application lifecycle shell with one Dashboard QWebEngineView and one native Settings window, using the architecture proven by Task 0.

### References

- `docs/spec.md`: §3 High-Level Architecture; §5 Dashboard Window Behavior; §19 Settings Window.
- `docs/quality/requirements-traceability.md`: search `Task 3`.
- `docs/quality/test-matrix.md`: search `Task 3`.

**Files:**
- Create: `src/deskboard/app/application.py`
- Create: `src/deskboard/ui/dashboard/window.py`
- Create: `src/deskboard/ui/dashboard/bridge.py`
- Create: `src/deskboard/ui/dashboard/web/index.html`
- Create: `src/deskboard/ui/settings/window.py`
- Create: `tests/unit/app/test_application_lifecycle.py`
- Create: `tests/integration/test_dashboard_bridge_shell.py`
- Modify: `src/deskboard/main.py`

**Produces:**
- `DeskBoardApplication` lifecycle owner;
- one frameless Dashboard window with exactly one QWebEngineView;
- one normal native PySide6 Settings window;
- minimal QWebChannel bridge shell;
- legal Locked/Interaction/Layout Edit mode application plumbing without domain rules.

### Verification IDs

`MAN-SET-01`, `MAN-WIN-02`, `MAN-WIN-03`, `MAN-WIN-05`, `MAN-WIN-06`, `REV-ARCH-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write lifecycle tests that are Qt-independent where practical**
- [ ] **Step 2: Write a minimal bridge-shell contract test**
- [ ] **Step 3: Implement `DeskBoardApplication` without Todo/Course/Provider logic**
- [ ] **Step 4: Implement Dashboard window and local HTML shell using the Task 0 validated approach**
- [ ] **Step 5: Implement native Settings window open/close semantics; closing Settings must not exit DeskBoard**
- [ ] **Step 6: Apply legal app modes to shell state, but do not add GridStack layout editing yet**
- [ ] **Step 7: Run focused tests and `ruff check`**
- [ ] **Step 8: Perform a bounded Windows smoke test proving Dashboard/Settings coexist and only one QWebEngineView exists**
- [ ] **Step 9: Stop**

Acceptance:

- app starts and Dashboard appears;
- Settings can open/close without exiting;
- Dashboard contains one QWebEngineView only;
- no tray or single-instance behavior is required until Task 4;
- no domain/business feature is implemented.


---

## Task 4: Tray, Single Instance, and Shell Acceptance

**Goal:** Complete the application-shell operating behavior without adding domain features.

### References

- `docs/spec.md`: §5 Dashboard Window Behavior; §6 System Tray; §27.2 Real Windows Acceptance.
- `docs/quality/requirements-traceability.md`: search `Task 4`.
- `docs/quality/test-matrix.md`: search `Task 4`.

**Files:**
- Create: `src/deskboard/ui/tray/tray_icon.py`
- Create: `src/deskboard/app/single_instance.py`
- Modify: `src/deskboard/app/application.py`
- Modify: `src/deskboard/main.py`
- Create: `tests/unit/app/test_single_instance_contract.py`
- Create: `tests/unit/ui/test_tray_action_contract.py`

**Produces:**
- tray left-click opens Settings;
- tray right-click supports Show/Hide, Locked/Interaction switch, Settings, Exit;
- one-instance guard using `QLocalServer` / `QLocalSocket`;
- second launch asks the existing instance to open/focus Settings, then exits.

### Verification IDs

`AUT-SINGLE-01`, `AUT-TRAY-01`, `MAN-TRAY-01..04`, `MAN-WIN-04`, `MAN-WIN-05`, `MAN-WIN-07`, `MAN-WIN-09`, `MAN-WIN-10`, `REV-ARCH-01`, `REV-SCOPE-01`, `REV-SCOPE-03`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tray-action and single-instance contract tests where Qt-independent**
- [ ] **Step 2: Implement tray behavior without Profile/refresh/layout-edit actions**
- [ ] **Step 3: Implement single-instance guard and second-launch handoff**
- [ ] **Step 4: Run focused tests and `ruff check`**
- [ ] **Step 5: Perform real Windows shell acceptance: Show/Hide, Locked/Interaction, Settings, Exit, and second-launch behavior**
- [ ] **Step 6: Stop**

Acceptance:

- second process never creates a second Dashboard/tray/refresh lifecycle;
- tray remains intentionally minimal;
- Dashboard shell behavior still matches Task 0's validated Windows layering strategy.


---

## Task 5: SQLite Schema, Migrations, Repository Ownership, and Clock

**Goal:** Establish the complete V1 persistence schema, explicit persistence ownership, SQLite-only application configuration rule, and deterministic time abstraction.

### References

- `docs/spec.md`: §3.5 Repositories; §4 Runtime Files and Persistence; §20 Time Semantics; §21 Database Model.
- `docs/quality/requirements-traceability.md`: search `Task 5`.
- `docs/quality/test-matrix.md`: search `Task 5`.

**Files:**
- Create: `src/deskboard/infrastructure/clock.py`
- Create: `src/deskboard/database/connection.py`
- Create: `src/deskboard/database/schema.py`
- Create: `src/deskboard/database/migrations/v001_initial.py`
- Create: `src/deskboard/repositories/settings_repository.py`
- Create: `tests/unit/database/test_schema.py`
- Create: `tests/unit/database/test_migrations.py`
- Create: `tests/unit/infrastructure/test_clock.py`

**Produces:**
- all V1 tables from `docs/spec.md`;
- foreign-key-enabled connection factory;
- `schema_version`;
- `SystemClock` and test `FakeClock` pattern.

**Interfaces:**

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
    def today(self) -> date: ...
```

### Verification IDs

`AUT-DB-01..16`, `AUT-TIME-01..04`, `REV-ARCH-01`, `REV-DB-01..03`, `REV-SCOPE-01`, `REV-SCOPE-02`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tests for schema creation, foreign keys, and schema version**
- [ ] **Step 2: Write failing tests for key uniqueness/cascade constraints**
- [ ] **Step 3: Write failing settings/path guard tests proving DeskBoard-owned persistent user configuration uses SQLite and the foundation does not create QSettings/JSON/YAML/TOML as a second config store; Windows autostart registry integration is exempt**
- [ ] **Step 4: Implement `connection.py` and migration v001**
- [ ] **Step 5: Implement minimal settings key/value repository**
- [ ] **Step 6: Implement `SystemClock`; tests use a deterministic fake**
- [ ] **Step 7: Run database/clock/ownership tests**
- [ ] **Step 8: Verify a fresh application data directory auto-creates the database**
- [ ] **Step 9: Stop**

Acceptance includes all logical tables listed in the spec and no legacy `schedule_items`, backup table, or generic event table.

Persistence ownership for all later tasks:

| Repository | Owned table(s) |
|---|---|
| `SettingsRepository` | `app_settings` |
| `TodoRepository` | `todos` |
| `CourseRepository` | `semesters`, `recurring_courses`, `course_cancellations`, `one_off_courses`, `class_periods` |
| `ProfileRepository` | `profiles`, `profile_widgets` |
| `WeatherRepository` | `weather_cities` only |
| `FinanceRepository` | `finance_preferences` only |
| `NetworkRepository` | `network_cache`, `network_state` only |

Weather/Finance payload cache must never be moved into `WeatherRepository` or `FinanceRepository`.


---

# Phase 2 — Todo

---

## Task 6: Todo Domain, Repository, and Service

**Goal:** Implement all Todo business semantics independent of UI.

### References

- `docs/spec.md`: §11 Todo Domain; §20 Time Semantics; §21 Database Model.
- `docs/quality/requirements-traceability.md`: search `Task 6`.
- `docs/quality/test-matrix.md`: search `Task 6`.

**Files:**
- Create: `src/deskboard/models/todo.py`
- Create: `src/deskboard/repositories/todo_repository.py`
- Create: `src/deskboard/services/todo_service.py`
- Create: `tests/unit/repositories/test_todo_repository.py`
- Create: `tests/unit/services/test_todo_service.py`

**Produces:**

```python
TodoService.add_quick(content: str) -> Todo
TodoService.update(todo_id: int, update: TodoUpdate) -> Todo
TodoService.set_completed(todo_id: int, completed: bool) -> Todo
TodoService.delete(todo_id: int) -> None
TodoService.restore(todo_id: int) -> Todo
TodoService.reorder(ordered_ids: list[int]) -> None
TodoService.get_dashboard_items() -> list[Todo]
TodoService.get_completed_history() -> list[Todo]
TodoService.get_for_date(day: date) -> list[Todo]
```

### Verification IDs

`AUT-TIME-01..04`, `AUT-TODO-01..22`, `REV-ARCH-01`, `REV-SCOPE-01`, `REV-TODO-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tests for quick-add/top ordering**
- [ ] **Step 2: Write failing tests for today-completed visibility and next-day disappearance**
- [ ] **Step 3: Write failing tests for Deadline date/time default semantics**
- [ ] **Step 4: Write failing tests for planned date/point/range semantics and validation**
- [ ] **Step 5: Write failing repository transaction/reorder tests**
- [ ] **Step 6: Implement the minimal models/repository/service**
- [ ] **Step 7: Run Todo tests**
- [ ] **Step 8: Run relevant DB regression tests**
- [ ] **Step 9: Stop**

No UI changes belong in this task.

---

## Task 7: Todo Presenter and Dashboard Interaction

**Goal:** Expose the high-frequency Todo behavior on the Dashboard without yet implementing native detailed editing/history UI.

### References

- `docs/spec.md`: §5.3 Operating Modes; §11.5–11.8 Todo Widget/Interaction; §22 QWebChannel Contract.
- `docs/quality/requirements-traceability.md`: search `Task 7`.
- `docs/quality/test-matrix.md`: search `Task 7`.

**Files:**
- Create: `src/deskboard/presentation/todo_presenter.py`
- Modify: `src/deskboard/ui/dashboard/bridge.py`
- Create: `src/deskboard/ui/dashboard/web/js/widgets/todo.js`
- Create/Modify: `src/deskboard/ui/dashboard/web/css/widgets.css`
- Create: `tests/unit/presentation/test_todo_presenter.py`
- Create: `tests/integration/test_todo_bridge_contract.py`

**Produces bridge semantics:**

```text
addQuickTodo(content)
toggleTodo(todo_id)
reorderTodos(ordered_ids)
todosChanged(payload)
```

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-PRES-01..07`, `MAN-TODO-01..04`, `MAN-UI-06`, `MAN-UI-07`, `REV-ARCH-01..03`, `REV-SCOPE-01`, `REV-TODO-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write presenter contract tests**
- [ ] **Step 2: Write bridge/service integration tests where Qt-independent**
- [ ] **Step 3: Implement Todo presenter**
- [ ] **Step 4: Implement quick-add, checkbox, drag-order, and Todo content scrolling**
- [ ] **Step 5: Implement completed-today and overdue visual states from Python-provided ViewModel fields**
- [ ] **Step 6: Run focused automated verification**
- [ ] **Step 7: Perform bounded Interaction/Locked acceptance for add/check/reorder/scroll**
- [ ] **Step 8: Stop**

Acceptance:

- `+` only asks for content;
- new item appears at the top;
- completed-today item stays in place and uses pale-green/check style;
- previous-day completed items are absent from Dashboard;
- Interaction scrolling works; Locked remains true Windows pointer-through;
- detailed edit/delete/history UI is intentionally deferred to Task 8.


---

## Task 8: Todo Native Editor, Delete Confirmation, and Settings History

**Goal:** Add the lower-frequency native Todo management surfaces while reusing the Task 6 service and Task 7 presenter/bridge model.

### References

- `docs/spec.md`: §11.6–11.8 Todo Interaction/Settings/Style; §19 Settings Window; §22.2 QWebChannel Commands.
- `docs/quality/requirements-traceability.md`: search `Task 8`.
- `docs/quality/test-matrix.md`: search `Task 8`.

**Files:**
- Create: `src/deskboard/ui/dialogs/todo_editor.py`
- Create: `src/deskboard/ui/settings/todo_page.py`
- Modify: `src/deskboard/ui/dashboard/bridge.py`
- Modify: `src/deskboard/ui/dashboard/web/js/widgets/todo.js`
- Create: `tests/unit/ui/test_todo_editor_validation.py`
- Create: `tests/integration/test_todo_management_contract.py`

**Produces bridge semantics:**

```text
openTodoEditor(todo_id)
requestDeleteTodo(todo_id)
```

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-TODO-01..22`, `MAN-SET-04`, `MAN-TODO-05`, `REV-ARCH-01`, `REV-SCOPE-01`, `REV-TODO-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing editor validation tests for deadline/planned-date/point/range semantics where Qt-independent**
- [ ] **Step 2: Implement the native Todo editor using Qt date/time controls**
- [ ] **Step 3: Implement right-click `Edit details`, complete/uncomplete, and `Delete` commands**
- [ ] **Step 4: Implement native delete confirmation before permanent delete**
- [ ] **Step 5: Implement Settings Todo page with explicit Incomplete and Completed-history lists**
- [ ] **Step 6: Implement restore-to-incomplete and confirmed permanent delete from completed history**
- [ ] **Step 7: Run focused automated verification**
- [ ] **Step 8: Perform bounded native dialog/Settings manual acceptance**
- [ ] **Step 9: Stop**

Acceptance:

- single-click Todo text does not become the primary edit gesture;
- detailed editing is native Qt;
- delete always confirms;
- completed history can be viewed, restored, and permanently deleted;
- Dashboard and Settings both reuse the same TodoService.


---

# Phase 3 — Semester, Courses, Agenda, Timetable

---

## Task 9: Semester and Course Domain

**Goal:** Implement semester, recurring course, cancellation, one-off course, and global period business rules.

### References

- `docs/spec.md`: §12 Semester and Course Domain; §20 Time Semantics; §21 Database Model.
- `docs/quality/requirements-traceability.md`: search `Task 9`.
- `docs/quality/test-matrix.md`: search `Task 9`.

**Files:**
- Create: `src/deskboard/models/course.py`
- Create: `src/deskboard/repositories/course_repository.py`
- Create: `src/deskboard/services/course_service.py`
- Create: `tests/unit/repositories/test_course_repository.py`
- Create: `tests/unit/services/test_course_service.py`

**Produces:**

```python
CourseService.get_teaching_week(day: date) -> int | None
CourseService.get_occurrences_for_date(day: date) -> list[CourseOccurrence]
CourseService.get_occurrences_for_week(day: date) -> list[CourseOccurrence]
CourseService.cancel_occurrence(course_id: int, occurrence_date: date) -> None
```

plus CRUD methods required by Settings for semesters/courses/one-offs/periods.

### Verification IDs

`AUT-COURSE-01..25`, `AUT-TIME-01..04`, `REV-ARCH-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tests for Monday-based teaching-week calculation and prove zero active semester is valid, one active semester is valid, and two active semesters cannot be represented**
- [ ] **Step 2: Write failing recurring-course occurrence tests**
- [ ] **Step 3: Write failing cancellation tests**
- [ ] **Step 4: Write failing one-off/reschedule tests, including outside teaching range: `get_teaching_week()` returns `None`, recurring occurrence is absent, and a matching explicit-date one-off remains present**
- [ ] **Step 5: Write failing global-period validation tests proving a saved active configuration must contain exactly unique period numbers 1..8, rejects partial/duplicate/0/9 configurations, and requires `end_time > start_time`; an initially unconfigured set is valid and must not invent default school times**
- [ ] **Step 6: Implement repository/service minimally**
- [ ] **Step 7: Run Course tests**
- [ ] **Step 8: Run relevant database cascade tests**
- [ ] **Step 9: Stop**

Acceptance:

- active-semester state is valid with zero or one active semester only;
- a configured global class-period set is exactly periods 1..8; a fresh unconfigured state is allowed until Settings saves all eight;
- outside teaching range, recurring courses are absent while matching one-off courses remain eligible;
- no odd/even-week logic;
- no persisted current-week field;
- `start_monday` must be Monday;
- periods are global and courses retain actual times.

---

## Task 10: Agenda and Timetable Domain/Presentation

**Goal:** Derive Today Agenda and current-week timetable data without persisting a generic event model.

### References

- `docs/spec.md`: §11.4 Planned-Time Semantics; §12 Semester/Course; §13 Today Agenda; §14 Weekly Timetable; §20 Time Semantics; §22.4 Presentation Models.
- `docs/quality/requirements-traceability.md`: search `Task 10`.
- `docs/quality/test-matrix.md`: search `Task 10`.

**Files:**
- Create: `src/deskboard/services/agenda_service.py`
- Create: `src/deskboard/services/timetable_service.py`
- Create: `src/deskboard/presentation/agenda_presenter.py`
- Create: `src/deskboard/presentation/timetable_presenter.py`
- Create: `tests/unit/services/test_agenda_service.py`
- Create: `tests/unit/services/test_timetable_service.py`
- Create: `tests/unit/presentation/test_timetable_presenter.py`

**Produces:**

```python
AgendaService.get_today(day: date) -> Agenda
TimetableService.get_current_week(day: date) -> TimetableWeek
```

Timetable events include semantic metadata such as:

```text
type
date
start
end
time_kind
completed
conflict
```

but no CSS pixels.

### Verification IDs

`AUT-AGENDA-01..11`, `AUT-PRES-01..07`, `AUT-TIME-01..04`, `AUT-TT-01..21`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-DB-03`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tests for timed Course/Todo merge order**
- [ ] **Step 2: Write failing tests for date-only Todos after timed items**
- [ ] **Step 3: Write failing tests proving Deadline-only Todos do not enter Agenda**
- [ ] **Step 4: Write failing timetable tests for point/range/date-only Todos**
- [ ] **Step 5: Write failing overlap/conflict metadata tests**
- [ ] **Step 6: Write failing week-label/header-mode tests, including blank week label outside teaching range and a configuration-required timetable state when global period bounds are not yet configured**
- [ ] **Step 7: Write failing visible-range tests proving events wholly outside period-1-start through period-8-end are excluded from the weekly timetable ViewModel**
- [ ] **Step 8: Implement services/presenters**
- [ ] **Step 9: Run focused tests and relevant Todo/Course regressions**
- [ ] **Step 10: Stop**

No Agenda or generic Schedule table may be created.

---

## Task 11: Dashboard State Snapshot and Today Agenda Widget

**Goal:** Build the coarse Python-owned Dashboard state flow and render Today Agenda as a pure, view-only widget.

### References

- `docs/spec.md`: §7 Built-In Widgets; §13 Today Agenda; §22 QWebChannel Contract.
- `docs/quality/requirements-traceability.md`: search `Task 11`.
- `docs/quality/test-matrix.md`: search `Task 11`.

**Files:**
- Create: `src/deskboard/presentation/dashboard_state.py`
- Modify: `src/deskboard/ui/dashboard/bridge.py`
- Create/Modify: `src/deskboard/ui/dashboard/web/index.html`
- Create: `src/deskboard/ui/dashboard/web/js/app.js`
- Create: `src/deskboard/ui/dashboard/web/js/bridge.js`
- Create: `src/deskboard/ui/dashboard/web/js/store.js`
- Create: `src/deskboard/ui/dashboard/web/js/widgets/agenda.js`
- Create/Modify: `src/deskboard/ui/dashboard/web/css/widgets.css`
- Create: `tests/unit/presentation/test_dashboard_state.py`
- Create: `tests/integration/test_dashboard_state_bridge.py`

**Produces bridge semantics:**

```text
requestInitialState()
stateChanged
agendaChanged
modeChanged
```

### Verification IDs

`AUT-AGENDA-01..11`, `AUT-BRIDGE-01..08`, `AUT-PRES-01..07`, `AUT-STATE-01`, `AUT-STATE-02`, `MAN-AGENDA-01`, `MAN-UI-07`, `MAN-UI-08`, `REV-ARCH-01..03`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write state-snapshot presentation tests**
- [ ] **Step 2: Write bridge tests proving one coarse initial state request rather than many fine-grained getters**
- [ ] **Step 3: Implement the thin JavaScript render-state mirror/store**
- [ ] **Step 4: Implement Today Agenda pure rendering from Python-owned ViewModels**
- [ ] **Step 5: Keep Agenda rows view-only and preserve past-today items without auto-hide/grey**
- [ ] **Step 6: Run automated verification**
- [ ] **Step 7: Perform bounded visual/manual acceptance of Today Agenda**
- [ ] **Step 8: Stop**

Acceptance:

- JavaScript does not calculate Todo overdue, teaching week, or Agenda ordering;
- Today Agenda contains no edit/complete/delete actions;
- no weekly overlay is implemented until Task 12.


---

## Task 12: Weekly Timetable Overlay

**Goal:** Render the current-week Monday–Sunday timetable overlay from Task 10's Python-owned Timetable ViewModel.

### References

- `docs/spec.md`: §5.3 Operating Modes; §12–14 Course/Agenda/Timetable; §22 QWebChannel Contract; §27.2 Manual Acceptance.
- `docs/quality/requirements-traceability.md`: search `Task 12`.
- `docs/quality/test-matrix.md`: search `Task 12`.

**Files:**
- Modify: `src/deskboard/ui/dashboard/bridge.py`
- Modify: `src/deskboard/ui/dashboard/web/js/widgets/agenda.js`
- Create: `src/deskboard/ui/dashboard/web/js/timetable.js`
- Create: `src/deskboard/ui/dashboard/web/css/timetable.css`
- Create: `tests/integration/test_timetable_bridge_contract.py`

**Produces bridge semantics:**

```text
requestWeeklyTimetable()
```

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-PRES-01..07`, `AUT-TT-01..21`, `MAN-AGENDA-01`, `MAN-TT-01..07`, `MAN-UI-07`, `MAN-UI-09`, `REV-ARCH-01..03`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write bridge-contract tests for requesting the current-week Timetable ViewModel**
- [ ] **Step 2: Implement title-click timetable opening in Interaction Mode only**
- [ ] **Step 3: Implement Monday–Sunday overlay and all three header modes**
- [ ] **Step 4: Implement real-time percentage vertical positioning from the visible timetable bounds**
- [ ] **Step 5: Implement course, point-Todo, range-Todo, completed-Todo, and overlap/conflict visual variants**
- [ ] **Step 6: Prove events outside visible bounds are not rendered even if malformed/out-of-range data reaches the UI boundary**
- [ ] **Step 7: Run automated bridge verification**
- [ ] **Step 8: Perform visual/manual Windows acceptance**
- [ ] **Step 9: Stop**

Acceptance:

- current week only; no previous/next week navigation;
- non-teaching-week week label is blank;
- past current-week events remain rendered normally;
- single-point Todo is not given fake duration;
- the overlay reuses the one existing QWebEngineView.


---

# Phase 4 — Profiles and Layout

---

## Task 13: Profile Domain and Persistence

**Goal:** Implement Profile persistence and management rules without yet implementing GridStack editing or visual theme tuning.

### References

- `docs/spec.md`: §7 Built-In Widgets; §8 Grid Layout; §9 Profiles; §10 Themes; §21 Database Model.
- `docs/quality/requirements-traceability.md`: search `Task 13`.
- `docs/quality/test-matrix.md`: search `Task 13`.

**Files:**
- Create: `src/deskboard/models/profile.py`
- Create: `src/deskboard/repositories/profile_repository.py`
- Create: `src/deskboard/services/profile_service.py`
- Create: `tests/unit/services/test_profile_service.py`
- Create: `tests/unit/repositories/test_profile_repository.py`

**Produces:**

```python
ProfileService.switch(profile_id: int) -> ProfileState
ProfileService.save_current(state: ProfileState) -> None
ProfileService.save_as(name: str, state: ProfileState) -> Profile
ProfileService.rename(profile_id: int, name: str) -> None
ProfileService.delete(profile_id: int) -> None
ProfileService.restore_default() -> ProfileState
```

Profile state covers Dashboard geometry, widget geometry/visibility, theme key, opacity, and widget display config. Business data, city list, primary city, finance preferences, and network cache remain global.

### Verification IDs

`AUT-PROFILE-01..16`, `MAN-LAYOUT-03`, `REV-ARCH-01`, `REV-PROFILE-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing tests for built-in Default Profile creation/protection**
- [ ] **Step 2: Write failing tests for the maximum-eight-user-Profile rule**
- [ ] **Step 3: Write failing tests for Profile/widget persistence and last-profile selection**
- [ ] **Step 4: Write failing tests for Save As, rename, delete-active→Default fallback, switch, and restore-default behavior**
- [ ] **Step 5: Implement the minimal model/repository/service**
- [ ] **Step 6: Run focused Profile tests and relevant database regression tests**
- [ ] **Step 7: Stop**

Acceptance:

- built-in Default does not count toward the eight-user limit;
- Default cannot be overwritten or deleted;
- a Profile contains only visual/spatial state;
- finance enabled/order and weather city/primary-city settings are not stored in Profile;
- no GridStack DOM behavior or Settings page is implemented yet.

---

## Task 14: GridStack Layout Editing and Dashboard Geometry

**Goal:** Implement the approved 12-column layout editor, Dashboard move/resize behavior, Save/Cancel snapshot semantics, and Profile application.

### References

- `docs/spec.md`: §5.2–5.3 Dashboard Window/Modes; §8 Grid Layout; §9 Profiles; §22 QWebChannel Contract.
- `docs/quality/requirements-traceability.md`: search `Task 14`.
- `docs/quality/test-matrix.md`: search `Task 14`.

**Files:**
- Modify: `src/deskboard/ui/dashboard/window.py`
- Modify: `src/deskboard/ui/dashboard/bridge.py`
- Create: `src/deskboard/ui/dashboard/web/js/layout.js`
- Create/Modify: `src/deskboard/ui/dashboard/web/js/app.js`
- Create: `src/deskboard/ui/dashboard/web/css/layout.css`
- Create: `tests/integration/test_layout_bridge_contract.py`
- Modify relevant Profile/application tests

**Produces bridge semantics:**

```text
enterLayoutEdit()
saveLayout(layout_state)
cancelLayoutEdit()
profileChanged(profile_state)
modeChanged(mode)
```

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-LAYOUT-01`, `AUT-PROFILE-01..16`, `MAN-LAYOUT-01..03`, `MAN-WIN-06`, `REV-ARCH-01`, `REV-ARCH-03`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write tests for entering Layout Edit from Locked and Interaction modes**
- [ ] **Step 2: Write tests proving Save and Cancel both restore the recorded previous daily mode**
- [ ] **Step 3: Write bridge-contract tests for one layout snapshot/save transaction**
- [ ] **Step 4: Implement fixed 12-column GridStack topology with move/resize disabled outside Layout Edit**
- [ ] **Step 5: Implement outer Dashboard move/resize only in Layout Edit**
- [ ] **Step 6: Implement pre-edit snapshot, Save, and Cancel without continuous SQLite writes while dragging; when built-in Default is active, Save must use a small native Save-As-Profile prompt rather than overwrite Default**
- [ ] **Step 7: Apply Profile widget geometry/visibility and Dashboard geometry on switch/restart**
- [ ] **Step 8: Verify outer-window resize changes cell pixels but does not responsive-reflow widget topology**
- [ ] **Step 9: Run automated verification**
- [ ] **Step 10: Perform real GridStack/Windows manual acceptance**
- [ ] **Step 11: Stop**

Use only conservative technical minimum geometry in this task. Do not invent final readability minimums; Task 23 owns them after all real widget types exist.

---

# Phase 5 — Network Foundation and Weather

---

## Task 15: Network Cache, Refresh, and Global Status Foundation

**Goal:** Implement the generic low-frequency network pipeline before adding production Weather/Finance providers.

### References

- `docs/spec.md`: §3.5–3.6 Repositories/Providers; §18 Refresh, Cache, and Status; §21.2 Cache/State Separation; §24 Performance.
- `docs/quality/requirements-traceability.md`: search `Task 15`.
- `docs/quality/test-matrix.md`: search `Task 15`.

**Files:**
- Create: `src/deskboard/providers/base.py`
- Create: `src/deskboard/providers/http_client.py`
- Create: `src/deskboard/providers/errors.py`
- Create: `src/deskboard/repositories/network_repository.py`
- Create: `src/deskboard/services/refresh_service.py`
- Create: `src/deskboard/services/status_service.py`
- Create/Modify: `src/deskboard/services/settings_service.py`
- Create: `src/deskboard/infrastructure/workers.py`
- Create: `tests/unit/repositories/test_network_repository.py`
- Create: `tests/unit/services/test_refresh_service.py`
- Create: `tests/unit/services/test_status_service.py`

**Required semantics:**

```text
60-minute fixed auto refresh
successful payload cache separate from attempt/error state
fresh cache skips startup refetch
stale/no cache triggers background refresh
partial provider-group success is allowed
failure never overwrites successful payload
no short retry loop
no connectivity gate
one in-flight request per provider group
Dashboard hidden does not stop refresh
status = grey while an active enabled-data refresh is unresolved
status = green when all enabled items last resolved successfully
status = red when any enabled item failed
```

### Verification IDs

`AUT-NET-01..29`, `AUT-PROV-01`, `MAN-NET-01`, `MAN-NET-02`, `MAN-PERF-04`, `MAN-UI-14`, `REV-ARCH-01`, `REV-PROV-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write failing cache/state separation tests**
- [ ] **Step 2: Write failing startup-freshness and 60-minute scheduling tests using FakeClock**
- [ ] **Step 3: Write failing partial-success/failure-preserves-cache tests**
- [ ] **Step 4: Write failing status tests proving disabled items do not participate, zero enabled/configured network items => grey, fresh-cache startup restores persisted prior success/failure as green/red, and the global dot color is derived rather than persisted directly**
- [ ] **Step 5: Write failing single-in-flight-provider-group tests**
- [ ] **Step 6: Write a test proving Dashboard visibility is not part of refresh scheduling decisions**
- [ ] **Step 7: Implement bounded synchronous HTTP client plus QThreadPool/QRunnable execution**
- [ ] **Step 8: Implement repository/services with no retry queue and no async framework**
- [ ] **Step 9: Run focused tests and relevant DB regressions**
- [ ] **Step 10: Stop**

No production endpoint-specific parsing belongs in this task.

---

## Task 16: Weather Provider and City Domain

**Goal:** Implement the validated Weather source, normalized model, and global city configuration domain without Dashboard rendering.

### References

- `docs/spec.md`: §15 Weather; §17 Network Source Requirements; §21 Database Model; §25 Dependencies.
- `docs/quality/requirements-traceability.md`: search `Task 16`.
- `docs/quality/test-matrix.md`: search `Task 16`.

**Files:**
- Create: `src/deskboard/models/weather.py`
- Create: `src/deskboard/repositories/weather_repository.py`
- Create: `src/deskboard/services/weather_service.py`
- Create: `src/deskboard/providers/weather/provider.py`
- Create parser/resolver files only if the selected Task 1 source justifies them
- Create: `tests/unit/repositories/test_weather_repository.py`
- Create: `tests/unit/services/test_weather_service.py`
- Create: `tests/unit/providers/test_weather_parser.py`

**Required fields:**

```text
condition
current temperature
high
low
wind
```

**Persistence boundary:** `WeatherRepository` owns `weather_cities` only. Weather payload cache/state always belongs to `NetworkRepository`.

### Verification IDs

`AUT-PROV-01`, `AUT-WTH-01..09`, `MAN-PROV-01`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write parser tests against Task 1 raw fixtures**
- [ ] **Step 2: Write city-order/primary-city tests, including exactly one primary city when cities exist**
- [ ] **Step 3: Implement the validated provider and normalized Weather model**
- [ ] **Step 4: Implement WeatherRepository/WeatherService for global city list/order/primary-city configuration only**
- [ ] **Step 5: Run focused tests and repository-ownership regressions**
- [ ] **Step 6: Perform a bounded live smoke request against the already-approved source**
- [ ] **Step 7: Stop**

Acceptance:

- city list/order/primary city are global rather than Profile-owned;
- no weather payload is stored by WeatherRepository;
- no Weather Dashboard widget/presenter is implemented until Task 17;
- overseas cities remain optional/non-blocking.


---

## Task 17: Weather Presenter, Dashboard Widget, and Refresh Integration

**Goal:** Connect Task 16 Weather data to Task 15 network/cache/status services and render the approved Weather widget.

### References

- `docs/spec.md`: §7 Built-In Widgets; §15 Weather; §18 Refresh/Cache/Status; §22 QWebChannel Contract; §24 Performance.
- `docs/quality/requirements-traceability.md`: search `Task 17`.
- `docs/quality/test-matrix.md`: search `Task 17`.

**Files:**
- Create: `src/deskboard/presentation/weather_presenter.py`
- Create: `src/deskboard/ui/dashboard/web/js/widgets/weather.js`
- Modify: `src/deskboard/presentation/dashboard_state.py`
- Modify: `src/deskboard/ui/dashboard/bridge.py`
- Modify: `src/deskboard/ui/dashboard/web/js/app.js`
- Modify: `src/deskboard/ui/dashboard/web/css/widgets.css`
- Create: `tests/unit/presentation/test_weather_presenter.py`
- Create: `tests/integration/test_weather_refresh_integration.py`

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-PRES-01..07`, `AUT-PROV-01`, `AUT-WTH-01..09`, `MAN-NET-01`, `MAN-UI-10`, `MAN-UI-11`, `REV-ARCH-01..03`, `REV-PROV-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write presenter tests for primary-city compact display and expanded single-city/multi-city modes**
- [ ] **Step 2: Write integration tests proving Weather refresh success uses NetworkRepository cache/state and failure preserves last successful payload**
- [ ] **Step 3: Integrate Weather provider group with Task 15 refresh/status services**
- [ ] **Step 4: Implement Weather widget without provider-specific fields in JavaScript**
- [ ] **Step 5: Implement global grey/green/red status-dot rendering if not already visible in the shell; do not add per-widget dots or timestamps**
- [ ] **Step 6: Verify multi-city order follows global city order and truncates to available capacity without forced scrolling**
- [ ] **Step 7: Run automated tests**
- [ ] **Step 8: Perform bounded live/visual acceptance**
- [ ] **Step 9: Stop**


---

# Phase 6 — Finance

---

## Task 18: Finance Catalog and Global Preferences

**Goal:** Define only Task 1 validated finance items and implement global enable/order preferences independently of provider/widget code.

### References

- `docs/spec.md`: §16 Finance; §21 Database Model.
- `docs/quality/requirements-traceability.md`: search `Task 18`.
- `docs/quality/test-matrix.md`: search `Task 18`.

**Files:**
- Create: `src/deskboard/models/finance.py`
- Create: `src/deskboard/providers/catalog.py`
- Create: `src/deskboard/repositories/finance_repository.py`
- Create: `src/deskboard/services/finance_service.py`
- Create: `tests/unit/repositories/test_finance_repository.py`
- Create: `tests/unit/services/test_finance_service.py`
- Create: `tests/unit/providers/test_finance_catalog.py`

**FinanceCatalog entries include:**

```text
stable DeskBoard item key
display name
category
unit/format metadata
provider group
provider-internal mapping
source name/homepage attribution metadata
```

### Verification IDs

`AUT-FIN-01..15`, `AUT-PROV-01`, `REV-ARCH-01`, `REV-PROV-01`, `REV-SCOPE-01`, `REV-SCOPE-05`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Encode only the Task 1 validated whitelist; do not add speculative items**
- [ ] **Step 2: Write repository/service tests for enable/disable and display order**
- [ ] **Step 3: Write tests proving preferences are global and not Profile-owned**
- [ ] **Step 4: Write tests proving disabled items do not participate in global network status**
- [ ] **Step 5: Implement minimal repository/service; `FinanceRepository` owns `finance_preferences` only and must never store market payload/cache data**
- [ ] **Step 6: Run focused tests plus a persistence-boundary regression proving finance payload/cache state remains owned by `NetworkRepository`**
- [ ] **Step 7: Stop**

No arbitrary ticker/security input or dynamic market catalog loading is allowed. Finance market payloads/cache never belong to `FinanceRepository`.

---

## Task 19: Gold and CNY FX Providers

**Goal:** Implement the validated Gold and FX parser/provider paths with normalized DeskBoard-owned results.

### References

- `docs/spec.md`: §16 Finance; §17 Network Source Requirements; §18 Refresh/Cache/Status; §25 Dependencies.
- `docs/quality/requirements-traceability.md`: search `Task 19`.
- `docs/quality/test-matrix.md`: search `Task 19`.

**Files:**
- Create: `src/deskboard/providers/gold/provider.py`
- Create parser file only if useful
- Create: `src/deskboard/providers/fx/provider.py`
- Create parser file only if useful
- Create: `tests/unit/providers/test_gold_parser.py`
- Create: `tests/unit/providers/test_fx_parser.py`
- Create: `tests/integration/test_gold_fx_refresh.py`

### Verification IDs

`AUT-FX-01..04`, `AUT-PROV-01`, `MAN-PROV-02`, `MAN-PROV-03`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write Gold parser tests from Task 1 fixtures including unit sanity checks**
- [ ] **Step 2: Write FX parser tests from Task 1 fixtures including any per-100-unit normalization selected in Task 1**
- [ ] **Step 3: Implement the minimal validated provider/parser paths**
- [ ] **Step 4: Add basic invalid/zero/missing-value sanity rejection**
- [ ] **Step 5: Integrate with Task 15 cache/status pipeline**
- [ ] **Step 6: Run automated tests**
- [ ] **Step 7: Perform one bounded mainland-China live smoke check**
- [ ] **Step 8: Stop**

Do not add runtime fallback chains.

---

## Task 20: China Index Provider

**Goal:** Implement only the Task 1 validated A-share index sources/items.

### References

- `docs/spec.md`: §16 Finance; §17 Network Source Requirements; §18 Refresh/Cache/Status; §25 Dependencies.
- `docs/quality/requirements-traceability.md`: search `Task 20`.
- `docs/quality/test-matrix.md`: search `Task 20`.

**Files:**
- Create: `src/deskboard/providers/china_index/provider.py`
- Create parser/source-specific internal files only where necessary
- Create: `tests/unit/providers/test_china_index_parser.py`
- Create: `tests/integration/test_china_index_refresh.py`

### Verification IDs

`AUT-PROV-01`, `MAN-PROV-04`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write parser tests from every selected A-share fixture path**
- [ ] **Step 2: Implement normalized value/change extraction without leaking source field names upward**
- [ ] **Step 3: Add minimal invalid-data sanity checks**
- [ ] **Step 4: Integrate with Task 15 cache/status pipeline**
- [ ] **Step 5: Run automated tests**
- [ ] **Step 6: Perform one bounded mainland-China live smoke check**
- [ ] **Step 7: Stop**

Using more than one official source internally is acceptable if Task 1 selected that strategy; upper layers still receive one normalized model.

---

## Task 21: U.S. Index Provider or Explicit V1 Deferral

**Goal:** Implement U.S. indices only if Task 1 produced a mainland-China-direct, no-account/no-key accepted source; otherwise close the task by implementing/confirming the approved unavailable state.

### References

- `docs/spec.md`: §16 Finance; §17 Network Source Requirements; §18 Refresh/Cache/Status; §25 Dependencies; §29 Public Release Gate.
- `docs/quality/requirements-traceability.md`: search `Task 21`.
- `docs/quality/test-matrix.md`: search `Task 21`.

**Files:**
- Conditionally Create: `src/deskboard/providers/us_index/provider.py`
- Conditionally Create parser files
- Create/Modify tests for the validated provider or deferred-catalog behavior

**Branch A — source validated in Task 1:**

### Verification IDs

`AUT-PROV-01`, `MAN-PROV-05`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1A: Write parser tests from Task 1 fixtures**
- [ ] **Step 2A: Implement the validated normalized provider**
- [ ] **Step 3A: Integrate with Task 15 cache/status pipeline**
- [ ] **Step 4A: Run automated tests and one bounded mainland-China live smoke check**

**Branch B — no acceptable source in Task 1:**

- [ ] **Step 1B: Verify no U.S.-index catalog items are enabled/shipped**
- [ ] **Step 2B: Verify the reserved `us_indices` widget type can remain hidden/unavailable without status failures or proxy prompts**

- [ ] **Final Step: Stop**

Do not add VPN/proxy configuration, end-user API keys/accounts, or a weaker source merely to avoid deferral.

---

## Task 22: Finance Presenter and Dashboard Widgets

**Goal:** Present the enabled global finance whitelist through Gold, FX, China-index, optional U.S.-index, and combined Finance Overview widgets without duplicate network requests.

### References

- `docs/spec.md`: §7 Built-In Widgets; §16 Finance; §18 Refresh/Cache/Status; §22 QWebChannel Contract.
- `docs/quality/requirements-traceability.md`: search `Task 22`.
- `docs/quality/test-matrix.md`: search `Task 22`.

**Files:**
- Create: `src/deskboard/presentation/finance_presenter.py`
- Create: `src/deskboard/ui/dashboard/web/js/widgets/finance.js`
- Modify relevant Dashboard state/ViewModel files
- Create: `tests/unit/presentation/test_finance_presenter.py`
- Create: `tests/integration/test_finance_dashboard_state.py`

**Required ViewModel semantics:**

```text
key
category
name
valueText
changePercentText where relevant
direction = up | down | flat | unknown
marketState = open | closed | unknown
secondaryText = "上一交易日收盘" only when reliably justified
```

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-FIN-01..15`, `AUT-PRES-01..07`, `MAN-NET-01`, `MAN-UI-05`, `MAN-UI-12`, `MAN-UI-13`, `REV-ARCH-01..03`, `REV-SCOPE-01`, `REV-SCOPE-05`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write presenter tests for formatting/category filtering/order**
- [ ] **Step 2: Write tests proving individual and overview widgets share one finance state/cache path**
- [ ] **Step 3: Write tests for closed/unknown market labels; unknown must not be falsely labeled as previous-close**
- [ ] **Step 4: Implement normalized presenter and Dashboard state integration**
- [ ] **Step 5: Implement minimal no-chart/no-scroll finance renderers**
- [ ] **Step 6: Implement size-based visible-item count using global preference order**
- [ ] **Step 7: Verify Chinese-market red-up/green-down styling**
- [ ] **Step 8: Run automated and bounded visual acceptance**
- [ ] **Step 9: Stop**

Widget duplication is visual only and must never schedule duplicate Provider requests.

---

# Phase 7 — Visual Baseline and Settings

---

## Task 23: Dashboard Visual Baseline, Themes, and Readability Gate

**Goal:** Close the intentionally deferred visual/readability decisions after all real V1 widget types can be rendered.

### References

- `docs/spec.md`: §5.2 Dashboard Window; §8 Grid Layout; §10 Themes; §24 Performance; §27.2 Manual Acceptance.
- `docs/quality/requirements-traceability.md`: search `Task 23`.
- `docs/quality/test-matrix.md`: search `Task 23`.

**Files:**
- Create: `docs/ui-readability-baseline.md`
- Create/Modify: `src/deskboard/ui/dashboard/web/css/base.css`
- Modify: `src/deskboard/ui/dashboard/web/css/layout.css`
- Create/Modify: `src/deskboard/ui/dashboard/web/css/themes.css`
- Modify relevant widget CSS/JS only for size-adaptive presentation
- Modify Profile display-config handling only where required by approved visual modes

**Must establish and record:**

- default Profile visual arrangement;
- overall Dashboard minimum width/height;
- final minimum readable size for each built-in widget type;
- pixel thresholds used for compact/normal/expanded presentation where a widget needs them;
- panel spacing/dividers/outer rounding baseline;
- four light themes: Mist Blue, Mint Breeze, Almond Sand, Lavender Cloud;
- Profile opacity behavior;
- completed Todo pale-green/check treatment;
- financial red-up/green-down treatment;
- weekly timetable course/Todo distinction and point/range readability.

### Verification IDs

`AUT-PROFILE-01..16`, `MAN-PERF-06`, `MAN-TODO-03`, `MAN-TT-07`, `MAN-UI-01..14`, `REV-ARCH-01`, `REV-PERF-01`, `REV-SCOPE-01`, `REV-UI-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Render all real V1 widget types with representative fixture/local data**
- [ ] **Step 2: Establish the smallest readable Dashboard and per-widget sizes by visual acceptance rather than arbitrary constants**
- [ ] **Step 3: Record accepted values/rationale in `docs/ui-readability-baseline.md`**
- [ ] **Step 4: Implement the four light themes and shared visual tokens**
- [ ] **Step 5: Implement size-adaptive widget presentation using actual pixel size; do not persist generic compact/normal/expanded state**
- [ ] **Step 6: Verify transparent outer window, semi-transparent panel regions, subtle separators, minimal shadows, and no continuous decorative animation**
- [ ] **Step 7: Perform visual/manual acceptance at representative small/normal/large Dashboard sizes**
- [ ] **Step 8: Stop**

If the agent cannot truthfully judge the required visual acceptance in its environment, return `AWAITING_MANUAL_ACCEPTANCE` with screenshots/steps to check; do not guess final minimums.

---

## Task 24: General, Profile, Weather, and Finance Settings

**Goal:** Build the first half of the native PySide6 Settings UI around already-tested services.

### References

- `docs/spec.md`: §5.3–5.4 Modes/Startup; §6 System Tray; §9 Profiles; §15–16 Weather/Finance; §19 Settings; §26 Packaging/Autostart.
- `docs/quality/requirements-traceability.md`: search `Task 24`.
- `docs/quality/test-matrix.md`: search `Task 24`.

**Files:**
- Modify: `src/deskboard/ui/settings/window.py`
- Create: `src/deskboard/ui/settings/general_page.py`
- Create: `src/deskboard/ui/settings/profile_page.py`
- Create: `src/deskboard/ui/settings/weather_page.py`
- Create: `src/deskboard/ui/settings/finance_page.py`
- Create: `src/deskboard/infrastructure/autostart.py`
- Add focused tests for non-visual settings/service decisions

**Required behavior:**

- Settings uses native PySide6 Widgets, never a second QWebEngineView;
- Profile switching/Save/Save As/rename/delete/restore-default exists only here;
- at most 8 user Profiles plus built-in Default;
- city list/order/primary city management is global;
- finance whitelist enable/order management is global;
- General includes Dashboard show/hide, Locked/Interaction mode, enter Layout Edit, autostart, exit;
- simple settings apply immediately; structured Profile operations have explicit actions;
- autostart exists but defaults OFF.

### Verification IDs

`AUT-SET-01`, `MAN-SET-01..03`, `MAN-SET-08..11`, `MAN-WIN-03`, `MAN-WIN-10`, `REV-ARCH-01`, `REV-DB-02`, `REV-SCOPE-01`, `REV-SCOPE-03`, `REV-SCOPE-06`, `REV-SCOPE-07`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Implement Settings sidebar/stack entries for General, Profiles, Weather, Finance**
- [ ] **Step 2: Implement General controls using App/Settings services**
- [ ] **Step 3: Implement Profile management against ProfileService only**
- [ ] **Step 4: Implement Weather global city/primary controls against WeatherService only**
- [ ] **Step 5: Implement Finance whitelist/order controls against FinanceService only**
- [ ] **Step 6: Implement current-user Windows autostart toggle**
- [ ] **Step 7: Run focused automated verification**
- [ ] **Step 8: Perform native Settings manual smoke test**
- [ ] **Step 9: Stop**

---

## Task 25: Todo, Course, Data Status, and About Settings

**Goal:** Complete the native Settings pages without duplicating domain business logic.

### References

- `docs/spec.md`: §11.7 Todo Settings; §12 Semester/Course; §18.6–18.7 Manual Refresh/Status; §19 Settings Window.
- `docs/quality/requirements-traceability.md`: search `Task 25`.
- `docs/quality/test-matrix.md`: search `Task 25`.

**Files:**
- Modify: `src/deskboard/ui/settings/window.py`
- Modify/Create: `src/deskboard/ui/settings/todo_page.py`
- Create: `src/deskboard/ui/settings/course_page.py`
- Create: `src/deskboard/ui/settings/data_status_page.py`
- Create: `src/deskboard/ui/settings/about_page.py`
- Add focused tests for settings-facing service logic where deterministic

**Required behavior:**

- Todo page has separate Incomplete and Completed-history views;
- completed history can restore or permanently delete with confirmation;
- Course page manages semester, active semester, recurring courses, cancellations, one-offs, global periods 1–8, and timetable header mode;
- Data Status shows source/group, last attempt, last success, status, last readable error, attribution, Refresh All, per-group Refresh, Open Log Folder;
- About shows app/version/basic disclaimer/source references;
- closing Settings does not exit DeskBoard;
- structured object editors use Save/Cancel.

### Verification IDs

`AUT-SET-01`, `AUT-SET-02`, `MAN-SET-01`, `MAN-SET-04..07`, `MAN-SET-10`, `MAN-SET-12`, `MAN-SET-13`, `MAN-TT-02`, `MAN-TT-04`, `MAN-WIN-03`, `REV-ARCH-01`, `REV-DB-02`, `REV-SCOPE-01`, `REV-SCOPE-04`, `REV-SCOPE-07`, `REV-SCOPE-08`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Complete Todo Incomplete/Completed-history UI using TodoService**
- [ ] **Step 2: Implement semester/course/period/cancellation/one-off editors using CourseService**
- [ ] **Step 3: Implement Data Status with manual refresh controls and diagnostic state; verify the Dashboard itself exposes no refresh control**
- [ ] **Step 4: Implement About/version page**
- [ ] **Step 5: Run focused automated verification**
- [ ] **Step 6: Perform native Settings manual smoke test**
- [ ] **Step 7: Stop**

No Settings page may directly query SQL or call a Provider.

---

# Phase 8 — Runtime, Packaging, Stability, Release

---

## Task 26: Startup, Day Rollover, Window Recovery, and Windows Behavior Hardening

**Goal:** Finalize runtime restoration and long-lived Windows behavior after all main features exist.

### References

- `docs/spec.md`: §5.4 Startup Behavior; §18 Refresh/Cache/Status; §20 Time Semantics; §24 Performance; §26 Packaging/Autostart.
- `docs/quality/requirements-traceability.md`: search `Task 26`.
- `docs/quality/test-matrix.md`: search `Task 26`.

**Files:**
- Modify: `src/deskboard/app/application.py`
- Create/Modify: `src/deskboard/app/startup.py`
- Modify: `src/deskboard/ui/dashboard/window.py`
- Modify: `src/deskboard/infrastructure/clock.py`
- Add focused tests for pure startup/day-rollover decisions

### Verification IDs

`AUT-BRIDGE-01..08`, `AUT-NET-01..29`, `AUT-START-01..06`, `AUT-TIME-01..04`, `MAN-NET-01`, `MAN-PACK-07`, `MAN-PACK-08`, `MAN-PERF-05`, `MAN-WIN-04`, `MAN-WIN-06`, `MAN-WIN-08`, `MAN-WIN-11`, `MAN-WIN-12`, `REV-DB-02`, `REV-PERF-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Write tests for first-run vs later-run mode/Profile decisions**
- [ ] **Step 2: Write tests proving process restart from last Layout Edit restores Interaction**
- [ ] **Step 3: Write tests for visible-on-every-launch behavior**
- [ ] **Step 4: Implement first-run Settings-open-once state**
- [ ] **Step 5: Implement Python-side local-midnight/day-rollover refresh of Todo/Agenda/Course-derived state**
- [ ] **Step 6: Implement primary-work-area geometry recovery only when saved Dashboard is fully off-screen**
- [ ] **Step 7: Reapply the Task 0 validated Z-order/pointer state after relevant Windows events where required**
- [ ] **Step 8: Verify Dashboard hide/show preserves the single QWebEngineView and hide does not stop 60-minute network updates**
- [ ] **Step 9: Run automated tests**
- [ ] **Step 10: Perform bounded real-Windows acceptance**
- [ ] **Step 11: Stop**

Do not turn off-screen recovery into multi-monitor V1 support.

---

## Task 27: Production Packaging and Installer

**Goal:** Produce the standard Windows installer using the already-proven PyInstaller onedir architecture.

### References

- `docs/spec.md`: §4 Runtime Files; §24 Performance; §25 Dependencies; §26 Packaging; §27 Testing/Acceptance.
- `docs/quality/requirements-traceability.md`: search `Task 27`.
- `docs/quality/test-matrix.md`: search `Task 27`.

**Files:**
- Create/Modify: `installer/deskboard.spec`
- Create: `installer/deskboard.iss`
- Create: `scripts/build.ps1`
- Create: `scripts/smoke_test.ps1`
- Modify: `pyproject.toml` version metadata as needed

### Verification IDs

`MAN-PACK-01..09`, `MAN-WIN-01`, `REV-DEP-01`, `REV-SCOPE-01`, `REV-SCOPE-02`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Build PyInstaller onedir with all local WebEngine/Web/GridStack resources**
- [ ] **Step 2: Verify the built application from a clean test directory**
- [ ] **Step 3: Create the Inno Setup installer**
- [ ] **Step 4: Verify install/start/uninstall**
- [ ] **Step 5: Verify `%LOCALAPPDATA%\DeskBoard` database/log behavior**
- [ ] **Step 6: Verify normal operation requires no administrator privilege**
- [ ] **Step 7: Verify installed-build autostart toggle**
- [ ] **Step 8: Verify uninstall does not silently erase personal data**
- [ ] **Step 9: Run full automated test/lint suite and bounded installer smoke checklist**
- [ ] **Step 10: Stop**

V1 ships no portable build and no automatic updater.

---

## Task 28: Stability and Performance Manual Acceptance Gate

**Goal:** Freeze feature scope, prepare/execute bounded automated smoke checks, and collect real personal-use long-run evidence without keeping an agent session alive for hours or days.

### References

- `docs/spec.md`: §24 Performance; §27 Testing/Acceptance; §28 V1 Completion Definition.
- `docs/quality/requirements-traceability.md`: search `Task 28`.
- `docs/quality/test-matrix.md`: search `Task 28`.

**Files:**
- Create: `docs/v1-stability-checklist.md`
- Modify production code only for a verified bug/performance issue discovered from concrete evidence; if a fix becomes a substantive implementation/debugging task, stop this acceptance task and ask for a separate user-authorized session rather than expanding Task 28.

**Acceptance scenarios:**

```text
Locked idle
Interaction idle
Dashboard hidden
60-minute refresh
network disconnect/reconnect
provider failure with cache fallback
sleep/wake
cross midnight
Sunday → Monday
cross teaching-week boundary
manual system-time change
multiple Profile switches
Layout Edit Save/Cancel
Settings open/close repeatedly
multi-hour / multi-day personal-use memory trend
```

### Verification IDs

`MAN-PERF-01..07`, `MAN-STAB-01..08`, `REV-DONE-01`, `REV-PERF-01`, `REV-SCOPE-01`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Run the full automated suite and production-build smoke checks before manual stability testing**
- [ ] **Step 2: Record a bounded baseline CPU/RAM snapshot for Locked, Interaction, hidden, and active-refresh states**
- [ ] **Step 3: Write exact manual procedures, expected results, evidence fields, and failure-report format into `docs/v1-stability-checklist.md`**
- [ ] **Step 4: Run only bounded acceptance checks that fit the current session**
- [ ] **Step 5: For multi-hour/multi-day, sleep/wake, and naturally occurring boundary cases that cannot be truthfully observed now, report `AWAITING_MANUAL_ACCEPTANCE`; do not wait, poll, or keep the session running**
- [ ] **Step 6: When user evidence is later supplied, classify each scenario PASS/FAIL and use systematic debugging only for concrete failures**
- [ ] **Step 7: Record known bounded limitations and accepted CPU/RAM observations**
- [ ] **Step 8: Stop**

A stable working-memory value slightly above the preferred ~200 MB guideline is not automatically a failure. Continuous substantial memory growth or persistent non-idle CPU is a blocker.

---

## Task 29: Documentation and Public Release Gate

**Goal:** Prepare for public GitHub release only after Task 28 personal-use stability evidence is accepted.

### References

- `docs/spec.md`: §17.3 Release Review; §26 Packaging; §28 Completion Definition; §29 Public GitHub Release Gate.
- `docs/quality/requirements-traceability.md`: search `Task 29`.
- `docs/quality/test-matrix.md`: search `Task 29`.

**Files:**
- Modify/Create: `README.md`
- Create: `docs/data-sources.md`
- Create: `docs/release-checklist.md`
- Modify installer/version metadata only as needed

### Verification IDs

`MAN-REL-01..06`, `REV-SCOPE-01`, `REV-SCOPE-08`

Use only the matching case definitions from `docs/quality/test-matrix.md`; do not load the whole matrix by default.

- [ ] **Step 1: Re-check every shipped network source for mainland-China direct access without VPN/proxy/Clash/account/API key**
- [ ] **Step 2: Review current attribution/redistribution/commercial terms for every shipped data source**
- [ ] **Step 3: Remove/replace/defer any source not acceptable for the intended public-release model**
- [ ] **Step 4: Document data sources and disclaimers**
- [ ] **Step 5: Document installation, startup modes, Settings, Profiles, Todo/course workflow, and troubleshooting/log location**
- [ ] **Step 6: Verify no API keys, secrets, private local data, or developer-only paths are included**
- [ ] **Step 7: Build and smoke-test the release installer**
- [ ] **Step 8: Run final automated verification**
- [ ] **Step 9: Stop before push/publish/release unless the user explicitly authorizes the external side effect**

---

# Plan-Wide Verification Map

| Requirement area | Primary task(s) | Verification |
|---|---:|---|
| Windows layer/pass-through | 0, 4, 26 | real Windows acceptance |
| One WebEngine/QWebChannel viability | 0, 3, 11-12 | spike + shell + bridge integration |
| Tray/single instance | 4 | unit contracts + real Windows smoke |
| GridStack topology/editing | 0, 14 | spike + bridge/manual acceptance |
| UI readability/minimums/themes | 23 | visual/readability gate |
| PyInstaller WebEngine viability | 0, 27 | built executable |
| Mainland-China source gate | 1, 16, 19-21, 29 | real direct-network acceptance |
| SQLite/migrations/ownership | 5 | unit/repository tests |
| Todo semantics | 6-8, 25 | unit + Dashboard/native Settings acceptance |
| Course semantics | 9, 25 | unit/repository + Settings acceptance |
| Agenda/timetable semantics | 10-12, 23 | unit + visual acceptance |
| Profiles/persistence | 13 | unit/repository tests |
| Layout/Profile application | 14 | bridge + restart/manual acceptance |
| Network cache/refresh/status | 15 | service/repository tests |
| Weather | 16-17 | fixture/domain/presenter + bounded live smoke |
| Finance catalog/preferences | 18 | unit tests |
| Gold/FX | 19 | fixture + bounded live smoke |
| China indices | 20 | fixture + bounded live smoke |
| U.S. indices | 21 | validated source or explicit deferral |
| Finance UI | 22-23 | presenter/state + visual acceptance |
| Native Settings | 24-25 | focused tests + native manual smoke |
| Startup/day rollover | 26 | pure tests + real runtime |
| Installer | 27 | clean install smoke |
| Long-run stability | 28 | user/manual checklist + metrics |
| Public release | 29 | source/legal/docs gate |

---

# Task Execution Rule

For every numbered task:

1. read `AGENTS.md`;
2. read this task;
3. read only the relevant `docs/spec.md` sections;
4. inspect only direct code/interfaces/tests;
5. establish failing tests first where deterministic behavior applies; an expected TDD red failure is not a debugging incident;
6. implement the smallest compliant change;
7. use systematic debugging for unexpected failures;
8. obey the 3-fix, no-progress, and task-complexity circuit breakers;
9. run fresh task verification;
10. report exactly `COMPLETE`, `AWAITING_MANUAL_ACCEPTANCE`, or `BLOCKED`;
11. **STOP**.

Do not begin the next numbered task automatically. Long-running manual acceptance must not be converted into an hours-long agent wait/poll loop.
