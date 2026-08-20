# DeskBoard Requirements Traceability Matrix

**Status:** Supporting execution reference for V1  
**Authority:** This file is **not** a product source of truth. `docs/spec.md` remains authoritative for product semantics; `docs/implementation-plan.md` remains authoritative for task order/scope; `AGENTS.md` remains authoritative for agent execution behavior.

## How Codex should use this file

- Do **not** read this whole file for every task.
- For the current numbered task, search this file by task number or requirement ID and read only matching rows.
- A traceability row never overrides the source section named in the `Source` column.
- `Verification ID(s)` point into `docs/quality/test-matrix.md`.
- Rows marked `Static/code review` represent deliberate scope/architecture absence checks rather than runtime tests.

## Coverage Legend

- **Automated** — deterministic unit/integration/fixture test.
- **Manual** — real Windows, real network, visual, packaging, or long-run acceptance.
- **Review** — bounded code/spec/dependency review.
- **Mixed** — more than one of the above.

## Requirement Matrix

| ID | Requirement | Source | Primary Task(s) | Verification ID(s) | Acceptance | Notes |
|---|---|---|---|---|---|---|
| REQ-PROD-01 | Windows 10/11 64-bit only; Python 3.12.x development baseline. | Spec §1–2, §25 | 0,2,27 | MAN-WIN-01; MAN-PACK-01 | Manual + static review | Platform gate. |
| REQ-PROD-02 | V1 operates on the primary display only. | Spec §2.1 | 26 | MAN-WIN-12 | Manual | No multi-monitor behavior required. |
| REQ-PROD-03 | DeskBoard is local-first, account-free, and personal-use stability precedes public release. | Spec §1, §29 | 1,28,29 | MAN-REL-01; MAN-STAB-01 | Manual + review | No account/login flow. |
| REQ-SCOPE-01 | V1 must not add WorkerW, multi-monitor, edge auto-hide, dark theme, plugins, arbitrary securities, finance charts/history/news, cloud/sync, reminders, imports/exports, auto-backup, auto-update, portable build, localhost server, CDN assets, API-key flow, proxy configuration, or AKShare. | Spec §2.2 | 0–29 | REV-SCOPE-01 | Static/code review | Scope guard; no runtime test can prove all absences. |
| REQ-ARCH-01 | Use modular monolith dependency direction UI → Services → Repositories/Providers → SQLite/HTTP. | Spec §3 | 2–25 | REV-ARCH-01 | Architecture review | No reverse dependencies. |
| REQ-ARCH-02 | Dashboard uses exactly one QWebEngineView with local HTML/CSS/ES Modules + GridStack + QWebChannel. | Spec §3, §5.2, §24–25 | 0,3,11,12,14,23,27 | MAN-WIN-02; AUT-STATE-01 | Manual + integration | Settings must not add another WebEngine. |
| REQ-ARCH-03 | Settings is a native PySide6 Widgets window and must not create a QWebEngineView. | Spec §3.2, §19 | 0,3,24,25 | MAN-WIN-03; MAN-SET-01 | Manual | Native settings only. |
| REQ-ARCH-04 | JavaScript is render-state only; Python remains business source of truth. | Spec §3.1, §22 | 7,10–12,17,22 | AUT-PRES-01; AUT-STATE-02; REV-ARCH-02 | Automated + review | No business-rule duplication in JS. |
| REQ-ARCH-05 | QWebChannel bridge maps commands/events only; no SQL, HTTP, or domain logic in bridge. | Spec §3.3, §22 | 7,11,12,14,17,22 | AUT-BRIDGE-01; REV-ARCH-03 | Automated + review | Bridge is adapter only. |
| REQ-ARCH-06 | Persistence ownership is explicit: Settings→app_settings; Todo→todos; Course→course tables; Profile→profile tables; Weather→weather_cities; Finance→finance_preferences; Network→network_cache/network_state. | Spec §3.5 | 5,6,9,13,15,16,18 | AUT-DB-01; REV-DB-01 | Automated + review | Weather/Finance payloads never stored by their config repositories. |
| REQ-ARCH-07 | Providers only fetch, parse, normalize; no SQLite/UI/status/retry ownership. | Spec §3.6 | 1,15–21 | AUT-PROV-01; REV-PROV-01 | Automated + review | Direct HTTP provider boundary. |
| REQ-DB-01 | Persistent root is %LOCALAPPDATA%\DeskBoard with data\deskboard.db and logs\. | Spec §4 | 2,5 | AUT-INFRA-01; MAN-PACK-02 | Automated + manual | User data outside Program Files. |
| REQ-DB-02 | No automatic database backup in V1. | Spec §4 | 5,27 | REV-SCOPE-02 | Static review | No backup scheduler/files. |
| REQ-DB-03 | SQLite foreign keys enabled; explicit schema version/migrations; transactions for multi-row/multi-table changes. | Spec §4, §21 | 5 | AUT-DB-02..06 | Automated | Migration/repository gate. |
| REQ-DB-04 | All DeskBoard-owned persistent user configuration uses SQLite; no second QSettings/JSON/YAML/TOML store. OS integration state such as autostart registry is exempt. | Spec §4 | 5,24–26 | AUT-DB-07; REV-DB-02 | Automated + review | Registry is OS integration, not second app config. |
| REQ-WIN-01 | Z-order is ordinary apps above DeskBoard above Windows desktop; no behind-icons embedding. | Spec §5.1 | 0,4,26 | MAN-WIN-04 | Manual | Task 0 hard gate. |
| REQ-WIN-02 | Dashboard is frameless, transparent outer window, no normal close button, and not a normal taskbar window. | Spec §5.2 | 0,3,4 | MAN-WIN-05 | Manual | Production shell acceptance. |
| REQ-WIN-03 | Dashboard is a freely positioned/resizable small rectangular panel, not forced full screen; starts visible on each launch. | Spec §5.2 | 3,14,26 | MAN-WIN-06; AUT-START-01 | Manual + automated | Final minimum size set later. |
| REQ-WIN-04 | Final Dashboard/widget readability minimums are established by UI readability gate, not guessed early. | Spec §5.2, §8 | 14,23 | MAN-UI-01 | Manual | Conservative technical bounds allowed before Task 23. |
| REQ-MODE-01 | Legal modes are locked, interaction, layout_edit. | Spec §5.3 | 2,3,4,14 | AUT-APP-01 | Automated | Mode enum. |
| REQ-MODE-02 | Locked mode is view-only with true Windows pointer pass-through; no Todo scrolling/interaction, timetable opening, or layout editing. | Spec §5.3 | 0,3,4,7,12,14 | MAN-WIN-07; MAN-TODO-01 | Manual | OS pass-through must be real. |
| REQ-MODE-03 | Interaction mode allows Todo interaction and Today Agenda timetable opening, while GridStack and Dashboard geometry stay fixed. | Spec §5.3 | 7,11,12,14 | AUT-BRIDGE-02; MAN-TODO-02 | Automated + manual | No layout drift in interaction. |
| REQ-MODE-04 | Layout Edit is entered from Settings, makes Dashboard editable/foreground, enables GridStack and whole-window move/resize/show-hide, disables normal Todo interaction, and shows Save/Cancel. | Spec §5.3 | 14,24 | AUT-PROFILE-08; MAN-LAYOUT-01 | Automated + manual | Edit-mode interaction isolation. |
| REQ-MODE-05 | Entering Layout Edit records prior daily mode; Save and Cancel both return to that prior Locked/Interaction mode. Restart from last recorded layout_edit restores Interaction. | Spec §5.3–5.4 | 14,26 | AUT-PROFILE-09; AUT-START-02 | Automated | Save/cancel and restart semantics differ intentionally. |
| REQ-START-01 | First-ever launch: Dashboard visible, Interaction mode, Settings opens once. | Spec §5.4 | 26 | AUT-START-03; MAN-WIN-08 | Automated + manual | First-run flag persisted in SQLite. |
| REQ-START-02 | Later launches: Dashboard always visible; last Profile and last daily mode restored; layout_edit restores Interaction. | Spec §5.4 | 13,26 | AUT-START-01..04 | Automated | Show/hide state itself is not persisted as startup hidden. |
| REQ-START-03 | No global hotkey in V1. | Spec §5.4 | 4,24 | REV-SCOPE-03 | Static review | Mode switch via tray/Settings. |
| REQ-TRAY-01 | Tray left-click opens/focuses Settings. | Spec §6 | 4 | MAN-TRAY-01 | Manual |  |
| REQ-TRAY-02 | Tray menu contains only Show/Hide Dashboard, Locked/Interaction switch, Open Settings, Exit. | Spec §6 | 4 | AUT-TRAY-01; MAN-TRAY-02 | Automated + manual | No Profile/layout/refresh/finance actions. |
| REQ-TRAY-03 | Closing Settings does not exit DeskBoard; Exit from tray or Settings exits application. | Spec §6 | 3,4,24 | MAN-TRAY-03 | Manual |  |
| REQ-TRAY-04 | Only one DeskBoard instance may run; second launch focuses/opens Settings in existing instance and exits. | Spec §6 | 4 | AUT-SINGLE-01; MAN-TRAY-04 | Automated + manual |  |
| REQ-WIDGET-01 | V1 widget keys are exactly weather, todo, today_agenda, gold, fx, china_indices, us_indices, finance_overview; max one instance of each per Profile. | Spec §7 | 5,11,13,17,22 | AUT-DB-08; AUT-PROFILE-01 | Automated | Reserved U.S. widget may be unavailable if no validated source. |
| REQ-WIDGET-02 | Financial widgets may repeat underlying items visually but share provider/cache data and do not cause duplicate requests. | Spec §7 | 15,22 | AUT-NET-12; AUT-FIN-12 | Automated |  |
| REQ-GRID-01 | Grid uses fixed 12-column topology; outer-window resize changes pixel cell size without responsive reflow of x/y/w/h. | Spec §8 | 0,14 | AUT-LAYOUT-01; MAN-LAYOUT-02 | Automated + manual |  |
| REQ-GRID-02 | Widget content adapts by actual pixel size; generic compact/normal/expanded is derived and not persisted. | Spec §8 | 17,22,23 | AUT-PROFILE-02; MAN-UI-02 | Automated + manual | Widget-specific display config may persist. |
| REQ-PROFILE-01 | Profile saves Dashboard geometry, widget layout/visibility, theme, opacity, and widget-specific display config. | Spec §9.2 | 13,14,23 | AUT-PROFILE-03..05 | Automated |  |
| REQ-PROFILE-02 | Profile does not save Todo/course/cities/primary city/finance choices/class periods/provider cache/network status. | Spec §9.3 | 13,15,16,18 | AUT-PROFILE-06; REV-PROFILE-01 | Automated + review | Global data remains global. |
| REQ-PROFILE-03 | Built-in Default exists, cannot be deleted/overwritten; up to 8 user Profiles; management only in Settings. | Spec §9.4 | 13,24 | AUT-PROFILE-07..11; MAN-SET-02 | Automated + manual |  |
| REQ-PROFILE-04 | Required actions: switch, save current, save as, rename, delete, restore Default. | Spec §9.4 | 13,24 | AUT-PROFILE-12; MAN-SET-03 | Automated + manual |  |
| REQ-PROFILE-05 | Saving Layout Edit while Default active opens native Save As prompt; confirm creates/switches user Profile and exits edit; dismiss stays in edit. | Spec §9.4 | 13,14,24 | AUT-PROFILE-13; MAN-LAYOUT-03 | Automated + manual |  |
| REQ-PROFILE-06 | Deleting active user Profile switches to Default; creating ninth user Profile is rejected. | Spec §9.4 | 13,24 | AUT-PROFILE-14..15 | Automated |  |
| REQ-THEME-01 | Exactly four light themes: Mist Blue, Mint Breeze, Almond Sand, Lavender Cloud; theme stored per Profile. | Spec §10 | 13,23,24 | AUT-PROFILE-16; MAN-UI-03 | Automated + manual | No dark theme. |
| REQ-THEME-02 | Visual style is minimal flat semi-transparent panel, subtle separators/rounding, almost no shadow, no acrylic/mica, no continuous animation; local assets only. | Spec §10 | 23,27 | MAN-UI-04; REV-UI-01 | Manual + review | clean > readable > fancy. |
| REQ-THEME-03 | Finance direction convention is red=up, green=down, explicit sign; gold may use theme accent. | Spec §10, §16.6 | 22,23 | AUT-FIN-11; MAN-UI-05 | Automated + manual |  |
| REQ-TODO-01 | Todo fields/semantics: content, optional deadline, optional planned date/time, completion via completed_at, manual display order; no priority/tags/subtasks/recurrence/reminders/etc. | Spec §11.1–11.2 | 5,6 | AUT-TODO-01; REV-TODO-01 | Automated + review |  |
| REQ-TODO-02 | Deadline combinations: date+time exact; date-only; time-only defaults date to today; neither means no deadline. | Spec §11.3 | 6 | AUT-TODO-02..05 | Automated |  |
| REQ-TODO-03 | Deadline alone never places Todo in Today Agenda/timetable; overdue incomplete Todo remains visible with only subtle warning allowed. | Spec §11.3 | 6,10,11,12,23 | AUT-TODO-06; AUT-AGENDA-06; AUT-TT-08 | Automated |  |
| REQ-TODO-04 | Planned forms: date-only, point time, range; time without date defaults today; range end > start. | Spec §11.4 | 6 | AUT-TODO-07..11 | Automated |  |
| REQ-TODO-05 | Main Todo widget shows all incomplete Todos regardless of future date plus Todos completed today; older completed Todos are excluded. | Spec §11.5 | 6,7 | AUT-TODO-12..14 | Automated |  |
| REQ-TODO-06 | Todo ordering is manual only: new item at top; completion does not move it; deadline/planned time do not auto-sort. | Spec §11.5 | 6,7 | AUT-TODO-15..18 | Automated |  |
| REQ-TODO-07 | Todo content area scrolls in Interaction Mode while title/add controls remain fixed; Locked mode is non-scrollable due pass-through. | Spec §11.5 | 7,23 | MAN-TODO-03; MAN-UI-06 | Manual |  |
| REQ-TODO-08 | Quick-add via + asks only content; Enter saves; checkbox toggles; drag reorders; right-click menu has Edit details, Mark complete/incomplete, Delete. | Spec §11.6 | 7 | AUT-BRIDGE-03..06; MAN-TODO-04 | Automated + manual |  |
| REQ-TODO-09 | Detailed edit uses native Qt dialog; deletion requires confirmation. | Spec §11.6 | 8 | AUT-TODO-19; MAN-TODO-05 | Automated + manual |  |
| REQ-TODO-10 | Settings Todo has Incomplete and Completed history; completed history supports view, restore, permanent delete with confirmation; no search/stats/tags/recycle bin. | Spec §11.7 | 8,25 | AUT-TODO-20..22; MAN-SET-04 | Automated + manual |  |
| REQ-TODO-11 | Completed today stays in position and uses pale/light green + check, no strikethrough; completed state carries into Agenda/timetable. | Spec §11.8 | 7,10–12,23 | AUT-PRES-02; AUT-AGENDA-07; AUT-TT-09; MAN-UI-07 | Automated + manual |  |
| REQ-COURSE-01 | Multiple semesters may exist; zero or one active; start_monday must be Monday; teaching week derived from local date; no automatic semester switching. | Spec §12.1 | 5,9,26 | AUT-COURSE-01..06 | Automated |  |
| REQ-COURSE-02 | Class periods: valid active set is exactly 8 unique period_no 1..8 with start/end; fresh install may be unconfigured; partial/duplicate/out-of-range invalid; do not invent times. | Spec §12.2 | 5,9,25 | AUT-COURSE-07..12; MAN-SET-05 | Automated + manual |  |
| REQ-COURSE-03 | Recurring course fields/validation: semester, name, weekday 1..7, actual start/end, start_week/end_week, optional classroom; repeats weekly; no odd/even field. | Spec §12.3 | 5,9 | AUT-COURSE-13..17 | Automated |  |
| REQ-COURSE-04 | Blank classroom is not displayed. | Spec §12.3 | 10,11,12 | AUT-PRES-03 | Automated |  |
| REQ-COURSE-05 | Cancellation uniquely targets one recurring occurrence date and suppresses only that occurrence. | Spec §12.4 | 5,9 | AUT-COURSE-18..20 | Automated |  |
| REQ-COURSE-06 | One-off course uses explicit date/start/end/classroom; reschedule = cancellation + one-off, no reschedule relationship model. | Spec §12.5 | 5,9 | AUT-COURSE-21..24 | Automated |  |
| REQ-COURSE-07 | Outside active semester teaching range: recurring absent, timetable week label blank, matching one-off course may still render. | Spec §12.5 | 9,10,12 | AUT-COURSE-25; AUT-TT-01..02 | Automated |  |
| REQ-COURSE-08 | Course/semester editing, cancellations, one-offs are Settings-only, not direct Dashboard edits. | Spec §12.5 | 25 | MAN-SET-06; REV-SCOPE-04 | Manual + review |  |
| REQ-AGENDA-01 | Today Agenda is derived, not persisted; combines CourseService + TodoService through AgendaService. | Spec §13 | 10,11 | AUT-AGENDA-01; REV-DB-03 | Automated + review | No agenda/schedule table. |
| REQ-AGENDA-02 | Timed section contains today's actual courses + point/range planned Todos and sorts by start time. | Spec §13.1 | 10,11 | AUT-AGENDA-02..04 | Automated |  |
| REQ-AGENDA-03 | Past and future timed items remain visible all day; no time-passed hide/grey. | Spec §13.1 | 10,11,23 | AUT-AGENDA-05; MAN-UI-08 | Automated + manual |  |
| REQ-AGENDA-04 | Date-only planned Todo for today appears after timed items; multiple date-only items follow Todo manual order. | Spec §13.2 | 10,11 | AUT-AGENDA-08..10 | Automated |  |
| REQ-AGENDA-05 | Todo with no planned date/time does not appear; deadline alone does not appear. | Spec §13.2 | 10,11 | AUT-AGENDA-06; AUT-AGENDA-11 | Automated |  |
| REQ-AGENDA-06 | Today Agenda is view-only; rows not editable/completable; title click in Interaction opens timetable. | Spec §13.3 | 11,12 | AUT-BRIDGE-07; MAN-AGENDA-01 | Automated + manual |  |
| REQ-TT-01 | Weekly timetable is an overlay inside the single Dashboard Web page, view-only, current local week only, Mon–Sun seven columns, no week navigation. | Spec §14, §14.1 | 12 | AUT-TT-03..05; MAN-TT-01 | Automated + manual |  |
| REQ-TT-02 | Week label is 第N周 inside teaching range and blank outside. | Spec §14.1 | 10,12 | AUT-TT-01..02 | Automated |  |
| REQ-TT-03 | Header mode supports weekday only, weekday+date, date only. | Spec §14.2 | 10,12,25 | AUT-TT-06; MAN-TT-02 | Automated + manual |  |
| REQ-TT-04 | Vertical axis uses continuous real clock time; labels 1..8; visible range is period1.start to period8.end; events outside range excluded. | Spec §14.3 | 10,12 | AUT-TT-07; AUT-TT-10..11; MAN-TT-03 | Automated + manual |  |
| REQ-TT-05 | If period set unconfigured, overlay shows compact configure-first state and does not invent bounds; Today Agenda still works. | Spec §14.3 | 9,10,12 | AUT-TT-12; MAN-TT-04 | Automated + manual |  |
| REQ-TT-06 | Course blocks use actual start/end and are not snapped to period cells. | Spec §14.4 | 10,12 | AUT-TT-13; MAN-TT-05 | Automated + manual |  |
| REQ-TT-07 | Only planned-time Todos appear: point→thin exact marker, range→normal block, date-only excluded; must be current week and inside visible range. | Spec §14.5 | 10,12 | AUT-TT-14..18; MAN-TT-06 | Automated + manual |  |
| REQ-TT-08 | Past timetable events remain rendered normally; no automatic hide/grey due solely to elapsed time. | Spec §14.6 | 10,12,23 | AUT-TT-19; MAN-UI-09 | Automated + manual |  |
| REQ-TT-09 | Course/Todo overlap allowed; course visual priority; Todo narrow/secondary + light overlap; no blocking or auto-reschedule. | Spec §14.7 | 10,12,23 | AUT-TT-20..21; MAN-TT-07 | Automated + manual |  |
| REQ-WEATHER-01 | Normalized weather fields are city, condition, current_temperature, high, low, wind; no feels-like/precip/AQI/lifestyle fields required. | Spec §15.1 | 16,17 | AUT-WTH-01..02 | Automated |  |
| REQ-WEATHER-02 | Global weather city list has order and exactly one primary city; mainland-China support required; overseas optional. | Spec §15.2 | 16,24 | AUT-WTH-03..06; MAN-PROV-01 | Automated + manual |  |
| REQ-WEATHER-03 | Small/normal weather prioritizes primary city; Profile may choose expanded single-city detail vs multi-city summary. | Spec §15.3 | 13,17,23 | AUT-WTH-07..08; MAN-UI-10 | Automated + manual |  |
| REQ-WEATHER-04 | Multi-city summary follows global order, shows as many as fit, and does not require scrolling. | Spec §15.3 | 17,23 | AUT-WTH-09; MAN-UI-11 | Automated + manual |  |
| REQ-FIN-01 | Finance is lightweight reference info only; catalog includes only Task 1 validated built-in items; no arbitrary user codes. | Spec §16.1–16.2 | 1,18 | AUT-FIN-01..03; REV-SCOPE-05 | Automated + review |  |
| REQ-FIN-02 | Finance enable/disable and order are global, not Profile-specific. | Spec §16.2 | 18,24 | AUT-FIN-04..06 | Automated |  |
| REQ-FIN-03 | Candidate starting set includes Au99.99, USD/EUR/JPY/HKD CNY, major A-share and U.S. indices subject to validation; U.S. widget reserved but unavailable/hidden if no source passes. | Spec §16.3 | 1,18–21 | AUT-FIN-07; MAN-PROV-05 | Automated + manual |  |
| REQ-FIN-04 | Finance display is name/value/change% where meaningful + optional closed label; no charts/history; capacity grows with widget size; no scrolling/pagination. | Spec §16.4 | 22,23 | AUT-FIN-08..10; MAN-UI-12 | Automated + manual |  |
| REQ-FIN-05 | FX normalizes to 1 foreign unit = CNY regardless of upstream basis. | Spec §16.4 | 19 | AUT-FX-01..04 | Automated |  |
| REQ-FIN-06 | When reliably closed, show latest completed-session close with 上一交易日收盘; if market state unknown, show value without guessing label; no front last-success timestamp. | Spec §16.5 | 19–22 | AUT-FIN-13..15; MAN-UI-13 | Automated + manual |  |
| REQ-SOURCE-01 | Every shipped network source works on ordinary mainland-China internet with no VPN/proxy/Clash and no user API key/account; app has no proxy settings. | Spec §17.1 | 1,16,19–21,29 | MAN-PROV-01..05; REV-SCOPE-06 | Manual + review | Hard release/source gate. |
| REQ-SOURCE-02 | Source preference is official no-auth public → parsable official page → stable public JSON/HTTP → defer; no runtime multi-source fallback chain. | Spec §17.2 | 1,16,19–21 | REV-PROV-02; MAN-PROV-06 | Review + manual | One selected provider per logical item/group. |
| REQ-SOURCE-03 | Public release requires separate attribution/terms review; technical access alone is insufficient. | Spec §17.3, §29 | 29 | MAN-REL-02..04 | Manual/review |  |
| REQ-NET-01 | Automatic refresh interval fixed at 60 minutes; hiding Dashboard does not stop refresh; only app exit stops it. | Spec §18.1 | 15,26 | AUT-NET-01..02; MAN-STAB-02 | Automated + manual |  |
| REQ-NET-02 | Startup loads cache immediately; fresh <60m cache skips refetch and restores prior status; stale cache displays then refreshes; no cache displays 暂无数据 then refreshes. | Spec §18.2 | 15,17,22,26 | AUT-NET-03..07; MAN-NET-01 | Automated + manual |  |
| REQ-NET-03 | Network I/O never blocks Qt GUI; preferred QThreadPool+QRunnable; one active refresh per group; duplicate same-group manual request ignored/disabled, not queued. | Spec §18.3 | 15 | AUT-NET-08..10; MAN-NET-02 | Automated + manual |  |
| REQ-NET-04 | Provider groups/items fail independently; successful payloads persist even if another group fails; no whole-round rollback. | Spec §18.4 | 15,17,19–21 | AUT-NET-11..13 | Automated |  |
| REQ-NET-05 | Failure never overwrites last successful cache; state/error separate; no short retry; no connectivity-probe gate. | Spec §18.5 | 15 | AUT-NET-14..18 | Automated |  |
| REQ-NET-06 | Settings Data Status has Refresh All + provider-group refresh; manual and automatic use same DataRefreshService; front has no refresh controls. | Spec §18.6 | 15,24,25 | AUT-NET-19; MAN-SET-07; REV-SCOPE-07 | Automated + manual/review |  |
| REQ-NET-07 | Exactly one global status dot: grey refresh/unknown, green all enabled success, red any enabled failure; only globally enabled network data participates; Profile visibility and local data do not. | Spec §18.7 | 15,17,22 | AUT-NET-20..25; MAN-UI-14 | Automated + manual |  |
| REQ-NET-08 | Fresh-cache startup reuses last-known green/red; no known state grey; zero enabled/configured network items grey; status color is derived, not persisted. | Spec §18.7, §21.2 | 15,26 | AUT-NET-26..29 | Automated |  |
| REQ-SET-01 | Native Settings pages: General, Profiles, Weather, Finance, Todo, Courses, Data Status, About. | Spec §19 | 24,25 | MAN-SET-01..09 | Manual |  |
| REQ-SET-02 | Simple settings may apply immediately; structured object editing uses explicit Save/Cancel. | Spec §19.1 | 24,25 | AUT-SET-01; MAN-SET-10 | Automated + manual |  |
| REQ-SET-03 | General includes Dashboard show/hide, Locked/Interaction, enter Layout Edit, autostart, exit. | Spec §19.2 | 24,26 | MAN-SET-11 | Manual |  |
| REQ-SET-04 | Data Status shows source/group, last attempt, last success, success/failure, readable error, attribution, refresh controls, Open Log Folder. | Spec §19.3 | 25 | AUT-SET-02; MAN-SET-12 | Automated + manual |  |
| REQ-SET-05 | About shows name, version, source/disclaimer references; no auto-update. | Spec §19.4 | 25,29 | MAN-SET-13; REV-SCOPE-08 | Manual + review |  |
| REQ-TIME-01 | Todo/course/semester/day-rollover use Windows system local time; no separate app timezone; remote weather city does not change it. | Spec §20 | 5,6,9,10,26 | AUT-TIME-01..04 | Automated |  |
| REQ-TIME-02 | Python-side lightweight day-rollover timer refreshes date-dependent views near local midnight; no one-second JS clock polling. | Spec §20 | 26 | AUT-START-05; REV-PERF-01 | Automated + review |  |
| REQ-DBMODEL-01 | V1 logical tables are exactly schema_meta, app_settings, todos, semesters, recurring_courses, course_cancellations, one_off_courses, class_periods, profiles, profile_widgets, weather_cities, finance_preferences, network_cache, network_state. | Spec §21 | 5 | AUT-DB-08 | Automated |  |
| REQ-DBMODEL-02 | Key constraints/cascades: unique cancellation occurrence, period_no 1..8, unique profile/widget, max 8 user Profiles, FK enabled, semester/course/profile cascades, no generic soft-delete. | Spec §21.1 | 5,6,9,13 | AUT-DB-09..16 | Automated |  |
| REQ-DBMODEL-03 | network_cache stores only successful normalized payload/time; network_state stores attempt/status/error; failure updates state without destroying cache; dot color not stored. | Spec §21.2 | 5,15 | AUT-NET-14; AUT-NET-29 | Automated |  |
| REQ-BRIDGE-01 | Initial Dashboard load obtains one coarse state snapshot rather than many small getters. | Spec §22.1 | 11 | AUT-STATE-01 | Automated |  |
| REQ-BRIDGE-02 | Bridge semantic commands include initial state, quick-add/toggle/reorder Todo, open Todo editor/delete, weekly timetable, save/cancel layout. | Spec §22.2 | 7,8,11,12,14 | AUT-BRIDGE-01..07 | Automated | Exact Qt signatures may adapt only for serialization. |
| REQ-BRIDGE-03 | Expected event families include state/todos/agenda/weather/finance/profile/networkStatus/mode changes; Python is source of truth. | Spec §22.3 | 7,11,14,17,22,26 | AUT-BRIDGE-08; AUT-STATE-02 | Automated |  |
| REQ-BRIDGE-04 | Presentation models hide raw SQLite/provider fields; presenter computes overdue/completed/order/formatted finance/conflict/normalized weather; pixel positioning stays Web-side. | Spec §22.4 | 7,10–12,17,22 | AUT-PRES-01..07 | Automated |  |
| REQ-LOG-01 | Use lightweight rotating logs; record useful startup/provider/SQLite/migration/WebEngine/runtime failures; no high-frequency noise; Settings can open log folder; no embedded viewer. | Spec §23 | 2,25 | AUT-INFRA-02..04; MAN-SET-12 | Automated + manual |  |
| REQ-PERF-01 | Idle CPU near zero, no continuous memory growth, <~200MB preferred not hard, one WebEngine, no high-frequency polling/network/animation, hide/show without destroying WebEngine. | Spec §24 | 0,23,26,28 | MAN-PERF-01..07; REV-PERF-01 | Manual + review |  |
| REQ-DEP-01 | Core stack is Python3.12/PySide6/requests/sqlite3/dataclasses/GridStack/pytest/ruff/PyInstaller/Inno; BS4 only if selected source needs it; prohibited major stack additions require spec change. | Spec §25 | 2,16,19–21,27 | REV-DEP-01 | Static/code review | No Node build chain. |
| REQ-PACK-01 | Production packaging is PyInstaller onedir → Inno Setup installer; installed app requires no Python; user data in LOCALAPPDATA; standard installer only. | Spec §26 | 0,27 | MAN-PACK-01..06 | Manual |  |
| REQ-PACK-02 | Autostart is current-user, default OFF, no service/admin requirement; uninstall must not silently destroy personal data. | Spec §26 | 24,26,27 | AUT-START-06; MAN-PACK-07..09 | Automated + manual |  |
| REQ-TEST-01 | Automated deterministic coverage includes Todo, course, Agenda/timetable metadata, Profiles, repositories, provider fixtures, presenters, cache/status; normal pytest never needs live internet. | Spec §27.1 | 5–22 | TEST-MATRIX | Automated | Detailed cases in test-matrix.md. |
| REQ-TEST-02 | Real Windows/manual evidence is required for Z-order, pointer pass-through, tray, WebEngine, GridStack feel, packaging/installer, sleep/wake/long-run, mainland direct provider access. | Spec §27.2 | 0,1,4,12,14,17,19–23,27,28 | MAN-* | Manual |  |
| REQ-GATE-01 | Formal feature implementation cannot begin until Phase 0 proves Windows shell, WebEngine/GridStack, performance baseline, PyInstaller, native Settings coexistence, and mandatory mainland-direct provider viability. | Spec §27.3 | 0,1 | MAN-WIN-*; MAN-PROV-* | Manual | Both Task 0 and Task 1 must close. |
| REQ-DONE-01 | V1 completion requires all core behavior, validated providers, refresh/status, Settings/tray/startup, low idle overhead/no obvious leak, installer, automated tests, manual evidence, diagnosability. | Spec §28 | 28 | MAN-STAB-01..08; REV-DONE-01 | Manual + review | No placeholder-only core area. |
| REQ-REL-01 | Public GitHub release only after personal-use stability; re-check mainland access, source terms/attribution, clean installer, no secrets; no trading-grade claims. | Spec §29 | 29 | MAN-REL-01..06 | Manual/review | Release gate. |

