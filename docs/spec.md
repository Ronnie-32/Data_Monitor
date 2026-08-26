# DeskBoard Product Specification

**Status:** V1 product specification  
**Platform:** Windows 10/11 64-bit  
**Development baseline:** Python 3.12.x  
**Primary objective:** stable personal daily use first; public GitHub release only after stability and data-source review.

---

## 1. Product Definition

DeskBoard is a **local Windows desktop information dashboard** that stays visually available above the Windows desktop but below ordinary application windows. It aggregates lightweight personal information—Todo, course arrangements, weather, and a small set of verified financial reference data—without becoming a full task manager, finance terminal, course-management platform, cloud service, or generic widget/plugin framework.

V1 priorities, in order:

1. stable daily personal use;
2. clean and flexible desktop presentation;
3. low idle CPU and reasonable memory use;
4. simple maintainable architecture;
5. later GitHub publication after real personal-use stability.

The product is intentionally local-first and account-free.

---

## 2. V1 Scope and Non-Goals

### 2.1 In scope

- Windows 10/11 64-bit desktop application.
- Primary-display operation only.
- Frameless desktop Dashboard.
- Locked, Interaction, and Layout Edit modes.
- Eight built-in widget types.
- Todo management.
- Semester/course management.
- Today Agenda aggregation.
- Current-week timetable overlay.
- Weather for mainland-China cities; overseas-city support is optional and non-blocking.
- Verified built-in financial items from mainland-China-direct-accessible sources.
- Multiple Dashboard Profiles.
- A curated set of light, dark, and high-contrast Dashboard themes.
- Global network-status indicator.
- Local SQLite persistence.
- Lightweight rotating logs.
- System tray.
- Optional Windows autostart, default OFF.
- Standard Windows installer.

### 2.2 Explicitly out of V1

Do not add any of the following to V1:

- WorkerW / behind-desktop-icons embedding;
- multi-monitor support;
- edge auto-hide / side dock behavior;
- plugin/custom-widget system;
- user scripting API;
- arbitrary stock/security input;
- finance charts, history, news, or trading functions;
- cloud backend, accounts, login, or sync;
- reminders, notifications, alarms, or recurring Todo;
- Todo tags, priorities, subtasks, attachments, or project management;
- school-system import, CSV import, or ICS import;
- data import/export;
- automatic database backup;
- automatic application update;
- portable ZIP build;
- localhost HTTP server;
- runtime CDN assets;
- API-key registration flow;
- proxy/VPN/Clash configuration;
- AKShare.

A future feature idea is not permission to expand V1.

---

## 3. High-Level Architecture

DeskBoard is a **modular monolithic desktop application**.

```text
DeskBoard.exe
│
├─ PySide6 application shell
│  ├─ DashboardWindow
│  │   └─ one QWebEngineView
│  │       └─ local HTML/CSS/ES Modules + GridStack
│  ├─ native PySide6 SettingsWindow
│  └─ system tray
│
├─ QWebChannel DashboardBridge
│
├─ Application services
│  ├─ TodoService
│  ├─ CourseService
│  ├─ AgendaService
│  ├─ TimetableService
│  ├─ ProfileService
│  ├─ SettingsService
│  ├─ DataRefreshService
│  └─ StatusService
│
├─ Repositories
│  └─ SQLite
│
└─ Providers
   └─ direct HTTP sources
```

Required dependency direction:

```text
UI
 ↓
Application Services
 ↓
Repositories / Providers
 ↓
SQLite / HTTP sources
```

### 3.1 Dashboard Web layer

The Web layer owns:

- rendering;
- GridStack layout;
- widget size adaptation;
- themes;
- timetable visual positioning;
- Todo scrolling and lightweight interaction;
- Layout Edit drag/resize behavior.

The Web layer does **not** own business truth.

JavaScript must not:

- access SQLite;
- call external data sources;
- calculate teaching-week domain rules;
- calculate Todo overdue semantics;
- calculate global provider status;
- maintain a second authoritative Todo/course state.

### 3.2 Native Settings layer

Settings is a normal PySide6 window using native Qt Widgets. It must not create another QWebEngineView.

### 3.3 QWebChannel

QWebChannel is a bridge only. It maps user commands to services and Python state/events to JavaScript. It must not contain SQL, provider requests, or domain rules.

### 3.4 Services

Business behavior belongs in focused services reused by both Dashboard and Settings.

### 3.5 Repositories

Repositories own SQLite persistence only. Use Python stdlib `sqlite3`; no ORM is required.

Persistence ownership is explicit:

| Repository | Owned table(s) | Notes |
|---|---|---|
| `SettingsRepository` | `app_settings` | Small application settings only |
| `TodoRepository` | `todos` | Todo persistence only |
| `CourseRepository` | `semesters`, `timetable_schemes`, `timetable_scheme_periods`, `recurring_courses`, `course_cancellations`, `one_off_courses` | Semester/course domain only; legacy `class_periods` is migration input only |
| `ProfileRepository` | `profiles`, `profile_widgets` | Profile visual/spatial state only |
| `WeatherRepository` | `weather_cities` | City list/order/primary-city configuration only; **not weather payload cache** |
| `FinanceRepository` | `finance_preferences` | Enabled/order preferences only; **not market payload cache** |
| `NetworkRepository` | `network_cache`, `network_state` | All successful network payload cache and network attempt/error state, including Weather and Finance |

No repository may silently duplicate another repository's owned persistent state. In particular, Weather/Finance network payloads always use `NetworkRepository`; `WeatherRepository` and `FinanceRepository` own configuration only.

### 3.6 Providers

A Provider only:

1. fetches;
2. parses;
3. normalizes data into DeskBoard-owned models/results.

