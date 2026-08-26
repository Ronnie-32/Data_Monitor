# DeskBoard V1 Test Matrix and Manual Acceptance Checklist

**Status:** Supporting verification reference  
**Authority:** This file does **not** override `docs/spec.md`, `docs/implementation-plan.md`, or `AGENTS.md`.

## Purpose

This file turns the approved V1 specification into concrete verification cases so an implementation agent does not need to invent test coverage during each task.

### Usage rules

- For one numbered task, search this file by the task number and run/read only the relevant cases.
- Automated tests should be implemented with the smallest deterministic fixtures possible.
- Normal `pytest` must never require live internet.
- A manual case that the agent cannot truthfully perform keeps the owning task in `AWAITING_MANUAL_ACCEPTANCE`.
- Long-running stability checks are performed by the user outside an agent session; the agent must not wait/poll for hours.
- Exact test file locations below are recommended organizational targets, not a product-semantic source of truth.

## Status vocabulary

For each case during execution:

```text
NOT_RUN
PASS
FAIL
BLOCKED
NOT_APPLICABLE
```

`NOT_APPLICABLE` is valid only when the specification explicitly allows deferral, such as U.S. indices after the mainland-source gate.

## Automated / Review Matrix

| ID | Type | Task(s) | Area | Scenario / Action | Expected Result | Suggested Location | Notes |
|---|---|---|---|---|---|---|---|
| AUT-APP-01 | Automated | 2 | Application modes | Construct/serialize legal AppMode values and reject/avoid undocumented values. | Exactly locked, interaction, layout_edit are available. | tests/unit/app/test_modes.py |  |
| AUT-INFRA-01 | Automated | 2 | Paths | Resolve LOCALAPPDATA root and create DeskBoard/data/logs paths under a temporary LOCALAPPDATA. | All paths resolve under supplied LOCALAPPDATA; directories are created without Program Files dependence. | tests/unit/infrastructure/test_paths.py |  |
| AUT-INFRA-02 | Automated | 2 | Logging | Initialize rotating logging in a temporary logs directory. | deskboard.log is created and handler is bounded/rotating. | tests/unit/infrastructure/test_logging_setup.py |  |
| AUT-INFRA-03 | Automated | 2 | Logging | Emit representative startup/provider/SQLite error records. | Useful fault records are written with context. | tests/unit/infrastructure/test_logging_setup.py |  |
| AUT-INFRA-04 | Automated | 2 | Logging | Exercise normal/high-frequency-style helper paths without fault conditions. | No mouse/render/heartbeat noise is emitted by application logging APIs. | tests/unit/infrastructure/test_logging_setup.py | Review complements this test. |
| AUT-TRAY-01 | Automated | 4 | Tray command mapping | Build tray menu/action model. | Only show/hide, locked/interaction, open settings, exit actions exist; no profile/layout/refresh/finance actions. | tests/unit/ui/test_tray_actions.py |  |
| AUT-SINGLE-01 | Automated | 4 | Single instance | Simulate primary/secondary instance IPC/lock path. | Secondary instance signals existing instance to focus/open Settings, then exits; no second app state is created. | tests/unit/app/test_single_instance.py |  |
| AUT-DB-01 | Automated | 5 | Repository ownership | Inspect repository table-access contracts/mappings. | Each repository accesses only its owned tables; Weather/Finance config repositories do not own network payload cache. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-02 | Automated | 5 | Foreign keys | Open test DB and query PRAGMA foreign_keys. | Foreign keys are ON. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-03 | Automated | 5 | Schema version | Create a fresh DB. | schema_meta exists and current schema version is recorded. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-04 | Automated | 5 | Migrations | Migrate from supported prior test schema to current. | Migration is ordered, deterministic, and reaches current version. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-05 | Automated | 5 | Transactions | Force an exception during a multi-row reorder/profile save transaction. | No partial state remains after rollback. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-06 | Automated | 5 | Transactions | Commit a valid multi-row/multi-table operation. | All intended rows change atomically. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-07 | Automated | 5 | SQLite-only config | Persist representative app setting/profile/city/finance preference. | Persistent app-owned configuration is retrievable from SQLite; no QSettings/JSON/YAML/TOML persistence adapter is required. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-08 | Automated | 5 | Logical schema | List user tables after v001 creation. | Exactly the approved V1 logical tables exist, excluding SQLite internals. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-09 | Automated | 5 | Cancellation uniqueness | Insert same (recurring_course_id, occurrence_date) twice. | Second insert fails/normalizes to one logical cancellation. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-10 | Automated | 5 | Class period constraint | Attempt period_no 0 and 9. | Out-of-range values are rejected. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-11 | Automated | 5 | Profile widget uniqueness | Insert duplicate (profile_id, widget_key). | Duplicate is rejected. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-12 | Automated | 5 | Semester cascade | Delete confirmed semester with recurring/cancellation/one-off children. | Child course-domain rows are removed. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-13 | Automated | 5 | Recurring cascade | Delete recurring course with cancellations. | Its cancellation rows are removed. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-14 | Automated | 5 | Profile cascade | Delete user Profile with profile_widgets. | Widget rows are removed. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-15 | Automated | 5 | No generic soft delete | Inspect schema/repositories for generic deleted_at/trash behavior. | No generic soft-delete mechanism exists for approved hard-delete entities. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-DB-16 | Automated | 5 | User Profile limit ownership | Create Profiles through service/repository boundary. | Persistence supports Default + user rows; max-8 rule is enforced by service, not hidden duplicate storage. | tests/unit/database/ or tests/unit/repositories/ |  |
| AUT-TODO-01 | Automated | 6,8 | Todo model | Create Todo with all supported fields and completed_at semantics. | completed_at NULL => incomplete; non-NULL => complete. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-02 | Automated | 6,8 | Deadline | Set deadline date+time. | Exact date and time are preserved. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-03 | Automated | 6,8 | Deadline | Set deadline date only. | Date is preserved; time remains absent. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-04 | Automated | 6,8 | Deadline | With FakeClock today=D, set deadline time only. | Deadline date becomes D. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-05 | Automated | 6,8 | Deadline | Create without deadline. | No deadline is present. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-06 | Automated | 6,8 | Deadline/visibility | Create overdue incomplete Todo. | Todo remains in dashboard list; presenter marks subtle overdue state only. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-07 | Automated | 6,8 | Planned time | Set planned date only. | planned_date present; start/end absent. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-08 | Automated | 6,8 | Planned time | Set date + point time. | start present; end absent. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-09 | Automated | 6,8 | Planned time | Set date + start/end range. | Range is preserved. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-10 | Automated | 6,8 | Planned time | With FakeClock today=D, enter planned time without date. | planned_date becomes D. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-11 | Automated | 6,8 | Planned time validation | Attempt range with end <= start. | Validation rejects it. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-12 | Automated | 6,8 | Dashboard visibility | Create incomplete Todos with past/today/future planned dates. | All incomplete Todos are included. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-13 | Automated | 6,8 | Dashboard visibility | Complete Todo today. | It remains included today. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-14 | Automated | 6,8 | Dashboard visibility | Advance FakeClock one day after completion. | Previously completed Todo is excluded from main list. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-15 | Automated | 6,8 | Ordering | Quick-add a Todo when list has existing items. | New Todo receives top manual order. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-16 | Automated | 6,8 | Ordering | Complete an item in middle of list. | Manual position is unchanged. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-17 | Automated | 6,8 | Ordering | Change deadline on an item. | Manual order is unchanged. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-18 | Automated | 6,8 | Ordering | Change planned time on an item. | Manual order is unchanged. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-19 | Automated | 6,8 | Delete | Delete Todo after confirmation path invokes service. | Record is actually deleted; no recycle-bin/soft-delete record is created. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-20 | Automated | 6,8 | Completed history | Query incomplete/completed views. | Incomplete and completed history are separated correctly. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-21 | Automated | 6,8 | Completed history | Restore completed Todo. | completed_at becomes NULL and Todo returns to incomplete view. | tests/unit/services/test_todo_service.py |  |
| AUT-TODO-22 | Automated | 6,8 | Completed history | Permanently delete completed Todo after confirmation. | Record is removed. | tests/unit/services/test_todo_service.py |  |
| AUT-BRIDGE-01 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Inspect/exercise DashboardBridge command surface. | Bridge exposes approved command semantics and delegates to services without SQL/HTTP logic. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-02 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Issue Todo command in Interaction vs Layout Edit/Locked test state. | Allowed only in Interaction as specified; no layout mutation. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-03 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Send addQuickTodo(content). | TodoService quick-add is called and refreshed Todo state is emitted. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-04 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Send toggleTodo(id). | Completion toggles through TodoService and state event is emitted. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-05 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Send reorderTodos(ids). | Validated ordered IDs are persisted in one service operation. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-06 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Request editor/delete. | Native editor/confirmation routing is invoked; JS does not directly persist. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-07 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Request weekly timetable from Agenda title action. | Timetable ViewModel request is served; no row-edit command is exposed. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-BRIDGE-08 | Automated | 7,8,11,12,14,17,22,26 | QWebChannel | Trigger domain/profile/network/mode changes. | Expected event families are emitted with presentation state, not raw rows. | tests/unit/ui/dashboard/test_bridge.py |  |
| AUT-PRES-01 | Automated | 7,10,11,12,17,22 | Presentation | Convert domain/repository/provider models to Dashboard ViewModels. | Output contains DeskBoard-owned display fields only; no raw SQLite/provider-specific fields. | tests/unit/presentation/ |  |
| AUT-PRES-02 | Automated | 7,10,11,12,17,22 | Presentation | Present Todo completed today. | ViewModel exposes completed=true/check styling state without strikethrough business flag. | tests/unit/presentation/ |  |
| AUT-PRES-03 | Automated | 7,10,11,12,17,22 | Presentation | Present course with blank vs populated classroom. | Blank classroom produces no displayed classroom text; populated value is included. | tests/unit/presentation/ |  |
| AUT-PRES-04 | Automated | 7,10,11,12,17,22 | Presentation | Present overdue/in-time incomplete Todos. | Overdue boolean/text is computed in Python presentation/service layer. | tests/unit/presentation/ |  |
| AUT-PRES-05 | Automated | 7,10,11,12,17,22 | Presentation | Present normalized finance value/change. | Stable formatted text and direction are produced consistently for all finance widgets. | tests/unit/presentation/ |  |
| AUT-PRES-06 | Automated | 7,10,11,12,17,22 | Presentation | Present overlapping course/Todo. | ViewModel carries conflict/type/time metadata but no CSS pixel positions. | tests/unit/presentation/ |  |
| AUT-PRES-07 | Automated | 7,10,11,12,17,22 | Presentation | Present normalized weather. | Only approved weather display fields are exposed. | tests/unit/presentation/ |  |
| AUT-COURSE-01 | Automated | 9 | Semester active state | Store multiple semesters with none active. | Zero active semester is valid. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-02 | Automated | 9 | Semester active state | Set one active semester. | Exactly one active semester is returned. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-03 | Automated | 9 | Semester active state | Attempt a second simultaneous active semester through service. | Service prevents two active semesters. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-04 | Automated | 9 | Semester validation | Create semester whose start_monday is not Monday. | Validation rejects it. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-05 | Automated | 9 | Teaching week | For date=start_monday, calculate teaching week. | Week = 1. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-06 | Automated | 9 | Teaching week | Calculate before start or after total_weeks. | No current teaching week is returned. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-07 | Automated | 9 | Periods unconfigured | Fresh DB has no saved complete period set. | Period configuration is treated as unconfigured, not invented. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-08 | Automated | 9 | Periods valid | Save exactly periods 1..8 with valid ranges. | Configuration becomes active/valid. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-09 | Automated | 9 | Periods duplicate | Attempt duplicate period_no. | Rejected. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-10 | Automated | 9 | Periods missing | Attempt 7-row or otherwise partial set. | Rejected/not activated. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-11 | Automated | 9 | Periods out of range | Attempt period 0/9. | Rejected. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-12 | Automated | 9 | Periods time validation | Attempt end <= start. | Rejected. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-13 | Automated | 9 | Recurring course | Create recurring course within valid semester/week/day/time fields. | Record/service model is valid. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-14 | Automated | 9 | Recurring occurrence | Request day inside start_week..end_week on matching weekday. | Occurrence is generated. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-15 | Automated | 9 | Recurring occurrence | Request matching weekday outside course week range. | No occurrence. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-16 | Automated | 9 | Recurring validation | Attempt weekday outside 1..7 or invalid start/end. | Rejected. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-17 | Automated | 9 | No odd/even semantics | Generate every week between start_week/end_week. | Occurrence appears weekly without odd/even filtering. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-18 | Automated | 9 | Cancellation | Cancel one valid recurring occurrence. | That date's occurrence is suppressed. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-19 | Automated | 9 | Cancellation isolation | Inspect adjacent weeks after one cancellation. | Other occurrences remain. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-20 | Automated | 9 | Cancellation uniqueness | Cancel same occurrence twice. | No duplicate logical cancellation is created. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-21 | Automated | 9 | One-off | Create valid one-off course. | It appears only on explicit date. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-22 | Automated | 9 | Reschedule representation | Cancel recurring occurrence + add one-off replacement. | Original absent; one-off present; no reschedule relation needed. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-23 | Automated | 9 | One-off validation | Attempt invalid one-off end <= start. | Rejected. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-24 | Automated | 9 | One-off classroom | One-off with blank classroom. | Occurrence remains valid with no classroom display text. | tests/unit/services/test_course_service.py |  |
| AUT-COURSE-25 | Automated | 9 | Outside teaching range | Request week outside semester range containing matching one-off and recurring candidates. | Recurring absent; matching one-off present. | tests/unit/services/test_course_service.py |  |
| AUT-AGENDA-01 | Automated | 10,11 | Derived-only | Build agenda from TodoService/CourseService outputs. | Agenda is derived without persistence write/event table. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-02 | Automated | 10,11 | Timed merge | Today has course + point Todo + range Todo. | All three appear in timed section. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-03 | Automated | 10,11 | Timed sort | Provide out-of-order timed items. | Output sorted by start time. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-04 | Automated | 10,11 | Date selection | Include items from today and other dates. | Only today's eligible items appear. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-05 | Automated | 10,11 | Past visibility | Set current local time after morning items. | Past timed items remain in agenda and are not marked hidden/grey by time alone. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-06 | Automated | 10,11 | Today deadline inclusion | Todo is due today with no planned date, or with a planned date on another day. | It enters the date-only section; its planned time is not projected onto today. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-07 | Automated | 10,11 | Completed state | Scheduled Todo completed today. | It remains in agenda with completed state. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-08 | Automated | 10,11 | Date-only section | Todo planned_date=today and no time. | It appears after timed section. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-09 | Automated | 10,11 | Date-only ordering | Multiple date-only Todos with manual orders. | They follow Todo manual order. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-10 | Automated | 10,11 | Timed/date-only partition | Mix timed and date-only Todos. | All timed precede date-only regardless of Todo manual order. | tests/unit/services/test_agenda_service.py |  |
| AUT-AGENDA-11 | Automated | 10,11 | Unplanned exclusion | Todo has no planned date/time and no deadline today. | It does not enter agenda. | tests/unit/services/test_agenda_service.py |  |
| AUT-TT-01 | Automated | 10,12 | Teaching label | Current week inside active semester teaching range. | weekLabel = 第 N 周. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-02 | Automated | 10,12 | Teaching label | Current week outside active semester range. | weekLabel is blank while eligible one-offs may remain. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-03 | Automated | 10,12 | Week scope | Build timetable for local current week. | Exactly Monday–Sunday dates for current week are represented. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-04 | Automated | 10,12 | No navigation state | Inspect Timetable ViewModel. | No previous/next week domain state is required/exposed. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-05 | Automated | 10,12 | View-only data | Inspect commands/viewmodel. | No direct course/Todo edit commands are part of timetable overlay contract. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-06 | Automated | 10,12 | Header modes | Format each approved header mode. | weekday, weekday+date, date-only formats are correct. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-07 | Automated | 10,12,31 | Display range | Use a valid active timetable scheme. | Custom range begins at the first configured period and ends at the last; uniform range uses day_start/day_end. | tests/unit/services/test_timetable_service.py | The legacy eight-period case remains a compatibility fixture. |
| AUT-TT-08 | Automated | 10,12 | Deadline exclusion | Deadline-only Todo falls in current week. | It is absent from timetable. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-09 | Automated | 10,12 | Completed Todo | Planned-time Todo completed today/current week. | Completed metadata remains present. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-10 | Automated | 10,12 | Lower bound exclusion | Event ends/occurs before visible start. | It is excluded. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-11 | Automated | 10,12 | Upper bound exclusion | Event starts/occurs after visible end. | It is excluded. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-12 | Automated | 10,12,31 | Unconfigured axis | Build timetable without a valid active scheme. | ViewModel returns configuration-required state and no invented vertical bounds. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-13 | Automated | 10,12 | Course time | Course at arbitrary 08:30–09:20 within range. | Actual clock times are preserved; no period snapping. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-14 | Automated | 10,12 | Point Todo | Planned point-time Todo in current week/range. | ViewModel marks timeKind=point with exact start and no fabricated end. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-15 | Automated | 10,12 | Range Todo | Planned range Todo in current week/range. | ViewModel carries actual start/end range. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-16 | Automated | 10,12 | Date-only Todo | Date-only planned Todo in current week. | It is excluded. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-17 | Automated | 10,12 | Other-week Todo | Timed Todo outside current week. | It is excluded. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-18 | Automated | 10,12 | Bounds filter | Timed Todo in current week but outside visible bounds. | It is excluded. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-19 | Automated | 10,12 | Past events | Current time is after an event. | Event remains present and not domain-marked grey solely by elapsed time. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-20 | Automated | 10,12 | Overlap detection | Course and Todo time ranges overlap. | Conflict metadata is true for Todo/course relation. | tests/unit/services/test_timetable_service.py |  |
| AUT-TT-21 | Automated | 10,12 | No auto-reschedule | Create overlap. | Times remain unchanged; no save rejection/reschedule mutation occurs. | tests/unit/services/test_timetable_service.py |  |
| AUT-STATE-01 | Automated | 11 | Initial state | Request initial Dashboard state once. | One coarse snapshot contains app/profile/widgets/todos/agenda/weather/finance/networkStatus sections without many getter calls. | tests/unit/presentation/test_dashboard_state.py |  |
| AUT-STATE-02 | Automated | 11 | State authority | Apply service-side state change and emit update. | Python-produced state replaces/render-updates JS mirror; no JS-side authoritative mutation contract. | tests/unit/presentation/test_dashboard_state.py |  |
| AUT-PROFILE-01 | Automated | 13,14,23 | Widget instances | Attempt duplicate widget_key in one Profile. | At most one instance per approved widget type. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-02 | Automated | 13,14,23 | Derived sizing | Persist/reload Profile after runtime compact/normal/expanded derivation. | Generic derived size mode is not persisted. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-03 | Automated | 13,14,23 | Save geometry | Save Dashboard x/y/width/height. | Reload matches. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-04 | Automated | 13,14,23 | Save widgets | Save widget x/y/w/h and visible flags. | Reload matches. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-05 | Automated | 13,14,23 | Save visual config | Save theme/opacity/widget display config. | Reload matches. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-06 | Automated | 13,14,23,31 | Global-data isolation | Switch Profiles after storing Todo/cities/finance/timetable schemes/network data. | Global data remains unchanged. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-07 | Automated | 13,14,23 | Built-in Default | Initialize Profile domain. | Default exists and is built-in. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-08 | Automated | 13,14,23 | Layout edit snapshot | Enter edit then mutate layout before save/cancel. | Pre-edit snapshot exists and normal Todo interaction is gated by mode. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-09 | Automated | 13,14,23 | Mode restore | Enter layout edit from Locked and Interaction, then Save/Cancel. | Exit returns to the recorded prior daily mode. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-10 | Automated | 13,14,23 | Default immutable | Attempt delete/overwrite built-in Default through service. | Operation is rejected. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-11 | Automated | 13,14,23 | User limit | Create 8 user Profiles then attempt ninth. | First 8 succeed; ninth rejected with bounded error. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-12 | Automated | 13,14,23 | Management actions | Exercise switch/save current/save-as/rename/delete/restore default. | All approved actions work; no unsupported management action is required. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-13 | Automated | 13,14,23 | Save Default as user | While Default active, confirm Save As path and dismiss path. | Confirm creates/switches user Profile; dismiss leaves Default unchanged and edit session open. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-14 | Automated | 13,14,23 | Delete active | Delete active user Profile. | Active Profile becomes Default. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-15 | Automated | 13,14,23 | Delete inactive | Delete inactive user Profile. | Current active Profile remains unchanged. | tests/unit/services/test_profile_service.py |  |
| AUT-PROFILE-16 | Automated | 13,14,23 | Base theme list | Enumerate the initial supported theme keys. | Initial light theme keys remain valid and persist per Profile. | tests/unit/services/test_profile_service.py | Extended catalog is covered by Task 30. |
| AUT-PROFILE-17 | Automated | 30 | Theme/font persistence | Save a dark/high-contrast theme and installed-font key through ProfileRepository/Service. | Theme and font round-trip through migration and presentation without changing global data ownership. | tests/unit/ui/test_task30_ui_contract.py |  |
| AUT-SET-14 | Automated | 30 | Settings language | Construct SettingsService with no language value, switch to English, reload. | Default is `zh_CN`; `en_US` persists in SQLite and rejects unsupported languages. | tests/unit/ui/test_task30_ui_contract.py |  |
| AUT-UI-01 | Automated | 30 | Native Settings shell | Construct native Settings offscreen and switch language/appearance controls. | Sidebar/header retranslate, About content follows the language, and saved Profile visuals are applied. | tests/integration/test_settings_task30.py | Real Windows visual acceptance remains separate. |
| AUT-TSCHEME-01 | Automated | 31 | Legacy migration | Open a database with a complete legacy `class_periods` set. | A built-in custom scheme is created with identical values and existing semesters are bound to it. | tests/unit/repositories/test_timetable_scheme_repository.py | No fabricated rows are added. |
| AUT-TSCHEME-02 | Automated | 31 | Fresh migration | Open a fresh database or an incomplete legacy period set. | No active school-period axis is invented; timetable remains configure-first. | tests/unit/repositories/test_timetable_scheme_repository.py |  |
| AUT-TSCHEME-03 | Automated | 31 | Custom count | Save custom schemes with period_count at 1, 8, 24, and outside the allowed range. | Boundary values succeed; outside values are rejected. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-04 | Automated | 31 | Custom row shape | Save missing, duplicate, out-of-order, overlapping, and invalid start/end rows. | Invalid custom schemes never become active; valid increasing rows with gaps succeed. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-05 | Automated | 31 | Uniform defaults | Save a uniform scheme without explicit bounds. | It uses 00:00–24:00, stores no child period rows, and returns equal visual-guide metadata. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-06 | Automated | 31 | Uniform custom bounds | Save a uniform scheme with custom day_start/day_end and guide count. | Bounds and guide count round-trip; no artificial school-period labels are created. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-07 | Automated | 31 | Scheme reuse | Bind one scheme to multiple semesters and switch active semester. | Each semester resolves the same scheme without duplicating or mutating period data. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-08 | Automated | 31 | Scheme CRUD | Create, duplicate, rename, and delete schemes through the service contract. | Names/rows persist; duplicate is independent; delete is confirmation-gated. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-09 | Automated | 31 | Bound delete | Delete a scheme referenced by a semester. | The service requires confirmation and leaves the semester unbound/configure-first after confirmation. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-10 | Automated | 31 | Transactional save | Fail validation halfway through a multi-row scheme save. | No partial scheme/semester binding is committed. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-11 | Automated | 31 | Scheme normalization | Load a valid scheme through repository/service presentation. | Returned model contains semantic fields only, not raw SQLite/provider rows. | tests/unit/services/test_timetable_scheme_service.py |  |
| AUT-TSCHEME-12 | Automated | 31 | Semester editor state | Load semester list with bound, unbound, and invalid schemes. | Settings state clearly identifies the active binding and configure-first state. | tests/unit/ui/test_task31_ui_contract.py |  |
| AUT-TSCHEME-13 | Automated | 31 | Legacy write isolation | Modify a migrated scheme after startup. | New writes update scheme tables; legacy `class_periods` is not used as a second source of truth. | tests/unit/repositories/test_timetable_scheme_repository.py |  |
| AUT-TSCHEME-14 | Automated | 31 | Profile isolation | Save/switch Profile after changing the semester's timetable scheme. | Scheme binding and period data remain global and unchanged. | tests/unit/services/test_profile_service.py |  |
| AUT-TTSCHEME-01 | Automated | 31 | Custom axis metadata | Present a semester with a valid custom scheme. | Presenter returns first/last bounds, dynamic period references, and continuous-time metadata. | tests/unit/services/test_timetable_service.py |  |
| AUT-TTSCHEME-02 | Automated | 31 | Uniform axis metadata | Present a semester with a valid uniform scheme. | Presenter returns day bounds and guide count without fabricated period semantics. | tests/unit/services/test_timetable_service.py |  |
| AUT-TTSCHEME-03 | Automated | 31 | Dynamic labels/guides | Use custom counts other than eight and uniform guide counts. | Web-facing metadata renders the supplied count, not a hard-coded 1..8 contract. | tests/unit/services/test_timetable_service.py |  |
| AUT-TTSCHEME-04 | Automated | 31 | Scheme bounds filter | Place course/Todo events before, inside, and after each axis. | Only events inside the active scheme range are returned; actual times are preserved. | tests/unit/services/test_timetable_service.py |  |
| AUT-TTSCHEME-05 | Automated | 31 | Configure-first presentation | Omit the active semester scheme or make it invalid. | Timetable returns the compact configure-first state while Today Agenda remains available. | tests/unit/services/test_timetable_service.py |  |
| AUT-TTSCHEME-06 | Automated | 31 | Bridge contract | Request weekly timetable state. | Bridge exposes normalized axis metadata/commands and no raw scheme table rows. | tests/integration/test_timetable_bridge_task31.py |  |
| AUT-UI-02 | Automated | 31 | Settings palette preview | Select several Profile themes without saving, then cancel/reopen. | Settings shell/page and Dashboard preview synchronously; persisted theme is restored after cancellation/reopen. | tests/integration/test_settings_task31.py | Real Windows colors remain a manual gate. |
| AUT-LAYOUT-02 | Automated | 31 | Responsive edit-bar contract | Inspect Layout Edit shell markup/CSS/native hit-test regions at wide and narrow widths. | Edit mode replaces normal shell content with a primary Save/Cancel row plus a wrapping visibility row without a horizontal scrollbar; controls are excluded from native dragging and blank instruction space remains draggable through the native bridge. | tests/unit/ui/test_task31_ui_contract.py | Geometry feel remains a real Windows gate. |
| AUT-LAYOUT-01 | Automated | 14,23 | Grid topology | Round-trip a 48-column GridStack layout through save/load and outer-window resize state; exercise legacy 12-column migration. | x/y/w/h topology remains unchanged after normalization; only pixel dimensions are a Web runtime concern. | tests/unit/presentation/test_layout_state.py |  |
| AUT-NET-01 | Automated | 15,26 | Schedule | Configure auto refresh clock. | Nominal interval is fixed at 60 minutes. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-02 | Automated | 15,26 | Visibility independence | Hide Dashboard in app state while refresh scheduler remains active. | Refresh scheduling remains enabled until application exit. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-03 | Automated | 15,26 | Startup cache | Cache age <60m and last status success. | Cached payload returned immediately; no refresh scheduled solely for restart; status green. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-04 | Automated | 15,26 | Startup cache | Cache age <60m and last status failure. | Cached payload returned; no restart-only refresh; status red. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-05 | Automated | 15,26 | Startup cache | Cache age >=60m. | Cached payload returned immediately and background refresh scheduled. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-06 | Automated | 15,26 | Startup no cache | No payload/state. | View data represents no-data state and background refresh scheduled. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-07 | Automated | 15,26 | Startup unknown | Fresh/no-refresh scenario with no known state. | Status grey. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-08 | Automated | 15,26 | GUI thread safety | Dispatch provider work via worker abstraction. | HTTP work is not executed on Qt GUI thread. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-09 | Automated | 15,26 | Single active group | Start same provider group twice before first completes. | Second request ignored/disabled; no second worker for same group. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-10 | Automated | 15,26 | No queue | Attempt repeated duplicate group refreshes. | No refresh queue accumulates. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-11 | Automated | 15,26 | Partial success | One group fails while others succeed. | Successful results commit; failed group retains old cache; overall status red. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-12 | Automated | 15,26 | Shared data | Multiple finance widgets request same enabled item state. | Refresh layer schedules one underlying provider/group fetch, not one per widget. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-13 | Automated | 15,26 | Independent items | Batch/group response has one valid and one item parse failure where supported by contract. | Valid item may persist independently while failed item/state is recorded according to provider result model. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-14 | Automated | 15,26 | Cache protection | Refresh fails after prior success. | network_cache payload/success time remain last successful values; network_state updates failure. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-15 | Automated | 15,26 | No short retry | Provider refresh fails. | No automatic 1m/5m/backoff retry is scheduled. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-16 | Automated | 15,26 | Next cycle/manual | After failure, advance to next normal cycle or invoke manual refresh. | Only these mechanisms trigger next attempt. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-17 | Automated | 15,26 | No connectivity gate | Simulate connectivity probe concept absent while provider returns success/failure. | Refresh attempts provider directly; no ping/global connectivity precondition. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-18 | Automated | 15,26 | Error separation | Provider raises timeout/parse/invalid-data error. | Readable state error and detailed log context can be recorded without replacing cache. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-19 | Automated | 15,26 | Manual/auto same service | Invoke automatic and manual group refresh entry points. | Both delegate to same DataRefreshService implementation path. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-20 | Automated | 15,26 | Status grey in progress | Start applicable refresh. | Global status derives grey until applicable refresh completes. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-21 | Automated | 15,26 | Status green | All enabled items/groups last success. | Global status green. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-22 | Automated | 15,26 | Status red | At least one enabled item/group last failure. | Global status red. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-23 | Automated | 15,26 | Disabled exclusion | A disabled financial item has failure state while enabled items succeed. | Disabled item does not make global status red. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-24 | Automated | 15,26 | Profile visibility exclusion | Enabled item widget hidden in active Profile. | Item still participates in refresh/status. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-25 | Automated | 15,26 | Local data exclusion | Todo/course changes/errors. | They do not participate in network status dot. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-26 | Automated | 15,26 | Fresh status restore | Restart with fresh cache and persisted success/failure attempt state. | Prior green/red derivation is restored. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-27 | Automated | 15,26 | No known state | Enabled item has no attempt result yet. | Global status grey. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-28 | Automated | 15,26 | Zero enabled | No network items configured/enabled. | Global status grey, not vacuously green. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-NET-29 | Automated | 15,26 | Derived color | Inspect persistence/state calculation. | No status-dot color field is persisted; color derives from network_state + enabled config + refresh state. | tests/unit/services/test_refresh_status_service.py |  |
| AUT-PROV-01 | Automated | 15–21 | Provider boundary | Run provider/parser against fixture with repository/UI unavailable. | Provider returns normalized result/error only and performs no persistence/UI/status scheduling. | tests/unit/providers/test_provider_contract.py |  |
| AUT-WTH-01 | Automated | 16,17 | Weather parser | Parse representative validated raw fixture. | Normalized result contains city/condition/current_temperature/high/low/wind. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-02 | Automated | 16,17 | Weather field boundary | Inspect normalized/presentation result. | No V1-required dependency on feels-like/precip/AQI/lifestyle fields. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-03 | Automated | 16,17 | City domain | Add/reorder mainland-China cities. | Global order persists. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-04 | Automated | 16,17 | Primary city | Set a different primary city. | Exactly one primary city is selected. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-05 | Automated | 16,17 | City deletion/update | Delete/update primary/non-primary city per service rules. | City config remains valid and deterministic. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-06 | Automated | 16,17 | Profile independence | Switch Profiles. | City list/order/primary city remain global. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-07 | Automated | 16,17 | Primary presentation | Render small/normal Weather ViewModel. | Primary city is prioritized. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-08 | Automated | 16,17 | Expanded preference | Apply Profile single-detail vs multi-summary display config. | Presenter/state exposes the selected profile display preference without changing global city config. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-WTH-09 | Automated | 16,17 | Multi-city ordering | Provide more cities than a constrained capacity. | Candidate list follows global order; Web may show first N without scroll. | tests/unit/providers/weather/ or tests/unit/services/test_weather_service.py |  |
| AUT-FIN-01 | Automated | 18,22 | Catalog whitelist | Build FinanceCatalog from Task 1 accepted entries. | Only validated stable DeskBoard keys are present. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-02 | Automated | 18,22 | Arbitrary codes | Attempt to enable unknown/user-entered security key. | Rejected/not represented in preference service. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-03 | Automated | 18,22 | Catalog metadata | Inspect entries. | Each item has stable DeskBoard key/category/display/source-provider mapping needed by app. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-04 | Automated | 18,22 | Preferences | Enable/disable catalog items. | Enabled set persists globally. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-05 | Automated | 18,22 | Preferences order | Reorder enabled items. | Global display order persists. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-06 | Automated | 18,22 | Profile independence | Switch Profiles. | Finance enable/order remains unchanged. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-07 | Automated | 18,22 | U.S. deferral | Run catalog build when Task 1 has no accepted U.S. source. | No U.S. item ships; us_indices capability is marked unavailable/hidden, not proxied/keyed. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-08 | Automated | 18,22 | Minimal display and FX display basis | Present finance item, including normalized FX values above and below 1 CNY. | ViewModel contains name/value/change where meaningful and optional secondary label; no chart/history payload; FX values `>= 1` display as `1 foreign unit = N CNY`, while values `> 0` and `< 1` display as `1 CNY = N foreign units` using the reciprocal. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-09 | Automated | 18,22 | Capacity order | Give ordered enabled items to small/large widget capacity logic. | Items are consumed in global order and larger capacity reveals more. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-10 | Automated | 18,22 | No pagination contract | Inspect finance widget state. | No pagination/scroll state is required. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-11 | Automated | 18,22 | Direction | Present positive/negative change. | positive direction=up/red semantic with '+'; negative=down/green semantic with '-'. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-12 | Automated | 18,22 | Shared source | Render overview and category widget using same finance state. | Both consume same normalized/cache state; no duplicate fetch is triggered. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-13 | Automated | 18,22 | Closed market | Provider/model reliably marks market closed with latest completed session value. | secondaryText=上一交易日收盘. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-14 | Automated | 18,22 | Unknown market | Market state unknown. | No closed-market label is emitted. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FIN-15 | Automated | 18,22 | No timestamp front | Build finance Dashboard ViewModel. | No last-success timestamp field intended for front rendering. | tests/unit/services/test_finance_service.py or tests/unit/presentation/test_finance_presenter.py |  |
| AUT-FX-01 | Automated | 19 | FX normalization | Parse upstream rate quoted per 100 foreign units. | Normalized value equals upstream/100 as appropriate to 1 foreign unit=CNY convention. | tests/unit/providers/fx/test_parser.py |  |
| AUT-FX-02 | Automated | 19 | FX normalization | Parse upstream rate already per 1 unit. | Normalized value is not divided again. | tests/unit/providers/fx/test_parser.py |  |
| AUT-FX-03 | Automated | 19 | FX validation | Fixture missing/invalid/non-positive reference rate. | Parser returns typed invalid/parse failure, not 0.00 success. | tests/unit/providers/fx/test_parser.py |  |
| AUT-FX-04 | Automated | 19 | FX normalized item coverage | Parse USD/EUR/JPY/HKD normalized values. | Every Provider payload preserves the 1 foreign unit = CNY convention; Finance display-basis inversion is covered by AUT-FIN-08. | tests/unit/providers/test_fx_parser.py |  |
| AUT-SET-01 | Automated | 24,25 | Settings save behavior | Exercise representative immediate setting and structured editor save/cancel controller behavior. | Immediate setting applies through service; structured cancel leaves persisted object unchanged. | tests/unit/ui/settings/test_settings_controllers.py |  |
| AUT-SET-02 | Automated | 25 | Data Status model | Build Data Status row from network config/state/source metadata. | Row includes group/source, attempt, success time, status, readable error, attribution and refresh availability. | tests/unit/presentation/test_data_status_presenter.py |  |
| AUT-TIME-01 | Automated | 5,6,9,10,26 | Local time | Use FakeClock local date/time in Todo deadline/planned defaults. | Services use supplied Windows-local-equivalent clock. | tests/unit/infrastructure/test_clock_and_time_semantics.py |  |
| AUT-TIME-02 | Automated | 5,6,9,10,26 | Teaching week | Use FakeClock local dates around semester boundaries. | Course calculations use same local date source. | tests/unit/infrastructure/test_clock_and_time_semantics.py |  |
| AUT-TIME-03 | Automated | 5,6,9,10,26 | Day views | Change FakeClock date across midnight. | Todo completed-today/Agenda/current week recompute correctly. | tests/unit/infrastructure/test_clock_and_time_semantics.py |  |
| AUT-TIME-04 | Automated | 5,6,9,10,26 | Remote weather independence | Change weather city metadata/timezone-like data if present. | Todo/course clock behavior is unchanged. | tests/unit/infrastructure/test_clock_and_time_semantics.py |  |
| AUT-START-01 | Automated | 26 | Later startup | Persist last user Profile + daily mode and a prior hidden Dashboard state, then start. | Last Profile/daily mode restored; Dashboard is visible. | tests/unit/app/test_startup_runtime.py |  |
| AUT-START-02 | Automated | 26 | Layout-edit recovery | Persist last recorded mode=layout_edit then restart. | Startup mode is Interaction. | tests/unit/app/test_startup_runtime.py |  |
| AUT-START-03 | Automated | 26 | First run | Fresh app_settings DB. | Dashboard visible, mode Interaction, Settings-open-once flag/action produced. | tests/unit/app/test_startup_runtime.py |  |
| AUT-START-04 | Automated | 26 | Subsequent run | After first-run flag set. | Settings does not auto-open solely due startup. | tests/unit/app/test_startup_runtime.py |  |
| AUT-START-05 | Automated | 26 | Day rollover | Schedule/trigger Python-side rollover callback. | Date-dependent Todo/Agenda/Course state refreshes without one-second JS polling. | tests/unit/app/test_startup_runtime.py |  |
| AUT-START-06 | Automated | 26 | Autostart desired state | Toggle autostart setting/controller with mocked Windows integration. | Default OFF; enable/disable invokes current-user integration without admin/service requirement. | tests/unit/app/test_startup_runtime.py |  |
| REV-SCOPE-01 | Review | 0–29 | V1 exclusions | Search dependency/code/UI surfaces for explicitly excluded systems/features. | No unapproved V1 expansion exists. |  |  |
| REV-SCOPE-02 | Review | 5,27 | No DB backup | Inspect scheduled tasks/files/installer behavior. | No automatic DB backup system exists. |  |  |
| REV-SCOPE-03 | Review | 4,24 | No hotkey | Inspect app/tray/settings actions. | No global hotkey registration. |  |  |
| REV-SCOPE-04 | Review | 25 | Course editing boundary | Inspect Dashboard commands/components. | Course editing/cancellation/one-off creation exists only in Settings. |  |  |
| REV-SCOPE-05 | Review | 18,22 | Finance boundary | Inspect catalog/UI. | No arbitrary codes/trading/chart/history/news functionality. |  |  |
| REV-SCOPE-06 | Review | 1,24 | No proxy/key UI | Inspect settings/config/provider contracts. | No proxy/VPN/Clash or user API-key/account configuration flow. |  |  |
| REV-SCOPE-07 | Review | 24,25 | No front refresh | Inspect Dashboard/tray commands. | Manual refresh exists only in Settings Data Status. |  |  |
| REV-SCOPE-08 | Review | 25,29 | No auto-update | Inspect About/runtime. | No auto-update checker/installer logic. |  |  |
| REV-ARCH-01 | Review | 2–25 | Dependency direction | Review imports/calls for UI→Services→Repos/Providers. | No reverse/cross-layer ownership violations. |  |  |
| REV-ARCH-02 | Review | 7,10–12,17,22 | JS authority | Inspect JS modules. | No teaching week, overdue, global status, persistence, provider-domain rules implemented as authoritative JS logic. |  |  |
| REV-ARCH-03 | Review | 7,11,12,14,17,22 | Bridge thinness | Inspect DashboardBridge. | No SQL/HTTP/domain calculations in bridge. |  |  |
| REV-DB-01 | Review | 5 | Repository ownership | Review SQL/table names by repository. | Each repository touches only owned tables. |  |  |
| REV-DB-02 | Review | 5,24–26 | Config ownership | Search QSettings/JSON/YAML/TOML writes. | No second DeskBoard-owned user config store; Windows registry only for OS integration. |  |  |
| REV-DB-03 | Review | 5,10 | No generic agenda/event persistence | Inspect schema/repositories. | No agenda/schedule/today_events generic table is introduced. |  |  |
| REV-PROV-01 | Review | 15–21 | Provider boundary | Inspect provider imports/calls. | No DB/UI/status/retry scheduling ownership. |  |  |
| REV-PROV-02 | Review | 1,16,19–21 | Single-source policy | Inspect runtime provider routing. | No automatic multi-source fallback chain. |  |  |
| REV-PROFILE-01 | Review | 13 | Profile boundary | Inspect persisted Profile fields. | No domain/global network configuration copied into Profile. |  |  |
| REV-TODO-01 | Review | 6–8 | Todo boundary | Inspect model/UI/schema. | No priority/tags/subtasks/recurrence/reminder/attachment/project features. |  |  |
| REV-UI-01 | Review | 23,30 | Visual exclusions | Inspect CSS/assets. | No acrylic/mica, continuous animation, runtime CDN, remote theme/font assets, or extra WebEngine. |  |  |
| REV-PERF-01 | Review | 23,26,28 | Polling/animation | Search timers/network loops/JS intervals. | No one-second JS polling, high-frequency network polling, or continuous decorative animation. |  |  |
| REV-DEP-01 | Review | 2,16,19–21,27 | Dependencies | Review pyproject/build assets. | Only approved/minimal stack; any prohibited major dependency requires spec change. |  |  |
| REV-DONE-01 | Review | 28 | V1 completion | Walk §28 completion definition against repository/test/manual evidence. | No core area remains placeholder-only. |  |  |