## Task → Requirement Index

### Task 0: Windows / QWebEngine / Packaging Risk Spike

`REQ-ARCH-02`, `REQ-ARCH-03`, `REQ-GATE-01`, `REQ-GRID-01`, `REQ-MODE-02`, `REQ-PACK-01`, `REQ-PERF-01`, `REQ-PROD-01`, `REQ-SCOPE-01`, `REQ-TEST-02`, `REQ-WIN-01`, `REQ-WIN-02`

### Task 1: Mainland-China Provider Source Gate

`REQ-ARCH-07`, `REQ-FIN-01`, `REQ-FIN-03`, `REQ-GATE-01`, `REQ-PROD-03`, `REQ-SCOPE-01`, `REQ-SOURCE-01`, `REQ-SOURCE-02`, `REQ-TEST-02`

### Task 2: Project Skeleton, Modes, Paths, and Logging

`REQ-ARCH-01`, `REQ-DB-01`, `REQ-DEP-01`, `REQ-LOG-01`, `REQ-MODE-01`, `REQ-PROD-01`, `REQ-SCOPE-01`

### Task 3: Application Shell, Dashboard Window, and Native Settings Window

`REQ-ARCH-01`, `REQ-ARCH-02`, `REQ-ARCH-03`, `REQ-MODE-01`, `REQ-MODE-02`, `REQ-SCOPE-01`, `REQ-TRAY-03`, `REQ-WIN-02`, `REQ-WIN-03`