Providers do not write SQLite, update UI, calculate global status, or own retry scheduling.

---

## 4. Runtime Files and Persistence

Persistent data root:

```text
%LOCALAPPDATA%\DeskBoard\
├─ data\
│  └─ deskboard.db
└─ logs\
   ├─ deskboard.log
   ├─ deskboard.log.1
   └─ deskboard.log.2
```

No automatic database backup is required in V1.

SQLite must:

- enable foreign keys;
- maintain explicit schema-version metadata;
- use lightweight explicit migrations;
- use transactions for multi-row/multi-table state changes.

All DeskBoard-owned persistent user configuration uses SQLite and must not be duplicated in `QSettings`, JSON, YAML, TOML, or another application configuration store. OS-owned integration state such as a Windows autostart registry entry is exempt; DeskBoard may mirror the desired autostart setting in SQLite while the registry remains the operating-system integration mechanism.

---

## 5. Dashboard Window Behavior

### 5.1 Required window layer model

V1 requires:

```text
ordinary application windows
            ↑
         DeskBoard
            ↑
       Windows desktop
```

DeskBoard does not embed behind desktop icons.

The exact Windows Z-order technique must be proven during the Phase 0 risk gate.

### 5.2 Dashboard window

The Dashboard:

- is frameless;
- does not have a normal close button;
- does not appear as a normal taskbar window;
- has a transparent outer window;
- uses one QWebEngineView;
- can be shown/hidden from tray or Settings;
- is a freely positioned/resizable **small rectangular desktop panel**, not a full-screen or forced desktop-filling surface;
- may be resized within an overall minimum size established by the UI readability gate; that final minimum must not be invented before prototype/readability acceptance;
- starts visible on every application launch.

### 5.3 Operating modes

Legal modes:

```text
locked
interaction
layout_edit
```

#### Locked Mode

- view-only;
- true Windows pointer pass-through;
- no Todo interaction;
- no Todo scrolling;
- no timetable opening;
- no layout editing.

#### Interaction Mode

- GridStack layout is fixed;
- Todo can be added/completed/edited/deleted/reordered/scrolled;
- Today Agenda can quick-add a Todo planned for today, and its title can open
  the timetable;
- Dashboard window and widgets cannot be moved/resized.

#### Layout Edit Mode

Entered from Settings.

While active:

- Dashboard temporarily behaves as a foreground editable window;
- GridStack move/resize is enabled;
- whole Dashboard move/resize is enabled;
- widget show/hide may be changed;
- normal Todo interaction is disabled to avoid drag conflicts;
- a small `Save / Cancel` toolbar is visible.

In Layout Edit, the normal title/mode, network-status, and `Open Settings`
controls temporarily give way to a dedicated edit bar in the same shell-bar
area. The edit bar uses a stable primary row for the edit label/instructions
and `Save / Cancel`, plus a separate row for widget visibility controls. The
visibility row wraps when space is tight and must not show a horizontal
scrollbar. It must not overlap the Dashboard grid viewport. The blank edit-bar
area is a window drag region; because the shell is hosted in QWebEngine, its
pointer press may request a native caption drag through DashboardBridge. All
buttons, inputs, and visibility labels are excluded from dragging. After Save
or Cancel, the normal title/mode/status/Settings shell-bar content is restored.

Entering Layout Edit records the previous daily mode (`Locked` or `Interaction`).

Save persists the current Profile. Cancel restores the exact pre-edit snapshot. **Both Save and Cancel exit Layout Edit and restore the recorded previous daily mode.** If the application itself later restarts after having last recorded Layout Edit, startup still restores Interaction as specified below.

### 5.4 Mode startup behavior

First-ever launch:

- Dashboard is visible;
- mode is Interaction;
- Settings opens automatically once.

Later launches:

- Dashboard is always visible;
- last Profile is restored;
- last daily mode is restored;
- if the last recorded mode was Layout Edit, restore Interaction instead.

No global hotkey is required in V1.

---

## 6. System Tray

Tray behavior is intentionally minimal.

Left click:

- open/focus Settings.

Right-click menu:

- Show/Hide Dashboard;
- switch Locked/Interaction mode;
- Open Settings;
- Exit DeskBoard.

Do not put Profile switching, Layout Edit, manual refresh, or finance controls in the tray menu.

Closing Settings does not exit DeskBoard. Exiting from tray or Settings exits the application.

Only one DeskBoard application instance may run.

If a second launch is attempted, the existing instance should be focused/open Settings and the second process should exit.

---

## 7. Built-In Widget Types

V1 widget keys are exactly:

```text
weather
todo
today_agenda
gold
fx
china_indices
us_indices
finance_overview
```

A Profile may contain at most one instance of each widget type.

Financial widgets may coexist and may repeat the same underlying financial item visually. They share the same provider/cache data and must not trigger duplicate requests.

---

## 8. Grid Layout and Widget Adaptation

Dashboard uses a fixed **48-column GridStack topology**. The vertical axis uses
the same fine-grained layout units with a runtime cell height derived from the
board width and clamped to 20–32 CSS pixels. The topology is fixed, while the
number of occupied rows remains unbounded and the Dashboard viewport scrolls
when needed.

A Profile stores each widget's:

- visible/hidden state;
- `x`;
- `y`;
- `w`;
- `h`;
- widget-specific display configuration.

When the outer Dashboard window changes size:

- cell pixel dimensions change;
- widget topology and grid coordinates do not responsive-reflow.

Widget content may adapt to actual pixel size using `ResizeObserver` or equivalent.

Do not predefine final per-widget minimum sizes before the UI prototype/readability pass. The initial implementation may use conservative technical minimums solely to prevent zero/invalid geometry; final readability minimums are established by UI acceptance.
The same rule applies to the **overall Dashboard minimum width/height**: use only conservative technical bounds until the visual/readability gate establishes the final minimum.