## Manual Acceptance Matrix

| ID | Type | Task(s) | Area | Procedure | Expected Result | Evidence to Record | Notes |
|---|---|---|---|---|---|---|---|
| MAN-WIN-01 | Manual | 0,27 | Platform | Run spike/installed app on Windows 10/11 64-bit target environment. | Application launches on supported 64-bit Windows; packaged app does not require dev Python. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-02 | Manual | 0,3 | WebEngine | Inspect running Dashboard and process/window behavior. | Exactly one Dashboard QWebEngineView is used and local page/QWebChannel renders. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-03 | Manual | 0,3,24,25 | Native Settings | Open/focus Settings while Dashboard exists. | Settings is native Qt, coexists correctly, and does not spawn a second WebEngine. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-04 | Manual | 0,4,26 | Z-order | Place ordinary app over DeskBoard, then expose desktop. | Ordinary app covers DeskBoard; DeskBoard remains above desktop. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-05 | Manual | 0,3,4 | Dashboard chrome | Inspect taskbar/window. | Frameless transparent panel, no normal close button, no normal taskbar entry. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-06 | Manual | 3,14,26 | Dashboard geometry | Enter Layout Edit and move/resize panel. | Small rectangular free-position panel moves/resizes; not forced full-screen; visible on startup. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-07 | Manual | 0,4 | Pointer pass-through | In Locked mode click/drag desktop item beneath Dashboard; switch to Interaction. | Locked passes pointer to desktop; Interaction receives intended Dashboard interaction. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-08 | Manual | 26 | First launch | Use clean user data and start app. | Dashboard visible in Interaction and Settings opens once. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-09 | Manual | 4 | Settings close | Close Settings via window close button. | DeskBoard/tray continue running. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-10 | Manual | 4,24 | Exit | Use tray Exit and Settings Exit. | Application exits cleanly. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-11 | Manual | 26 | Window recovery | Persist geometry completely outside current primary work area, then start. | Dashboard is moved back to a visible valid area. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-WIN-12 | Manual | 26 | Primary display only | Run with normal supported primary-display setup; if multiple monitors present, verify V1 does not promise/manage multi-monitor layouts. | Dashboard uses supported primary-display behavior only. | Screenshot / short note / command output as appropriate | Real Windows acceptance |
| MAN-TRAY-01 | Manual | 4 | Tray | Left-click tray icon. | Settings opens/focuses. | Screenshot / short note / command output as appropriate |  |
| MAN-TRAY-02 | Manual | 4 | Tray | Open right-click menu. | Only approved compact actions are present. | Screenshot / short note / command output as appropriate |  |
| MAN-TRAY-03 | Manual | 4 | Tray lifecycle | Hide/show Dashboard, close Settings, exit. | Hide does not exit; close Settings does not exit; Exit does. | Screenshot / short note / command output as appropriate |  |
| MAN-TRAY-04 | Manual | 4 | Single instance | Start DeskBoard twice. | Second process does not create second Dashboard/tray and focuses Settings in first instance. | Screenshot / short note / command output as appropriate |  |
| MAN-TODO-01 | Manual | 7 | Locked Todo | Try scrolling/clicking Todo in Locked mode. | No Todo interaction; pointer passes through. | Screenshot / short note / command output as appropriate |  |
| MAN-TODO-02 | Manual | 7 | Interaction Todo | Use add/check/drag/right-click in Interaction. | All intended actions work while widget/window layout remains fixed. | Screenshot / short note / command output as appropriate |  |
| MAN-TODO-03 | Manual | 7,23 | Todo scroll | Fill Todo beyond visible area. | Content area scrolls; header/+ stay fixed; scrollbar styling is unobtrusive. | Screenshot / short note / command output as appropriate |  |
| MAN-TODO-04 | Manual | 7 | Todo context menu | Right-click incomplete/completed Todo. | Correct Edit/Mark complete-or-incomplete/Delete items shown. | Screenshot / short note / command output as appropriate |  |
| MAN-TODO-05 | Manual | 8 | Native editor/delete | Edit details and trigger Delete. | Native dialog handles fields; delete confirmation prevents accidental deletion. | Screenshot / short note / command output as appropriate |  |
| MAN-LAYOUT-01 | Manual | 14,31 | Layout Edit | Enter from Settings. | Dashboard foreground/editable; GridStack + whole-window move/resize enabled; Todo interaction disabled; Save/Cancel visible in the shell bar. | Screenshot / short note / command output as appropriate | Toolbar placement/no-overlap is detailed in MAN-LAYOUT-04. |
| MAN-LAYOUT-02 | Manual | 14 | Topology | Create asymmetric 12-col layout, save, resize outer Dashboard, restart. | Widget grid topology x/y/w/h remains the same; pixel sizes change; restart restores layout. | Screenshot / short note / command output as appropriate |  |
| MAN-LAYOUT-03 | Manual | 13,14 | Default Save As | Edit built-in Default, press Save; test confirm and dismiss. | Confirm creates/switches user Profile; dismiss leaves edit mode active and Default unmodified. | Screenshot / short note / command output as appropriate |  |
| MAN-LAYOUT-04 | Manual | 31 | Responsive edit controls | Enter Layout Edit at a wide and a narrow Dashboard width; inspect the shell-bar, edit rows, and grid. | Normal title/status/Settings content temporarily yields to the edit bar; Save/Cancel remain visible, visibility controls wrap without a horizontal scrollbar, no control covers grid content, controls do not drag the window, and blank edit-bar space does drag it. | Screenshot / short note / command output as appropriate | Must be checked in normal Windows GUI, not only offscreen/static tests. |
| MAN-AGENDA-01 | Manual | 11,12 | Today Agenda | In Interaction click only the Today Agenda title; inspect rows. | Title opens timetable; rows remain view-only and do not directly edit/complete. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-01 | Manual | 12 | Timetable structure | Open timetable. | Large overlay inside same Dashboard shows current Mon–Sun only and no prev/next controls. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-02 | Manual | 12,25 | Headers | Switch each header setting. | weekday / weekday+date / date-only render correctly. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-03 | Manual | 12,31 | Continuous positioning | Compare events at different arbitrary clock times under a custom and a uniform scheme. | Vertical positions reflect continuous actual time within the active scheme's bounds. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-04 | Manual | 12,25,31 | Unconfigured axis | Use a fresh/unbound semester and open timetable. | Compact configure-first empty state appears; no fake period times; Today Agenda still works. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-05 | Manual | 12 | Course blocks | Show course not aligned to period boundary. | Block appears at actual time, not snapped. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-06 | Manual | 12 | Todo blocks | Show point, range and date-only Todos. | Point is thin exact marker; range is block; date-only absent. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-07 | Manual | 12,23 | Conflict visual | Create course/Todo overlap. | Course visually primary; Todo remains visible narrow/secondary with light indication; times unchanged. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-08 | Manual | 31 | Scheme/semester binding | Create two schemes and two semesters; reuse one scheme, bind the other, switch the active semester. | Each semester uses its selected scheme; switching Profile does not change the scheme or period data. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-09 | Manual | 31 | Custom scheme axis | Create a non-eight-period custom scheme with gaps and arbitrary times. | Saved rows/labels and first-to-last bounds render correctly; invalid overlap/partial rows are rejected; courses remain at actual times. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-10 | Manual | 31 | Uniform day axis | Select the no-school-period option, test default 00:00–24:00 and a custom day range. | Courses/Todos use continuous actual positions; equal guide bands follow the configured count; no artificial school times/labels appear. | Screenshot / short note / command output as appropriate |  |
| MAN-TT-11 | Manual | 31 | Default compatibility | Open a migrated database with the former eight configured periods, then test a fresh/unconfigured database. | Migrated eight-period layout/times are unchanged; fresh state remains configure-first until explicit configuration. | Screenshot / short note / command output as appropriate |  |
| MAN-PROV-01 | Manual | 1,16 | Weather mainland direct | With VPN/Clash/proxy off on ordinary mainland-China connection, run bounded source check for representative mainland cities. | Selected weather source succeeds with required fields and no user key/account. | Screenshot / short note / command output as appropriate | Must be run on user's mainland-China network with proxy/VPN/Clash disabled. |
| MAN-PROV-02 | Manual | 1,19 | Gold mainland direct | Same environment, query selected Au99.99 source. | Succeeds with understood value/unit and no user key/account. | Screenshot / short note / command output as appropriate | Must be run on user's mainland-China network with proxy/VPN/Clash disabled. |
| MAN-PROV-03 | Manual | 1,19 | FX mainland direct | Same environment, query selected CNY FX source. | Succeeds for validated currencies with understood basis and no user key/account. | Screenshot / short note / command output as appropriate | Must be run on user's mainland-China network with proxy/VPN/Clash disabled. |
| MAN-PROV-04 | Manual | 1,20 | A-share mainland direct | Same environment, query selected index source(s). | Validated major A-share items succeed. | Screenshot / short note / command output as appropriate | Must be run on user's mainland-China network with proxy/VPN/Clash disabled. |
| MAN-PROV-05 | Manual | 1,21 | U.S. index gate | Same environment, test candidate U.S. source(s). | Either an accepted no-key mainland-direct source passes or U.S. catalog items are explicitly deferred. | Screenshot / short note / command output as appropriate | Must be run on user's mainland-China network with proxy/VPN/Clash disabled. |
| MAN-PROV-06 | Manual | 1 | Source behavior | Run each selected source repeatedly in bounded checks and capture representative success/error response. | Parser feasibility/error behavior is documented; no runtime fallback/proxy/key workaround is introduced. | Screenshot / short note / command output as appropriate | Must be run on user's mainland-China network with proxy/VPN/Clash disabled. |
| MAN-NET-01 | Manual | 15,17,22,26 | Startup cache experience | Start app with fresh, stale, and absent cache test states. | Dashboard shows cached/no-data immediately and refresh behavior matches age rules without UI freeze. | Screenshot / short note / command output as appropriate |  |
| MAN-NET-02 | Manual | 15 | Refresh responsiveness | Trigger provider-group refresh from Settings while interacting with window. | GUI stays responsive; duplicate same-group refresh is disabled/ignored. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-01 | Manual | 23 | Readability minimums | Resize overall Dashboard/widgets across realistic lower bounds. | Choose/document final minimum Dashboard and per-widget readable sizes; no clipped/unusable core controls. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-02 | Manual | 23 | Adaptive content | Resize Weather/Finance/Todo/Agenda widgets. | Content adapts by pixel size without changing persisted grid topology. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-03 | Manual | 23,30 | Themes and fonts | Switch all twelve themes and several Profile/font combinations. | Original light/dark/high-contrast themes and four token-only genre-inspired themes are distinct/readable; selected theme and font persist per Profile. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-04 | Manual | 23 | Visual direction | Inspect final Dashboard. | Minimal flat semi-transparent regions, subtle separators/outer rounding, almost no shadow, no blur/continuous animation. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-05 | Manual | 22,23 | Finance colors | Display positive and negative finance samples. | Up is red with +; down is green with -; legible in all themes. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-06 | Manual | 7,23 | Todo scroll visual | Overflow Todo content and interact. | Scroll behavior/readability fits panel style. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-07 | Manual | 7,11,12,23 | Completed Todo style | Complete scheduled Todo. | Pale/light green + check, no strikethrough, consistent in Todo/Agenda/timetable. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-08 | Manual | 11,23 | Agenda past items | Open later in day. | Earlier items remain normally visible, not auto-grey/hidden. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-09 | Manual | 12,23 | Timetable past items | Inspect elapsed week events. | Events remain normally rendered, not auto-grey/hidden. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-10 | Manual | 17,23 | Weather modes | Test primary/single-detail/multi-summary at relevant sizes. | Primary prioritized; configured expanded mode behaves as intended. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-11 | Manual | 17,23 | Weather capacity | Use more cities than fit. | First cities in global order shown; no internal weather scroll required. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-12 | Manual | 22,23 | Finance capacity | Enable more items than small widget fits; resize larger. | Small shows first N globally ordered items; larger reveals more; no pagination/scroll. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-13 | Manual | 22,23 | Closed label/timestamp | Show closed/unknown finance states. | Closed reliable state shows 上一交易日收盘; unknown omits label; no last-update timestamp on front. | Screenshot / short note / command output as appropriate |  |
| MAN-UI-14 | Manual | 15,23 | Global dot | Exercise grey/green/red states. | Exactly one small global dot in Dashboard upper-right; no per-widget status dots. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-01 | Manual | 3,24,25 | Settings structure | Open Settings. | Native pages exist for General, Profiles, Weather, Finance, Todo, Courses, Data Status, About. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-02 | Manual | 24 | Profile list | Inspect Default + user Profiles. | Default is protected; max 8 user Profiles represented. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-03 | Manual | 24 | Profile operations | Exercise switch/save/save-as/rename/delete/restore Default. | Approved actions work and active deletion falls back to Default. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-04 | Manual | 8,25 | Todo lists | Inspect Incomplete and Completed history; restore/delete. | Two simple views and approved history actions work; confirmations appear. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-05 | Manual | 25,31 | Timetable schemes | In Courses Settings create/duplicate/rename schemes, bind one per semester, try partial/duplicate/overlap/out-of-range edits, and save a valid custom or uniform scheme. | Invalid set is not active; valid scheme/binding saves; delete of a bound scheme is confirmed; no school times are invented. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-06 | Manual | 25 | Course management | Create/edit semester, recurring, cancellation and one-off. | All structured edits use Settings and Save/Cancel. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-07 | Manual | 25 | Refresh controls | Use Refresh All and each available group. | Only Settings exposes manual refresh; actions use same service semantics. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-08 | Manual | 24 | Weather settings | Add/reorder cities and select primary. | Global city config applies immediately/as designed. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-09 | Manual | 24 | Finance settings | Enable/disable/reorder validated catalog items. | Global finance preferences update and persist. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-10 | Manual | 24,25 | Save behavior | Change immediate setting; cancel structured editor. | Immediate setting applies; cancelled object edit does not persist partial data. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-11 | Manual | 24 | General actions | Show/hide Dashboard, change daily mode, enter Layout Edit, toggle autostart, exit. | Each action matches spec; no extra tray-only dependence. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-12 | Manual | 25 | Data Status/logs | Inspect provider diagnostics and click Open Log Folder. | Detailed fields, source attribution, refresh actions and logs folder open correctly. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-13 | Manual | 25 | About | Inspect About. | Name/version/basic source/disclaimer references shown; no auto-update UI. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-14 | Manual | 30 | Settings language and appearance | Open Settings with no language value, switch Chinese/English, select a theme and font, restart/open again. | Chinese is the default; English updates native static UI; selected visual preferences persist per Profile. | Screenshot / short note / command output as appropriate |  |
| MAN-SET-15 | Manual | 31 | Synchronized theme preview | In Profiles select several themes without saving, observe Dashboard and Settings shell/page, then cancel/close and reopen. | Settings colors change in the same interaction as Dashboard; initial fallback is light rather than black; unsaved preview does not overwrite the stored Profile. | Screenshot / short note / command output as appropriate | Must be checked with Windows night mode both on and off. |
| MAN-PERF-01 | Manual | 0,28 | Idle CPU | Measure minimal spike/final app while Locked and idle. | CPU is close to zero except normal sampling noise. | Screenshot / short note / command output as appropriate |  |
| MAN-PERF-02 | Manual | 0,28 | Memory baseline | Measure minimal WebEngine spike and final app. | ~200MB is preferred but not a hard fail; measurement recorded. | Screenshot / short note / command output as appropriate |  |
| MAN-PERF-03 | Manual | 28 | Memory trend | Run normal personal-use long session per checklist. | Memory does not continuously climb without bound. | Screenshot / short note / command output as appropriate |  |
| MAN-PERF-04 | Manual | 15,28 | Refresh spike | Observe scheduled/manual refresh. | Short CPU/network spikes acceptable; UI remains responsive. | Screenshot / short note / command output as appropriate |  |
| MAN-PERF-05 | Manual | 26,28 | Hidden Dashboard | Hide for extended bounded/manual interval then show. | Refresh continues; WebEngine is not destroyed/recreated; no abnormal CPU loop. | Screenshot / short note / command output as appropriate |  |
| MAN-PERF-06 | Manual | 23,28 | Animations/polling | Observe idle UI and inspect dev/runtime behavior. | No continuous decorative animation or high-frequency JS polling. | Screenshot / short note / command output as appropriate |  |
| MAN-PERF-07 | Manual | 28 | Process behavior | Inspect Chromium/Qt processes during long run and after show/hide. | No runaway process multiplication or obvious resource leak. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-01 | Manual | 0,27 | PyInstaller/installer | Build onedir and production installer, install on clean Windows user environment. | Installed DeskBoard launches with bundled Python/QtWebEngine resources. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-02 | Manual | 27 | Data location | Run installed app and inspect files. | User DB/logs are under LOCALAPPDATA, not Program Files. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-03 | Manual | 27 | Local frontend assets | Disconnect internet then launch Dashboard shell/UI. | Local HTML/CSS/JS/GridStack assets still render (network data may remain cached/unavailable). | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-04 | Manual | 27 | QWebChannel packaged | Use interactive Dashboard feature in installed build. | QWebChannel commands/events work after packaging. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-05 | Manual | 27 | Uninstall base | Uninstall app. | Program files removed cleanly. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-06 | Manual | 27 | Personal data preservation | Uninstall using default/declared behavior. | Personal data is not silently destroyed; any deletion requires explicit user choice. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-07 | Manual | 26,27 | Autostart default | Fresh install/start. | Autostart default is OFF. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-08 | Manual | 26,27 | Autostart toggle | Enable current-user autostart, sign out/restart test as practical, then disable. | DeskBoard starts only when enabled; no admin/service dependency. | Screenshot / short note / command output as appropriate |  |
| MAN-PACK-09 | Manual | 27 | Normal privileges | Install/run normal app path per installer design. | Normal application operation does not require UAC/admin elevation. | Screenshot / short note / command output as appropriate |  |
| MAN-STAB-01 | Manual | 28 | Personal-use soak | Use final installed build normally for agreed real-use interval. | No blocker/crash/major corruption; evidence recorded by user, not agent polling. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-02 | Manual | 28 | Hidden refresh | Hide Dashboard across at least one 60-minute refresh boundary. | Data refresh scheduling continues while hidden. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-03 | Manual | 28 | Network loss/recovery | Disconnect network across refresh, then restore and manually/next-cycle refresh. | Old cache remains, red status shows failure, later success recovers without corruption. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-04 | Manual | 28 | Midnight rollover | Leave/run across local midnight. | Completed-today list/Agenda/date-dependent state rolls to new day correctly. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-05 | Manual | 28 | Week rollover | Exercise Sunday→Monday/current teaching week change. | Agenda/timetable teaching-week state updates correctly. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-06 | Manual | 28 | Sleep/wake | Sleep Windows then resume. | App remains usable; refresh/day state recovers without duplicate workers/processes. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-07 | Manual | 28 | Repeated mode/show/profile use | Cycle show/hide, Locked/Interaction, Profile switches, Layout Edit save/cancel. | No state corruption or sustained resource growth. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-STAB-08 | Manual | 28 | Diagnostics | Induce representative provider failure and inspect Settings/logs. | Failure is diagnosable with cached UI retained and useful log/status evidence. | Screenshot / short note / command output as appropriate | Long-running checks return AWAITING_MANUAL_ACCEPTANCE until user evidence exists. |
| MAN-REL-01 | Manual/Review | 29 | Stability prerequisite | Review Task 28 evidence before release work. | Public release does not proceed before accepted personal-use stability. | Checklist result + source/document reference |  |
| MAN-REL-02 | Manual/Review | 29 | Mainland recheck | Re-run all shipped source checks from mainland direct network. | All shipped providers still pass no-VPN/proxy/Clash/key/account gate. | Checklist result + source/document reference |  |
| MAN-REL-03 | Manual/Review | 29 | Terms/attribution | Review each shipped source's current terms/attribution notes. | README/source documentation reflects required attribution and limitations. | Checklist result + source/document reference |  |
| MAN-REL-04 | Manual/Review | 29 | Provider release suitability | Evaluate any redistribution/commercial restrictions. | Unacceptable source/item is replaced or removed/deferred before release. | Checklist result + source/document reference |  |
| MAN-REL-05 | Manual/Review | 29 | Secrets | Search release tree/build config for secrets/API keys. | No secrets or required end-user keys embedded. | Checklist result + source/document reference |  |
| MAN-REL-06 | Manual/Review | 29 | Claims | Review README/About wording. | No trading-grade, real-time, investment-grade, or guaranteed-data claims. | Checklist result + source/document reference |  |