### Task 4: Tray, Single Instance, and Shell Acceptance

`REQ-ARCH-01`, `REQ-MODE-01`, `REQ-MODE-02`, `REQ-SCOPE-01`, `REQ-START-03`, `REQ-TEST-02`, `REQ-TRAY-01`, `REQ-TRAY-02`, `REQ-TRAY-03`, `REQ-TRAY-04`, `REQ-WIN-01`, `REQ-WIN-02`

### Task 5: SQLite Schema, Migrations, Repository Ownership, and Clock

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-COURSE-01`, `REQ-COURSE-02`, `REQ-COURSE-03`, `REQ-COURSE-05`, `REQ-COURSE-06`, `REQ-DB-01`, `REQ-DB-02`, `REQ-DB-03`, `REQ-DB-04`, `REQ-DBMODEL-01`, `REQ-DBMODEL-02`, `REQ-DBMODEL-03`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TIME-01`, `REQ-TODO-01`, `REQ-WIDGET-01`

### Task 6: Todo Domain, Repository, and Service

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-DBMODEL-02`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TIME-01`, `REQ-TODO-01`, `REQ-TODO-02`, `REQ-TODO-03`, `REQ-TODO-04`, `REQ-TODO-05`, `REQ-TODO-06`

### Task 7: Todo Presenter and Dashboard Interaction