Generic `compact / normal / expanded` state is not persisted. It is derived from actual pixel size.

---

## 9. Profiles

### 9.1 Purpose

A Profile is a **visual/spatial Dashboard configuration**, not a user account or data set.

### 9.2 Profile saves

A Profile saves:

- Dashboard window position;
- Dashboard window size;
- widget positions;
- widget sizes;
- widget visible/hidden state;
- theme;
- panel/background opacity;
- widget display modes/configuration, such as weather expanded mode.

### 9.3 Profile does not save

Profile does not save:

- Todo records;
- semester/course data;
- weather city list;
- primary weather city;
- financial item selection/order;
- timetable scheme and period-axis configuration;
- provider cache;
- network status.

Those are global.

### 9.4 Profile limits and management

- One built-in `Default` Profile exists.
- Built-in Default cannot be deleted.
- Up to **8 user Profiles** may exist in addition to Default.
- Profile management exists only in Settings.

Required actions:

- switch Profile;
- save current Profile;
- save as a new Profile;
- rename;
- delete;
- restore Default layout.

When a user Profile named `1` (also accepted as `方案1`) exists, startup
refreshes the built-in Default's Dashboard layout from that Profile. This
copies the window geometry and widget visibility, positions, sizes, and display
configuration only; Default's own theme, font, and opacity remain unchanged.
The source Profile remains editable, and Default's built-in protection, Save As
behavior, selection, and deletion rules do not change.

If editing the built-in Default layout, changes must be saved as a user Profile rather than overwriting the built-in template. In Layout Edit, pressing Save while Default is active opens a small native **Save As Profile** name prompt; confirming creates/switches to the new user Profile and exits Layout Edit, while dismissing that prompt leaves the user in Layout Edit so they may Save again or use the normal Cancel action.

If the currently active user Profile is deleted from Settings, DeskBoard switches to the built-in Default Profile.

When the eight-user-Profile limit is reached, creating another Profile is rejected with a normal user-facing message.

---

## 10. Themes, Typography, and Visual Style

V1 includes a curated set of Dashboard themes. The initial catalog contains:

- Mist Blue / 雾蓝晨光
- Mint Breeze / 薄荷清风
- Almond Sand / 杏仁暖沙
- Lavender Cloud / 淡紫暮云
- Ocean Night / 深海夜航
- Graphite Night / 石墨夜色
- Rose Dusk / 玫瑰暮色
- High Contrast / 高对比度
- Terra Signal / 大地信号
- Frontier Foundry / 边境铸造
- Astral Transit / 星际航线
- Coastal Tide / 海岸潮汐

Theme is stored per Profile.

The Dashboard font is also stored per Profile. Font choices use installed system
fonts with fallbacks; V1 does not download or bundle font files. The initial
choices are System UI, Microsoft YaHei, Noto Sans, Source Han Sans, and Source
Han Serif. A missing font must fall back without breaking the layout.

The four additional themes are original token-based visual directions. They use
project-authored colors and interface language only; the application does not
bundle third-party logos, screenshots, character art, or other external assets.

Visual direction:

- minimal flat panel;
- transparent outer Dashboard window;
- theme-appropriate semi-transparent widget regions;
- clear opaque text/icons;
- subtle separators/spacing;
- subtle outer rounding;
- almost no shadow;
- no acrylic/mica blur;
- no continuous decorative animation.

Light and dark themes must use the same semantic color roles for headings,
secondary text, controls, focus, status, and finance direction. Color must not
be the only indication of state; text, symbols, or shape differences remain
available. The high-contrast theme prioritizes readable borders and focus rings
over decorative subtlety.

Priority:

```text
clean > readable > fancy
```

Financial direction convention:

- red = up;
- green = down;
- explicit `+` / `-` text.

Gold may use the current theme accent as its primary highlight.

Frontend assets must be bundled locally. No runtime CDN.

---

## 11. Todo Domain

### 11.1 Product boundary

Todo is a lightweight personal list, not a project-management system.

Todo has:

- content;
- optional Deadline;
- optional planned date/time;
- completion state;
- manual display order.

Todo does not have:

- priority;
- tags;
- subtasks;
- recurrence;
- reminders;
- notifications;
- attachments;
- projects.

### 11.2 Persistence semantics

Recommended logical fields:

```text
id
content
deadline_date?
deadline_time?
planned_date?
planned_start_time?
planned_end_time?
completed_at?
display_order
created_at
updated_at
```

`completed_at IS NULL` means incomplete; otherwise complete.

### 11.3 Deadline semantics

Deadline answers: **when must this be completed by?**

Legal combinations:

- date + time → exact Deadline;
- date only → complete by that day;
- time only → date defaults to today;
- neither → no Deadline.

When `deadline_date == today`, a Todo appears in Today Agenda even if its
`planned_date` is missing or another date. If its planned date is not today,
it appears as a date-only item because its planned time belongs to another
date; if its planned date is today, its planned point/range time keeps the
normal timed-item behavior. A deadline date alone never creates a weekly
timetable event.

An overdue incomplete Todo remains visible. V1 may apply only a subtle warning color to Deadline text; no notification or explicit alert is required.

### 11.4 Planned-time semantics

Planned time answers: **when do I intend to do this?**

Legal forms:

```text
date only
date + point time
date + start/end time range
```

If a planned time is entered without a date, date defaults to today.

A range must have `end > start`.

### 11.5 Main Todo widget

The main Todo widget displays:

- all incomplete Todos, regardless of future date;
- Todos completed today.

It does not show Todos completed before today.

Ordering is entirely manual.