## Task → Verification Index

### Task 0

`MAN-PACK-01`, `MAN-PERF-01`, `MAN-PERF-02`, `MAN-WIN-01`, `MAN-WIN-02`, `MAN-WIN-03`, `MAN-WIN-04`, `MAN-WIN-05`, `MAN-WIN-07`, `REV-SCOPE-01`

### Task 1

`MAN-PROV-01`, `MAN-PROV-02`, `MAN-PROV-03`, `MAN-PROV-04`, `MAN-PROV-05`, `MAN-PROV-06`, `REV-PROV-02`, `REV-SCOPE-01`, `REV-SCOPE-06`

### Task 2

`AUT-APP-01`, `AUT-INFRA-01`, `AUT-INFRA-02`, `AUT-INFRA-03`, `AUT-INFRA-04`, `REV-ARCH-01`, `REV-DEP-01`, `REV-SCOPE-01`

### Task 3

`MAN-SET-01`, `MAN-WIN-02`, `MAN-WIN-03`, `MAN-WIN-05`, `MAN-WIN-06`, `REV-ARCH-01`, `REV-SCOPE-01`

### Task 4

`AUT-SINGLE-01`, `AUT-TRAY-01`, `MAN-TRAY-01`, `MAN-TRAY-02`, `MAN-TRAY-03`, `MAN-TRAY-04`, `MAN-WIN-04`, `MAN-WIN-05`, `MAN-WIN-07`, `MAN-WIN-09`, `MAN-WIN-10`, `REV-ARCH-01`, `REV-SCOPE-01`, `REV-SCOPE-03`