`REQ-ARCH-01`, `REQ-ARCH-04`, `REQ-ARCH-05`, `REQ-BRIDGE-02`, `REQ-BRIDGE-03`, `REQ-BRIDGE-04`, `REQ-MODE-02`, `REQ-MODE-03`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TODO-05`, `REQ-TODO-06`, `REQ-TODO-07`, `REQ-TODO-08`, `REQ-TODO-11`

### Task 8: Todo Native Editor, Delete Confirmation, and Settings History

`REQ-ARCH-01`, `REQ-BRIDGE-02`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TODO-09`, `REQ-TODO-10`

### Task 9: Semester and Course Domain

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-COURSE-01`, `REQ-COURSE-02`, `REQ-COURSE-03`, `REQ-COURSE-05`, `REQ-COURSE-06`, `REQ-COURSE-07`, `REQ-DBMODEL-02`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TIME-01`, `REQ-TT-05`

### Task 10: Agenda and Timetable Domain/Presentation

`REQ-AGENDA-01`, `REQ-AGENDA-02`, `REQ-AGENDA-03`, `REQ-AGENDA-04`, `REQ-AGENDA-05`, `REQ-ARCH-01`, `REQ-ARCH-04`, `REQ-BRIDGE-04`, `REQ-COURSE-04`, `REQ-COURSE-07`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TIME-01`, `REQ-TODO-03`, `REQ-TODO-11`, `REQ-TT-02`, `REQ-TT-03`, `REQ-TT-04`, `REQ-TT-05`, `REQ-TT-06`, `REQ-TT-07`, `REQ-TT-08`, `REQ-TT-09`

### Task 11: Dashboard State Snapshot and Today Agenda Widget

`REQ-AGENDA-01`, `REQ-AGENDA-02`, `REQ-AGENDA-03`, `REQ-AGENDA-04`, `REQ-AGENDA-05`, `REQ-AGENDA-06`, `REQ-ARCH-01`, `REQ-ARCH-02`, `REQ-ARCH-04`, `REQ-ARCH-05`, `REQ-BRIDGE-01`, `REQ-BRIDGE-02`, `REQ-BRIDGE-03`, `REQ-BRIDGE-04`, `REQ-COURSE-04`, `REQ-MODE-03`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TODO-03`, `REQ-TODO-11`, `REQ-WIDGET-01`