- New Todo defaults to the top.
- Completing a Todo does not move it.
- Deadline does not auto-sort.
- Planned time does not auto-sort the Todo widget.

If the visible area is insufficient:

- the Todo content area is vertically scrollable in Interaction Mode;
- title/add controls remain fixed;
- Locked Mode is pointer-through and therefore not scrollable.

The Dashboard widget viewport is content-sized when all visible widgets fit, so
it does not reserve a scrollbar or a persistent empty grid tail. It becomes
vertically scrollable only when the visible layout extends beyond the available
window area. Hidden widgets do not contribute rows to the visible grid height.

### 11.6 Todo interaction

In Interaction Mode:

- `+` performs quick-add;
- quick-add asks only for content;
- Enter saves;
- new Todo appears at top;
- checkbox toggles complete/incomplete;
- drag reorders;
- right-click opens a compact context menu.

The Today Agenda `+` performs the same quick-add interaction but assigns the
new Todo to today's planned date. It has no planned time until edited in the
Todo editor.

Context menu:

- Edit details;
- Mark complete / Mark incomplete;
- Delete.

Detailed editing uses a native Qt Todo editor dialog.

Deleting requires confirmation.

Completed history is available in Settings with:

- view;
- restore to incomplete;
- permanent delete with confirmation.

No search/statistics/tagging is required.

### 11.7 Settings Todo lists

The native Settings Todo page provides two simple views:

- **Incomplete**: current unfinished Todos;
- **Completed history**: completed records.

Completed history supports view, restore to incomplete, and permanent delete. Permanent delete requires confirmation. V1 does not add Todo search, statistics, tags, projects, or a recycle bin.

### 11.8 Completed style

A Todo completed today remains in its current position.

Recommended visual treatment:

- pale/light green background;
- check mark;
- no strikethrough.

The same completed state is preserved when the Todo appears in Today Agenda or this week's timetable.

---

## 12. Semester and Course Domain

### 12.1 Semester

Multiple semesters may be stored. Exactly one may be active at a time, or none.

Semester fields:

```text
id
name
start_monday
total_weeks
timetable_scheme_id (nullable)
created_at
updated_at
```

`start_monday` must be a Monday.

Current teaching week is calculated from Windows local date and `start_monday`; it is never persisted.

No automatic semester switching is required.

### 12.2 Timetable schemes and period axes

Timetable period settings are reusable global schemes. Each semester may bind
to zero or one scheme through `timetable_scheme_id`; one scheme may be reused
by multiple semesters. The scheme is course/semester configuration, not Profile
visual state, so switching Profiles does not change the timetable axis.

Each scheme stores:

```text
id
name
axis_mode: custom_periods | uniform_day
period_count: 1..24
day_start: nullable HH:MM
day_end: nullable HH:MM
is_builtin
created_at
updated_at
```

`custom_periods` stores exactly `period_count` child rows in
`timetable_scheme_periods`:

```text
scheme_id
period_no: 1..period_count
start_time
end_time
```

Custom rows must have `start_time < end_time`, increasing period order, no
overlap, and no duplicate period numbers. Gaps such as lunch breaks are
allowed. A partial, duplicate, out-of-range, overlapping, or otherwise invalid
set is not active, and DeskBoard must not invent school times.

`uniform_day` is the explicit option for a timetable that does not use school
period times. It stores no child period rows and uses `day_start` / `day_end`
as a continuous visible range. The default range is `00:00` to `24:00`; the
user may choose another range. `period_count` only controls the number of
equal visual guide bands in this mode and does not create artificial school
period semantics or labels. Course blocks are still positioned by their real
start/end times.

On a fresh installation, DeskBoard seeds exactly one built-in editable sample
scheme named `UIBE`, with eight custom period rows, and one active sample
semester named `样例` bound to it. This is starter data for the first-run
experience, not a claim that the displayed periods are an official timetable;
users may edit, rename, delete, or bind schemes through Settings. During
migration, a complete legacy `class_periods` set is copied unchanged into the
same built-in `UIBE` scheme and existing semesters are bound to it. An
incomplete legacy set still receives the sample UIBE defaults. An upgrade
normalizes the previous generated labels `方案1`, `Default方案`, and
`Legacy 8 periods` to `UIBE`, changes the legacy sample semester title `大三上`
to `样例`, and removes only an unbound `UIBE copy` whose axis data is identical
to UIBE. Other user-created schemes and semester titles remain untouched.
After migration, new reads and writes use the scheme tables; legacy
`class_periods` is migration input only.

Courses are not forced to align to period boundaries in any axis mode.

### 12.3 Recurring course

Recurring-course fields:

```text
id
semester_id
name
weekday: 1..7
start_time
end_time
start_week
end_week
classroom?
created_at
updated_at
```

Between `start_week` and `end_week`, the course repeats every week on that weekday.

There is no odd/even-week field.

Classroom is optional. If blank, it is not displayed.

### 12.4 Temporary cancellation

A cancellation identifies one recurring-course occurrence on one specific date.

Logical uniqueness:

```text
(recurring_course_id, occurrence_date)
```

Cancelling an occurrence simply prevents that occurrence from rendering.

### 12.5 One-off course

One-off course fields:

```text
id
semester_id
name
course_date
start_time
end_time
classroom?
created_at
updated_at
```

A reschedule is represented as:

```text
cancel original recurring occurrence
+
add one-off course
```

No special reschedule relationship model is required.

When the current date is outside the active semester's normal teaching-week range:

- recurring courses are not generated;
- the timetable week label is blank;
- one-off courses belonging to the active semester may still render when their explicit date matches the requested day/week.

Course/semester editing, cancellation, and one-off creation are performed in Settings, not directly on the Dashboard.

---