### Task 5

`AUT-DB-01`, `AUT-DB-02`, `AUT-DB-03`, `AUT-DB-04`, `AUT-DB-05`, `AUT-DB-06`, `AUT-DB-07`, `AUT-DB-08`, `AUT-DB-09`, `AUT-DB-10`, `AUT-DB-11`, `AUT-DB-12`, `AUT-DB-13`, `AUT-DB-14`, `AUT-DB-15`, `AUT-DB-16`, `AUT-TIME-01`, `AUT-TIME-02`, `AUT-TIME-03`, `AUT-TIME-04`, `REV-ARCH-01`, `REV-DB-01`, `REV-DB-02`, `REV-DB-03`, `REV-SCOPE-01`, `REV-SCOPE-02`

### Task 6

`AUT-TIME-01`, `AUT-TIME-02`, `AUT-TIME-03`, `AUT-TIME-04`, `AUT-TODO-01`, `AUT-TODO-02`, `AUT-TODO-03`, `AUT-TODO-04`, `AUT-TODO-05`, `AUT-TODO-06`, `AUT-TODO-07`, `AUT-TODO-08`, `AUT-TODO-09`, `AUT-TODO-10`, `AUT-TODO-11`, `AUT-TODO-12`, `AUT-TODO-13`, `AUT-TODO-14`, `AUT-TODO-15`, `AUT-TODO-16`, `AUT-TODO-17`, `AUT-TODO-18`, `AUT-TODO-19`, `AUT-TODO-20`, `AUT-TODO-21`, `AUT-TODO-22`, `REV-ARCH-01`, `REV-SCOPE-01`, `REV-TODO-01`