### Task 12: Weekly Timetable Overlay

`REQ-AGENDA-06`, `REQ-ARCH-01`, `REQ-ARCH-02`, `REQ-ARCH-04`, `REQ-ARCH-05`, `REQ-BRIDGE-02`, `REQ-BRIDGE-04`, `REQ-COURSE-04`, `REQ-COURSE-07`, `REQ-MODE-02`, `REQ-MODE-03`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TEST-02`, `REQ-TODO-03`, `REQ-TODO-11`, `REQ-TT-01`, `REQ-TT-02`, `REQ-TT-03`, `REQ-TT-04`, `REQ-TT-05`, `REQ-TT-06`, `REQ-TT-07`, `REQ-TT-08`, `REQ-TT-09`

### Task 13: Profile Domain and Persistence

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-DBMODEL-02`, `REQ-PROFILE-01`, `REQ-PROFILE-02`, `REQ-PROFILE-03`, `REQ-PROFILE-04`, `REQ-PROFILE-05`, `REQ-PROFILE-06`, `REQ-SCOPE-01`, `REQ-START-02`, `REQ-TEST-01`, `REQ-THEME-01`, `REQ-WEATHER-03`, `REQ-WIDGET-01`

### Task 14: GridStack Layout Editing and Dashboard Geometry