## 13. Today Agenda

`today_agenda` is a **derived view**, not a persistent event table.

It combines:

```text
CourseService
+
TodoService
→ AgendaService
```

Todo eligibility for Today Agenda is the union of `planned_date == today`
and `deadline_date == today`; if both dates match, the Todo appears only once.

### 13.1 Unified Dashboard list

The Dashboard renders timed and date-only agenda items in one `今日事项` list;
there are no separate timed/date-only sections. Timed items retain their
semantic ordering before date-only items, and an item's start/range time is
shown inline after its title. Date-only items show no time suffix.

The service-level distinctions below remain for ordering, conflict detection,
and timetable semantics; they are not separate Dashboard lists.

### 13.2 Timed items

Include:

- today's actual course occurrences;
- today's Todos with planned point time;
- today's Todos with planned time range.

Sort by planned/course start time.

Do not hide or grey an item merely because its time has already passed. All of today's past and future items remain visible for the day.

### 13.3 Date-only items

A Todo whose `planned_date == today` but has no planned time, or whose
`deadline_date == today` while its planned date is missing/another date,
appears **after all timed items** in a date-only/Today Items section.

Multiple date-only Todos follow their Todo manual order.

A Todo with no planned date/time and no deadline due today does not appear in
Today Agenda.

### 13.4 Interaction

Today Agenda rows are view-only; the widget also provides a quick-add action.

- individual rows are not editable;
- individual Todos are not completed here;
- course rows are not editable here;
- the `+` action creates a Todo planned for today without a planned time;
- clicking the widget title in Interaction Mode opens the weekly timetable overlay.

---

## 14. Weekly Timetable Overlay

The timetable is a large temporary overlay inside the single Dashboard Web page. It does not create a second QWebEngineView.

It is view-only.

### 14.1 Week scope

- current Windows-local calendar week only;
- fixed Monday–Sunday seven columns;
- no previous/next week navigation.

If current date is inside the active semester's teaching range, the upper-left area displays:

```text
第 N 周
```

If not, the week-label area is blank.

### 14.2 Header modes

Settings provides one of:

- weekday only;
- weekday + date;
- date only.

### 14.3 Vertical axis

The active semester's bound timetable scheme determines the vertical axis.
Vertical positioning always uses real continuous clock time.

- `custom_periods`: the visible range is the first configured period start
  through the last configured period end; the left side may display the saved
  period labels `1..N` as reference lines.
- `uniform_day`: the visible range is the saved `day_start` through
  `day_end`; equal guide bands use `period_count` only as a visual grid and do
  not imply school-period labels.

Course/Todo data outside the selected scheme's visible range is not rendered
on the timetable. If the active semester has no scheme, or its scheme is not
valid, the overlay must not invent vertical bounds. It shows a compact
configuration-required empty state directing the user to Settings. Today
Agenda remains usable because it does not depend on timetable scheme bounds.

### 14.4 Course blocks

Course blocks use actual `start_time` / `end_time`.

They are not snapped to major-period cells.

### 14.5 Todo blocks

Only Todos with a planned time appear in the weekly timetable.

- planned point time → thin/small marker at the exact vertical time;
- planned time range → normal-height block;
- date-only Todo → does not appear.

Only Todos whose planned date lies in the current week and whose time lies inside the timetable visible range are rendered.

### 14.6 Past-event rendering

Past timetable events remain rendered normally for the current week. Do not automatically hide or grey a course/Todo solely because its time has already passed.

### 14.7 Course/Todo conflicts

Conflicts are allowed.

When a Todo overlaps a course:

- course receives visual priority;
- Todo remains visible in a secondary/narrow style;
- apply a light overlap indication;
- do not block save;
- do not auto-reschedule.

### 14.8 Timetable readability

The timetable uses responsive typography. Its title, day headers, axis labels,
course/Todo blocks, and metadata become larger when the overlay has sufficient
width, while compact widths fall back to smaller values to avoid clipping or
overlap. Dashboard widget typography is derived from the nearest live card or
widget container and scales smoothly within readable bounds. Finance name/value
pairs remain a two-column single-line heading at compact widths; only text that
actually exceeds its available track is right-elided or wrapped.

The native Settings Courses page keeps its semester, recurring-course,
one-off-course, and timetable-scheme collections at roughly six to seven
visible rows instead of expanding to fill the page. Collection items remain on
one line; overly long text is elided at the right and remains available in the
item tooltip.

---

## 15. Weather

### 15.1 Required data

Weather normalized fields:

```text
city
condition
current_temperature
high
low
wind
```

V1 does not require:

- feels-like temperature;
- precipitation probability;
- air quality;
- lifestyle indices.

### 15.2 Cities

Settings maintains a global weather-city list with:

- city order;
- one primary city.

Primary city and city list are global, not Profile-specific.

Mainland-China city support is required.

The initial V1 mainland-city catalog and acceptance fixtures must include
Beijing and Shanghai as first-priority supported cities. Their order and which
one is primary remain user-configurable in Settings.

Overseas-city support is optional and must not block V1.

### 15.3 Widget behavior

Small/normal weather presentation prioritizes the primary city.

A Profile may store the weather widget's expanded display preference:

```text
single-city detail
or
multi-city summary
```

Actual content capacity is determined by widget pixel size.

For multi-city summary:

- follow global city order;
- show as many cities as fit;
- do not require internal scrolling.

---

## 16. Finance

### 16.1 Product boundary

Finance is a lightweight reference-information feature, not a trading terminal.

V1 may include verified built-in items in these categories:

- gold;
- common CNY FX reference rates;
- major A-share indices;
- major U.S. indices.

The actual catalog contains only items that pass the Phase 0 provider gate.

### 16.2 Finance catalog