### Task 7

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-PRES-01`, `AUT-PRES-02`, `AUT-PRES-03`, `AUT-PRES-04`, `AUT-PRES-05`, `AUT-PRES-06`, `AUT-PRES-07`, `MAN-TODO-01`, `MAN-TODO-02`, `MAN-TODO-03`, `MAN-TODO-04`, `MAN-UI-06`, `MAN-UI-07`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-ARCH-03`, `REV-SCOPE-01`, `REV-TODO-01`

### Task 8

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-TODO-01`, `AUT-TODO-02`, `AUT-TODO-03`, `AUT-TODO-04`, `AUT-TODO-05`, `AUT-TODO-06`, `AUT-TODO-07`, `AUT-TODO-08`, `AUT-TODO-09`, `AUT-TODO-10`, `AUT-TODO-11`, `AUT-TODO-12`, `AUT-TODO-13`, `AUT-TODO-14`, `AUT-TODO-15`, `AUT-TODO-16`, `AUT-TODO-17`, `AUT-TODO-18`, `AUT-TODO-19`, `AUT-TODO-20`, `AUT-TODO-21`, `AUT-TODO-22`, `MAN-SET-04`, `MAN-TODO-05`, `REV-ARCH-01`, `REV-SCOPE-01`, `REV-TODO-01`

### Task 9

`AUT-COURSE-01`, `AUT-COURSE-02`, `AUT-COURSE-03`, `AUT-COURSE-04`, `AUT-COURSE-05`, `AUT-COURSE-06`, `AUT-COURSE-07`, `AUT-COURSE-08`, `AUT-COURSE-09`, `AUT-COURSE-10`, `AUT-COURSE-11`, `AUT-COURSE-12`, `AUT-COURSE-13`, `AUT-COURSE-14`, `AUT-COURSE-15`, `AUT-COURSE-16`, `AUT-COURSE-17`, `AUT-COURSE-18`, `AUT-COURSE-19`, `AUT-COURSE-20`, `AUT-COURSE-21`, `AUT-COURSE-22`, `AUT-COURSE-23`, `AUT-COURSE-24`, `AUT-COURSE-25`, `AUT-TIME-01`, `AUT-TIME-02`, `AUT-TIME-03`, `AUT-TIME-04`, `REV-ARCH-01`, `REV-SCOPE-01`

### Task 10

`AUT-AGENDA-01`, `AUT-AGENDA-02`, `AUT-AGENDA-03`, `AUT-AGENDA-04`, `AUT-AGENDA-05`, `AUT-AGENDA-06`, `AUT-AGENDA-07`, `AUT-AGENDA-08`, `AUT-AGENDA-09`, `AUT-AGENDA-10`, `AUT-AGENDA-11`, `AUT-PRES-01`, `AUT-PRES-02`, `AUT-PRES-03`, `AUT-PRES-04`, `AUT-PRES-05`, `AUT-PRES-06`, `AUT-PRES-07`, `AUT-TIME-01`, `AUT-TIME-02`, `AUT-TIME-03`, `AUT-TIME-04`, `AUT-TT-01`, `AUT-TT-02`, `AUT-TT-03`, `AUT-TT-04`, `AUT-TT-05`, `AUT-TT-06`, `AUT-TT-07`, `AUT-TT-08`, `AUT-TT-09`, `AUT-TT-10`, `AUT-TT-11`, `AUT-TT-12`, `AUT-TT-13`, `AUT-TT-14`, `AUT-TT-15`, `AUT-TT-16`, `AUT-TT-17`, `AUT-TT-18`, `AUT-TT-19`, `AUT-TT-20`, `AUT-TT-21`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-DB-03`, `REV-SCOPE-01`