`REQ-ARCH-01`, `REQ-ARCH-02`, `REQ-ARCH-05`, `REQ-BRIDGE-02`, `REQ-BRIDGE-03`, `REQ-GRID-01`, `REQ-MODE-01`, `REQ-MODE-02`, `REQ-MODE-03`, `REQ-MODE-04`, `REQ-MODE-05`, `REQ-PROFILE-01`, `REQ-PROFILE-05`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TEST-02`, `REQ-WIN-03`, `REQ-WIN-04`

### Task 15: Network Cache, Refresh, and Global Status Foundation

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-ARCH-07`, `REQ-DBMODEL-03`, `REQ-NET-01`, `REQ-NET-02`, `REQ-NET-03`, `REQ-NET-04`, `REQ-NET-05`, `REQ-NET-06`, `REQ-NET-07`, `REQ-NET-08`, `REQ-PROFILE-02`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-WIDGET-02`

### Task 16: Weather Provider and City Domain

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-ARCH-07`, `REQ-DEP-01`, `REQ-PROFILE-02`, `REQ-SCOPE-01`, `REQ-SOURCE-01`, `REQ-SOURCE-02`, `REQ-TEST-01`, `REQ-WEATHER-01`, `REQ-WEATHER-02`

### Task 17: Weather Presenter, Dashboard Widget, and Refresh Integration