The application maintains a code-owned `FinanceCatalog`.

A catalog item has a stable DeskBoard key such as:

```text
gold.au9999
fx.usd_cny
index.sse
index.csi300
index.sp500
```

The user cannot enter arbitrary codes.

Settings allows the user to:

- enable/disable validated catalog items;
- reorder enabled items globally.

Finance selection/order is global, not Profile-specific.

### 16.3 Candidate starting set

Candidate items may include, subject to successful provider validation:

Gold:

- Au99.99.

FX:

- USD/CNY;
- EUR/CNY;
- JPY/CNY;
- HKD/CNY.

A-share:

- Shanghai Composite;
- Shenzhen Component;
- ChiNext;
- CSI 300.

U.S.:

- Dow Jones;
- S&P 500;
- Nasdaq Composite.

A candidate is not guaranteed to ship merely because it appears in this list.

If no U.S.-index item passes the mainland-China source gate, the reserved `us_indices` widget type remains part of the code/layout vocabulary but is unavailable/hidden in the shipped V1 until a validated item exists.

### 16.4 Display

Finance is intentionally minimal:

```text
name
value
change percentage where meaningful
optional closed-market secondary label
```

Provider and cache FX values use a consistent DeskBoard convention of **1 unit of foreign currency = CNY**, even when an upstream source quotes per 100 units. Upstream quotation basis remains a Provider concern. Finance presentation uses a readable display basis derived from the normalized value: when CNY per 1 foreign unit is greater than or equal to 1, display `1 foreign unit = N CNY`; when it is greater than 0 and less than 1, display `1 CNY = N foreign units`, where `N` is the reciprocal. This inversion is presentation-only and must not change provider/cache values, stable keys, or source quotation metadata; invalid or non-positive values are unavailable rather than inverted.

No chart/sparkline/history.

Small widgets show only as many globally ordered enabled items as fit. Larger widgets reveal more items. Financial widgets do not require scrolling or pagination.

### 16.5 Market closure

When a market is reliably known to be closed, display the latest valid completed trading-session close and label:

```text
上一交易日收盘
```

If market state cannot be determined reliably, do not guess; show the value without the closed-market label.

Do not display last-success timestamps on the front Dashboard.

### 16.6 Direction colors

- positive/up: red;
- negative/down: green;
- include explicit sign.

---

## 17. Network Source Requirements

### 17.1 Mainland-China direct access

Every V1 network source must be usable on ordinary mainland-China internet access:

- no VPN requirement;
- no proxy requirement;
- no Clash requirement;
- no user API key/account requirement.

The application does not implement proxy settings.

A candidate source that cannot meet this gate is replaced or its catalog item is deferred.

U.S. indices do not weaken this rule.

### 17.2 Source preference

Selection priority:

1. official no-auth public source suitable for programmatic use;
2. stable official public page that can be parsed;
3. stable public JSON/HTTP source;
4. defer the item.

Do not implement runtime multi-source fallback chains in V1.

One logical item/group uses one selected provider implementation at a time.

### 17.3 Release review

Technical accessibility is not equivalent to redistribution permission.

Before public GitHub Release, review:

- current access method;
- attribution requirements;
- redistribution/commercial limitations;
- README source/disclaimer text.

Personal-use V1 development may proceed before this release review.

---

## 18. Refresh, Cache, and Status

### 18.1 Refresh interval

Automatic network refresh interval is fixed at **60 minutes**.

Dashboard visibility does not control network scheduling. Hiding the Dashboard window does **not** stop the 60-minute refresh service; only exiting DeskBoard stops it.

There is no trading-session-specific high-frequency schedule.

### 18.2 Startup behavior

On launch:

1. read local cache immediately;
2. render cached data if present;
3. check last successful age.

If cache is younger than 60 minutes:

- do not refetch merely because the app restarted;
- restore the last known green/red status.

If cache is 60 minutes old or older:

- render cache;
- refresh in background.

If no cache exists:

- render `暂无数据` as needed;
- refresh in background.

### 18.3 Refresh concurrency

Network I/O must not block the Qt GUI thread.

Preferred implementation:

```text
QThreadPool + QRunnable
```

V1 does not require an asyncio framework.

Each provider group may have at most one active refresh request.

If the same group is already refreshing, a duplicate manual request is ignored/disabled rather than queued.

### 18.4 Independent results

Provider groups/items fail independently.

Example:

```text
Weather: success
Gold: success
FX: failure
China indices: success
US indices: success
```

Result:

- successful new payloads are persisted;
- FX keeps its previous successful cache;
- global status becomes red.

Do not roll back a refresh round because one provider failed.

### 18.5 Failure behavior

A failed refresh:

- never overwrites the last successful payload;
- records attempt/error state separately;
- does not trigger short-interval automatic retries;
- waits for the next normal cycle or manual refresh.

Do not use a generic connectivity probe as a gate.

### 18.6 Manual refresh

Settings Data Status page provides:

- Refresh All;
- provider-group refresh actions.

Suggested groups:

```text
weather
gold
fx
china_indices
us_indices
```

Manual and automatic refresh use the same `DataRefreshService`.

The front Dashboard has **no refresh buttons or refresh menu actions**. Manual network refresh exists only in native Settings/Data Status.

### 18.7 Global status dot

Dashboard has exactly one global status dot in its upper-right area.

States:

```text
grey
green
red
```

Rules:

- grey → initial/unknown state or an applicable refresh is in progress;
- green → all currently enabled network data last refreshed successfully;
- red → at least one currently enabled network item/group last failed.

Only globally enabled data participates.

Profile visibility does not affect refreshing or status participation.

Local Todo/course data does not participate.

If startup skips refresh because cache is still fresh, reuse the persisted last-known status:

- prior success → green;
- prior failure → red;
- no known state → grey.

If no network items are currently enabled/configured, the global status is grey rather than vacuously green.

Front Dashboard does not show provider error text or last-update timestamps.

---

## 19. Settings Window

Settings is a normal native PySide6 window.

Recommended pages:

```text
General
Profiles
Weather
Finance
Todo
Courses
Data Status
About
```

### 19.1 Save behavior

Simple settings may apply immediately, for example:

- primary city;
- finance enable/disable;
- finance order;
- theme/opacity where edited through Profile UI;
- Dashboard font where edited through Profile UI;
- autostart.

When a Profile theme is selected for preview, the native Settings shell and
the currently visible Settings page must apply the same theme semantic palette
immediately as the Dashboard. Before a Profile/theme has been loaded, Settings
uses the safe initial Mist Blue/light fallback palette; it must not inherit
black surfaces from the Windows system night-mode setting. Preview is not
persistent until the user saves the Profile appearance. Cancelling or closing
without saving must leave the persisted Profile unchanged, and the next
Settings open must restore that persisted palette.

Structured object editing uses explicit Save/Cancel, for example:

- Todo detail editor;
- semester editor;
- recurring course editor;
- one-off course editor;
- Profile Save As/rename.

### 19.2 General

Includes at least:

- Dashboard show/hide;
- current Locked/Interaction mode;
- enter Layout Edit;
- autostart toggle;
- Settings language, default Simplified Chinese (`zh_CN`) with English
  (`en_US`) as an immediate switch;
- exit application.

The selected Settings language is an application setting stored in SQLite
`app_settings` under `ui.language`. It does not create a second JSON/YAML
configuration store. All native Settings page chrome and static controls must
be available in both languages; user-created names and provider data are not
translated.

### 19.3 Data Status

Displays detailed diagnostics unavailable on the front Dashboard:

- source/group name;
- last attempt;
- last successful update;
- success/failure;
- last user-readable error;
- data source attribution;
- Refresh All;
- per-group Refresh;
- Open Log Folder.

### 19.4 About

Displays at least:

- DeskBoard name;
- version;
- basic source/disclaimer references as appropriate.

No auto-update is required.

---

## 20. Time Semantics

All Todo/course/semester/day-rollover logic uses the **Windows system local time**.

DeskBoard does not maintain a separate application timezone.

Weather for another city does not change DeskBoard's Todo/course clock.

A lightweight Python-side day-rollover timer should refresh date-dependent local views near local midnight. Do not use a one-second JavaScript polling clock.

---

## 21. Database Model

V1 logical tables:

```text
schema_meta
app_settings

todos

semesters
timetable_schemes
timetable_scheme_periods
recurring_courses
course_cancellations
one_off_courses

profiles
profile_widgets

weather_cities

finance_preferences

network_cache
network_state
```

An upgrade migration may read the legacy `class_periods` table to preserve an
existing eight-period configuration, but steady-state repositories do not
read or write that table after the timetable-scheme migration.

### 21.1 Key constraints

- `course_cancellations(recurring_course_id, occurrence_date)` unique.
- `semesters.timetable_scheme_id` is nullable and references one global
  timetable scheme; deleting a scheme requires confirmation and unbinds the
  affected semesters into the configure-first state.
- `timetable_schemes.period_count` is constrained to 1..24.
- A `custom_periods` scheme has exactly one valid child row for each
  `period_no` from 1 through `period_count`; a `uniform_day` scheme has no
  child rows and requires `day_start < day_end`.
- `timetable_scheme_periods(scheme_id, period_no)` is unique and child rows
  cascade when their scheme is deleted.
- profile/widget key combination unique.
- user Profile count enforced by service: max 8 plus built-in Default.
- foreign keys enabled.
- deleting a semester requires user confirmation and cascades its course-domain child records.
- deleting a recurring course cascades its cancellation records.
- deleting a Profile cascades its widget layout rows.
- no generic soft-delete.

### 21.2 Cache/state separation

`network_cache` stores only last successful normalized payloads and success time.

`network_state` stores last attempt, last status, and last error summary.

A failure updates state without destroying cache.

The global dot color itself is derived and is not persisted as a color field.

---

## 22. QWebChannel Contract Principles

### 22.1 Initial state

Dashboard loads one coarse state snapshot rather than issuing many small getters.

Conceptual shape:

```json
{
  "app": {},
  "profile": {},
  "widgets": {},
  "todos": [],
  "agenda": {},
  "timetable": {"axis": {}},
  "weather": {},
  "finance": {},
  "networkStatus": {"state": "green"}
}
```

### 22.2 Commands: JS → Python

The final bridge should expose actions in this shape:

```text
requestInitialState()
addQuickTodo(content)
addTodayTodo(content)
toggleTodo(todo_id)
reorderTodos(ordered_ids)
openTodoEditor(todo_id)
requestDeleteTodo(todo_id)
requestWeeklyTimetable()
saveLayout(layout_state)
cancelLayoutEdit()
beginWindowDrag(screen_x, screen_y)
```

Exact Qt slot signatures may be adapted to QWebChannel serialization requirements, but semantic names/ownership must remain consistent.

### 22.3 Events: Python → JS

Expected event families:

```text
stateChanged
todosChanged
agendaChanged
weatherChanged
financeChanged
profileChanged
networkStatusChanged
modeChanged
```

Python is the source of truth.

JavaScript may keep a render-state mirror but must not become authoritative.

### 22.4 Presentation models

Do not expose raw SQLite rows or provider-specific fields directly to JavaScript.

Presentation layer converts domain state to ViewModels, including:

- Todo overdue boolean/text;
- completed boolean;
- Agenda ordering;
- finance formatted text/direction;
- active timetable scheme axis metadata and normalized guide references;
- timetable conflict metadata;
- normalized weather fields.

Pixel positioning remains a Web concern.

---

## 23. Logging and Diagnostics

Use lightweight rotating logs under `%LOCALAPPDATA%\DeskBoard\logs\`.

Record useful events such as:

- startup/shutdown problems;
- uncaught exceptions;
- provider/network/parse errors;
- SQLite errors;
- migration failures;
- QWebEngine page-load/console errors relevant to faults;
- packaging/runtime path failures.

Do not log high-frequency noise:

- mouse movement;
- render loops;
- polling heartbeats;
- normal widget redraws.

Settings provides `Open Log Folder`; V1 does not require an embedded log viewer.

---

## 24. Performance Requirements

Performance is experience-based, not an artificial hard RAM cap.

Requirements:

- idle CPU should be close to zero;
- short refresh spikes are acceptable;
- memory must not grow continuously during long-running use;
- total working memory under roughly **200 MB is preferred**, not a hard requirement;
- one QWebEngineView only;
- no high-frequency JS polling;
- no high-frequency network requests;
- the 48-column topology must remain a coordinate-resolution change only; do not create one DOM node or timer per grid cell;
- no continuous decorative animation;
- hide/show Dashboard without destroying/recreating QWebEngine.

Phase 0 must measure the real minimal WebEngine baseline before formal feature implementation.

---

## 25. Dependencies and Tooling

Expected core stack:

```text
Python 3.12.x
PySide6
requests
sqlite3 (stdlib)
dataclasses / standard Python models
GridStack bundled locally
pytest
ruff
PyInstaller onedir
Inno Setup
```

BeautifulSoup4 may be introduced only if a selected HTML source benefits from it.

Do not introduce, without a spec-level change:

```text
AKShare
pandas
NumPy
SQLAlchemy
Alembic
FastAPI
Flask
Django
aiohttp
custom asyncio-Qt integration
Pydantic
React
Vue
Electron
Node/Vite/Webpack build pipeline
Redis
Celery
APScheduler
```

Use local HTML/CSS/ES Modules. No Node runtime/build chain is required.

---

## 26. Packaging and Installation

V1 production path:

```text
PyInstaller onedir
→ Inno Setup
→ DeskBoard-Setup-x.x.x.exe
```

V1 provides the standard installer only.

Installed application must not require Python.

User data lives under `%LOCALAPPDATA%`, not Program Files.

Windows autostart:

- supported per current user;
- default OFF;
- no Windows service;
- no administrator requirement for normal operation.

Uninstall must not silently destroy personal data. The installer may explicitly offer user-data removal, or preserve it by default.

---

## 27. Testing and Acceptance

### 27.1 Automated tests

Core deterministic coverage must include:

- Todo completion/day visibility;
- Todo ordering;
- Deadline default-date semantics;
- planned date/point/range semantics;
- semester teaching-week calculation;
- recurring-course occurrence generation;
- cancellation;
- one-off course;
- Agenda merge/order/date-only section;
- timetable conflict metadata;
- Profile eight-user limit and built-in Default rules;
- repository transactions/cascades/migrations;
- provider parsers against saved fixtures;
- presentation/ViewModel transformation;
- cache/state separation;
- global status derivation.

Normal `pytest` must not require live internet.

### 27.2 Real Windows/manual acceptance

Mocks cannot prove:

- Z-order;
- true pointer pass-through;
- tray behavior;
- WebEngine rendering;
- GridStack drag/resize feel;
- PyInstaller WebEngine packaging;
- installer behavior;
- sleep/wake stability;
- long-running behavior;
- actual mainland-China direct provider reachability.

These require real acceptance evidence.

### 27.3 Phase 0 risk gate

Formal feature implementation must not begin until both risk tasks in the implementation plan establish:

1. viable Dashboard Z-order and pointer pass-through;
2. one QWebEngine + QWebChannel + GridStack viability;
3. acceptable minimal CPU/RAM behavior;
4. PyInstaller onedir viability for the minimal WebEngine spike;
5. native Settings window coexistence;
6. mainland-China-direct provider viability for mandatory V1 categories.

If a core assumption fails, update the specification/plan before feature implementation.

---

## 28. V1 Completion Definition

V1 is not complete while a core area is still placeholder-only.

Completion requires:

- Todo behavior matches this spec;
- semester/course behavior matches this spec;
- Today Agenda matches this spec;
- weekly timetable matches this spec;
- 48-column layout/Profile persistence is stable, including migration of the original 12-column Profile coordinates;
- up to 8 user Profiles plus built-in Default works;
- Weather uses validated mainland-China-direct data;
- every shipped Finance catalog item uses validated mainland-China-direct data;
- 60-minute refresh/cache fallback works;
- one global grey/green/red status works;
- Settings manages all V1 global configuration;
- Dashboard theme/font choices persist per Profile;
- native Settings defaults to Chinese and can switch to English;
- tray and startup behavior work;
- idle CPU is low and no obvious long-run memory leak exists;
- PyInstaller/Inno installer works on a clean Windows user environment;
- core automated tests pass;
- required manual acceptance evidence exists;
- major failures are diagnosable through logs/Settings status.

---

## 29. Public GitHub Release Gate

Public release occurs only after personal-use stability is proven.

Before release:

- re-check all network sources from mainland-China direct access;
- review upstream source/redistribution terms;
- document required attribution;
- add appropriate README disclaimer/source information;
- remove or replace any Provider/catalog item that is not acceptable for public distribution;
- verify a clean installer;
- verify no secrets/API keys are embedded.

DeskBoard must not claim trading-grade, real-time, investment-grade, or guaranteed financial data.