### Task 11

`AUT-AGENDA-01`, `AUT-AGENDA-02`, `AUT-AGENDA-03`, `AUT-AGENDA-04`, `AUT-AGENDA-05`, `AUT-AGENDA-06`, `AUT-AGENDA-07`, `AUT-AGENDA-08`, `AUT-AGENDA-09`, `AUT-AGENDA-10`, `AUT-AGENDA-11`, `AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-PRES-01`, `AUT-PRES-02`, `AUT-PRES-03`, `AUT-PRES-04`, `AUT-PRES-05`, `AUT-PRES-06`, `AUT-PRES-07`, `AUT-STATE-01`, `AUT-STATE-02`, `MAN-AGENDA-01`, `MAN-UI-07`, `MAN-UI-08`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-ARCH-03`, `REV-SCOPE-01`

### Task 12

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-PRES-01`, `AUT-PRES-02`, `AUT-PRES-03`, `AUT-PRES-04`, `AUT-PRES-05`, `AUT-PRES-06`, `AUT-PRES-07`, `AUT-TT-01`, `AUT-TT-02`, `AUT-TT-03`, `AUT-TT-04`, `AUT-TT-05`, `AUT-TT-06`, `AUT-TT-07`, `AUT-TT-08`, `AUT-TT-09`, `AUT-TT-10`, `AUT-TT-11`, `AUT-TT-12`, `AUT-TT-13`, `AUT-TT-14`, `AUT-TT-15`, `AUT-TT-16`, `AUT-TT-17`, `AUT-TT-18`, `AUT-TT-19`, `AUT-TT-20`, `AUT-TT-21`, `MAN-AGENDA-01`, `MAN-TT-01`, `MAN-TT-02`, `MAN-TT-03`, `MAN-TT-04`, `MAN-TT-05`, `MAN-TT-06`, `MAN-TT-07`, `MAN-UI-07`, `MAN-UI-09`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-ARCH-03`, `REV-SCOPE-01`

### Task 13

`AUT-PROFILE-01`, `AUT-PROFILE-02`, `AUT-PROFILE-03`, `AUT-PROFILE-04`, `AUT-PROFILE-05`, `AUT-PROFILE-06`, `AUT-PROFILE-07`, `AUT-PROFILE-08`, `AUT-PROFILE-09`, `AUT-PROFILE-10`, `AUT-PROFILE-11`, `AUT-PROFILE-12`, `AUT-PROFILE-13`, `AUT-PROFILE-14`, `AUT-PROFILE-15`, `AUT-PROFILE-16`, `MAN-LAYOUT-03`, `REV-ARCH-01`, `REV-PROFILE-01`, `REV-SCOPE-01`

### Task 14

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-LAYOUT-01`, `AUT-PROFILE-01`, `AUT-PROFILE-02`, `AUT-PROFILE-03`, `AUT-PROFILE-04`, `AUT-PROFILE-05`, `AUT-PROFILE-06`, `AUT-PROFILE-07`, `AUT-PROFILE-08`, `AUT-PROFILE-09`, `AUT-PROFILE-10`, `AUT-PROFILE-11`, `AUT-PROFILE-12`, `AUT-PROFILE-13`, `AUT-PROFILE-14`, `AUT-PROFILE-15`, `AUT-PROFILE-16`, `MAN-LAYOUT-01`, `MAN-LAYOUT-02`, `MAN-LAYOUT-03`, `MAN-WIN-06`, `REV-ARCH-01`, `REV-ARCH-03`, `REV-SCOPE-01`