`REQ-ARCH-01`, `REQ-ARCH-04`, `REQ-ARCH-05`, `REQ-ARCH-07`, `REQ-BRIDGE-03`, `REQ-BRIDGE-04`, `REQ-GRID-02`, `REQ-NET-02`, `REQ-NET-04`, `REQ-NET-07`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TEST-02`, `REQ-WEATHER-01`, `REQ-WEATHER-03`, `REQ-WEATHER-04`, `REQ-WIDGET-01`

### Task 18: Finance Catalog and Global Preferences

`REQ-ARCH-01`, `REQ-ARCH-06`, `REQ-ARCH-07`, `REQ-FIN-01`, `REQ-FIN-02`, `REQ-FIN-03`, `REQ-PROFILE-02`, `REQ-SCOPE-01`, `REQ-TEST-01`

### Task 19: Gold and CNY FX Providers

`REQ-ARCH-01`, `REQ-ARCH-07`, `REQ-DEP-01`, `REQ-FIN-03`, `REQ-FIN-05`, `REQ-FIN-06`, `REQ-NET-04`, `REQ-SCOPE-01`, `REQ-SOURCE-01`, `REQ-SOURCE-02`, `REQ-TEST-01`, `REQ-TEST-02`

### Task 20: China Index Provider

`REQ-ARCH-01`, `REQ-ARCH-07`, `REQ-DEP-01`, `REQ-FIN-03`, `REQ-FIN-06`, `REQ-NET-04`, `REQ-SCOPE-01`, `REQ-SOURCE-01`, `REQ-SOURCE-02`, `REQ-TEST-01`, `REQ-TEST-02`

### Task 21: U.S. Index Provider or Explicit V1 Deferral

`REQ-ARCH-01`, `REQ-ARCH-07`, `REQ-DEP-01`, `REQ-FIN-03`, `REQ-FIN-06`, `REQ-NET-04`, `REQ-SCOPE-01`, `REQ-SOURCE-01`, `REQ-SOURCE-02`, `REQ-TEST-01`, `REQ-TEST-02`

### Task 22: Finance Presenter and Dashboard Widgets

`REQ-ARCH-01`, `REQ-ARCH-04`, `REQ-ARCH-05`, `REQ-BRIDGE-03`, `REQ-BRIDGE-04`, `REQ-FIN-04`, `REQ-FIN-06`, `REQ-GRID-02`, `REQ-NET-02`, `REQ-NET-07`, `REQ-SCOPE-01`, `REQ-TEST-01`, `REQ-TEST-02`, `REQ-THEME-03`, `REQ-WIDGET-01`, `REQ-WIDGET-02`

### Task 23: Dashboard Visual Baseline, Themes, and Readability Gate

`REQ-AGENDA-03`, `REQ-ARCH-01`, `REQ-ARCH-02`, `REQ-FIN-04`, `REQ-GRID-02`, `REQ-PERF-01`, `REQ-PROFILE-01`, `REQ-SCOPE-01`, `REQ-TEST-02`, `REQ-THEME-01`, `REQ-THEME-02`, `REQ-THEME-03`, `REQ-TODO-03`, `REQ-TODO-07`, `REQ-TODO-11`, `REQ-TT-08`, `REQ-TT-09`, `REQ-WEATHER-03`, `REQ-WEATHER-04`, `REQ-WIN-04`

### Task 24: General, Profile, Weather, and Finance Settings

`REQ-ARCH-01`, `REQ-ARCH-03`, `REQ-DB-04`, `REQ-FIN-02`, `REQ-MODE-04`, `REQ-NET-06`, `REQ-PACK-02`, `REQ-PROFILE-03`, `REQ-PROFILE-04`, `REQ-PROFILE-05`, `REQ-PROFILE-06`, `REQ-SCOPE-01`, `REQ-SET-01`, `REQ-SET-02`, `REQ-SET-03`, `REQ-START-03`, `REQ-THEME-01`, `REQ-TRAY-03`, `REQ-WEATHER-02`

### Task 25: Todo, Course, Data Status, and About Settings

`REQ-ARCH-01`, `REQ-ARCH-03`, `REQ-COURSE-02`, `REQ-COURSE-08`, `REQ-DB-04`, `REQ-LOG-01`, `REQ-NET-06`, `REQ-SCOPE-01`, `REQ-SET-01`, `REQ-SET-02`, `REQ-SET-04`, `REQ-SET-05`, `REQ-TODO-10`, `REQ-TT-03`

### Task 26: Startup, Day Rollover, Window Recovery, and Windows Behavior Hardening

`REQ-BRIDGE-03`, `REQ-COURSE-01`, `REQ-DB-04`, `REQ-MODE-05`, `REQ-NET-01`, `REQ-NET-02`, `REQ-NET-08`, `REQ-PACK-02`, `REQ-PERF-01`, `REQ-PROD-02`, `REQ-SCOPE-01`, `REQ-SET-03`, `REQ-START-01`, `REQ-START-02`, `REQ-TIME-01`, `REQ-TIME-02`, `REQ-WIN-01`, `REQ-WIN-03`

### Task 27: Production Packaging and Installer

`REQ-ARCH-02`, `REQ-DB-02`, `REQ-DEP-01`, `REQ-PACK-01`, `REQ-PACK-02`, `REQ-PROD-01`, `REQ-SCOPE-01`, `REQ-TEST-02`, `REQ-THEME-02`

### Task 28: Stability and Performance Manual Acceptance Gate

`REQ-DONE-01`, `REQ-PERF-01`, `REQ-PROD-03`, `REQ-SCOPE-01`, `REQ-TEST-02`

### Task 29: Documentation and Public Release Gate

`REQ-PROD-03`, `REQ-REL-01`, `REQ-SCOPE-01`, `REQ-SET-05`, `REQ-SOURCE-01`, `REQ-SOURCE-03`

## Traceability Maintenance Rule

When `docs/spec.md` changes:

1. update/add the affected `REQ-*` row here;
2. map it to the implementation task that owns the change;
3. add or update a concrete test/manual acceptance ID in `docs/quality/test-matrix.md`;
4. if no current task can own it cleanly, change the implementation plan **before** coding.

When only implementation details change without product-semantic change, do not rewrite unrelated rows.