### Task 15

`AUT-NET-01`, `AUT-NET-02`, `AUT-NET-03`, `AUT-NET-04`, `AUT-NET-05`, `AUT-NET-06`, `AUT-NET-07`, `AUT-NET-08`, `AUT-NET-09`, `AUT-NET-10`, `AUT-NET-11`, `AUT-NET-12`, `AUT-NET-13`, `AUT-NET-14`, `AUT-NET-15`, `AUT-NET-16`, `AUT-NET-17`, `AUT-NET-18`, `AUT-NET-19`, `AUT-NET-20`, `AUT-NET-21`, `AUT-NET-22`, `AUT-NET-23`, `AUT-NET-24`, `AUT-NET-25`, `AUT-NET-26`, `AUT-NET-27`, `AUT-NET-28`, `AUT-NET-29`, `AUT-PROV-01`, `MAN-NET-01`, `MAN-NET-02`, `MAN-PERF-04`, `MAN-UI-14`, `REV-ARCH-01`, `REV-PROV-01`, `REV-SCOPE-01`

### Task 16

`AUT-PROV-01`, `AUT-WTH-01`, `AUT-WTH-02`, `AUT-WTH-03`, `AUT-WTH-04`, `AUT-WTH-05`, `AUT-WTH-06`, `AUT-WTH-07`, `AUT-WTH-08`, `AUT-WTH-09`, `MAN-PROV-01`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

### Task 17

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-PRES-01`, `AUT-PRES-02`, `AUT-PRES-03`, `AUT-PRES-04`, `AUT-PRES-05`, `AUT-PRES-06`, `AUT-PRES-07`, `AUT-PROV-01`, `AUT-WTH-01`, `AUT-WTH-02`, `AUT-WTH-03`, `AUT-WTH-04`, `AUT-WTH-05`, `AUT-WTH-06`, `AUT-WTH-07`, `AUT-WTH-08`, `AUT-WTH-09`, `MAN-NET-01`, `MAN-UI-10`, `MAN-UI-11`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-ARCH-03`, `REV-PROV-01`, `REV-SCOPE-01`

### Task 18

`AUT-FIN-01`, `AUT-FIN-02`, `AUT-FIN-03`, `AUT-FIN-04`, `AUT-FIN-05`, `AUT-FIN-06`, `AUT-FIN-07`, `AUT-FIN-08`, `AUT-FIN-09`, `AUT-FIN-10`, `AUT-FIN-11`, `AUT-FIN-12`, `AUT-FIN-13`, `AUT-FIN-14`, `AUT-FIN-15`, `AUT-PROV-01`, `REV-ARCH-01`, `REV-PROV-01`, `REV-SCOPE-01`, `REV-SCOPE-05`

### Task 19

`AUT-FX-01`, `AUT-FX-02`, `AUT-FX-03`, `AUT-FX-04`, `AUT-PROV-01`, `MAN-PROV-02`, `MAN-PROV-03`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

### Task 20

`AUT-PROV-01`, `MAN-PROV-04`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

### Task 21

`AUT-PROV-01`, `MAN-PROV-05`, `REV-ARCH-01`, `REV-DEP-01`, `REV-PROV-01`, `REV-PROV-02`, `REV-SCOPE-01`

### Task 22

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-FIN-01`, `AUT-FIN-02`, `AUT-FIN-03`, `AUT-FIN-04`, `AUT-FIN-05`, `AUT-FIN-06`, `AUT-FIN-07`, `AUT-FIN-08`, `AUT-FIN-09`, `AUT-FIN-10`, `AUT-FIN-11`, `AUT-FIN-12`, `AUT-FIN-13`, `AUT-FIN-14`, `AUT-FIN-15`, `AUT-PRES-01`, `AUT-PRES-02`, `AUT-PRES-03`, `AUT-PRES-04`, `AUT-PRES-05`, `AUT-PRES-06`, `AUT-PRES-07`, `MAN-NET-01`, `MAN-UI-05`, `MAN-UI-12`, `MAN-UI-13`, `REV-ARCH-01`, `REV-ARCH-02`, `REV-ARCH-03`, `REV-SCOPE-01`, `REV-SCOPE-05`

### Task 23

`AUT-PROFILE-01`, `AUT-PROFILE-02`, `AUT-PROFILE-03`, `AUT-PROFILE-04`, `AUT-PROFILE-05`, `AUT-PROFILE-06`, `AUT-PROFILE-07`, `AUT-PROFILE-08`, `AUT-PROFILE-09`, `AUT-PROFILE-10`, `AUT-PROFILE-11`, `AUT-PROFILE-12`, `AUT-PROFILE-13`, `AUT-PROFILE-14`, `AUT-PROFILE-15`, `AUT-PROFILE-16`, `MAN-PERF-06`, `MAN-TODO-03`, `MAN-TT-07`, `MAN-UI-01`, `MAN-UI-02`, `MAN-UI-03`, `MAN-UI-04`, `MAN-UI-05`, `MAN-UI-06`, `MAN-UI-07`, `MAN-UI-08`, `MAN-UI-09`, `MAN-UI-10`, `MAN-UI-11`, `MAN-UI-12`, `MAN-UI-13`, `MAN-UI-14`, `REV-ARCH-01`, `REV-PERF-01`, `REV-SCOPE-01`, `REV-UI-01`

### Task 24

`AUT-SET-01`, `MAN-SET-01`, `MAN-SET-02`, `MAN-SET-03`, `MAN-SET-08`, `MAN-SET-09`, `MAN-SET-10`, `MAN-SET-11`, `MAN-WIN-03`, `MAN-WIN-10`, `REV-ARCH-01`, `REV-DB-02`, `REV-SCOPE-01`, `REV-SCOPE-03`, `REV-SCOPE-06`, `REV-SCOPE-07`

### Task 25

`AUT-SET-01`, `AUT-SET-02`, `MAN-SET-01`, `MAN-SET-04`, `MAN-SET-05`, `MAN-SET-06`, `MAN-SET-07`, `MAN-SET-10`, `MAN-SET-12`, `MAN-SET-13`, `MAN-TT-02`, `MAN-TT-04`, `MAN-WIN-03`, `REV-ARCH-01`, `REV-DB-02`, `REV-SCOPE-01`, `REV-SCOPE-04`, `REV-SCOPE-07`, `REV-SCOPE-08`

### Task 26

`AUT-BRIDGE-01`, `AUT-BRIDGE-02`, `AUT-BRIDGE-03`, `AUT-BRIDGE-04`, `AUT-BRIDGE-05`, `AUT-BRIDGE-06`, `AUT-BRIDGE-07`, `AUT-BRIDGE-08`, `AUT-NET-01`, `AUT-NET-02`, `AUT-NET-03`, `AUT-NET-04`, `AUT-NET-05`, `AUT-NET-06`, `AUT-NET-07`, `AUT-NET-08`, `AUT-NET-09`, `AUT-NET-10`, `AUT-NET-11`, `AUT-NET-12`, `AUT-NET-13`, `AUT-NET-14`, `AUT-NET-15`, `AUT-NET-16`, `AUT-NET-17`, `AUT-NET-18`, `AUT-NET-19`, `AUT-NET-20`, `AUT-NET-21`, `AUT-NET-22`, `AUT-NET-23`, `AUT-NET-24`, `AUT-NET-25`, `AUT-NET-26`, `AUT-NET-27`, `AUT-NET-28`, `AUT-NET-29`, `AUT-START-01`, `AUT-START-02`, `AUT-START-03`, `AUT-START-04`, `AUT-START-05`, `AUT-START-06`, `AUT-TIME-01`, `AUT-TIME-02`, `AUT-TIME-03`, `AUT-TIME-04`, `MAN-NET-01`, `MAN-PACK-07`, `MAN-PACK-08`, `MAN-PERF-05`, `MAN-WIN-04`, `MAN-WIN-06`, `MAN-WIN-08`, `MAN-WIN-11`, `MAN-WIN-12`, `REV-DB-02`, `REV-PERF-01`, `REV-SCOPE-01`

### Task 27

`MAN-PACK-01`, `MAN-PACK-02`, `MAN-PACK-03`, `MAN-PACK-04`, `MAN-PACK-05`, `MAN-PACK-06`, `MAN-PACK-07`, `MAN-PACK-08`, `MAN-PACK-09`, `MAN-WIN-01`, `REV-DEP-01`, `REV-SCOPE-01`, `REV-SCOPE-02`

### Task 28

`MAN-PERF-01`, `MAN-PERF-02`, `MAN-PERF-03`, `MAN-PERF-04`, `MAN-PERF-05`, `MAN-PERF-06`, `MAN-PERF-07`, `MAN-STAB-01`, `MAN-STAB-02`, `MAN-STAB-03`, `MAN-STAB-04`, `MAN-STAB-05`, `MAN-STAB-06`, `MAN-STAB-07`, `MAN-STAB-08`, `REV-DONE-01`, `REV-PERF-01`, `REV-SCOPE-01`

### Task 29

`MAN-REL-01`, `MAN-REL-02`, `MAN-REL-03`, `MAN-REL-04`, `MAN-REL-05`, `MAN-REL-06`, `REV-SCOPE-01`, `REV-SCOPE-08`

### Task 30

`AUT-PROFILE-17`, `AUT-SET-14`, `AUT-UI-01`, `MAN-UI-03`, `MAN-SET-01`, `MAN-SET-14`, `REV-ARCH-01`, `REV-DB-02`, `REV-SCOPE-01`

### Task 31

`AUT-TSCHEME-01..14`, `AUT-TTSCHEME-01..06`, `AUT-UI-02`, `AUT-LAYOUT-02`,
`MAN-TT-08..11`, `MAN-SET-05`, `MAN-SET-15`, `MAN-LAYOUT-04`, `REV-ARCH-01`,
`REV-DB-02`, `REV-SCOPE-01`

## Evidence Retention

For manual gates, retain only bounded evidence needed to close the task:

- exact Windows/build version when relevant;
- PASS/FAIL result;
- one concise screenshot or command-output excerpt when useful;
- provider source URL/name and mainland-direct result for source gates;
- CPU/RAM observation for performance gates;
- date/duration for stability checks.

Do not paste multi-megabyte logs into agent context. Store large raw logs locally and provide only the relevant bounded excerpt.

## Maintenance Rule

When a requirement changes:

1. update the authoritative `docs/spec.md`;
2. update the owning task in `docs/implementation-plan.md`;
3. update the corresponding `REQ-*` row in `requirements-traceability.md`;
4. update/add the concrete `AUT-*`, `MAN-*`, or `REV-*` case here.

A test case must not silently redefine product behavior.
