# DeskBoard Agent Instructions

## 1. Authority and Project Goal

DeskBoard is a **Windows local desktop information dashboard** for personal daily use. V1 prioritizes stable daily use, clean/flexible UI, low idle CPU, maintainable architecture, and later GitHub publication after personal-use stability is proven.

Document authority:

- `docs/spec.md` — product requirements, user-visible behavior, domain semantics.
- `docs/implementation-plan.md` — task order, task scope, interfaces, acceptance gates.
- `AGENTS.md` — agent execution behavior, architecture guardrails, safety limits, anti-runaway rules.
- `docs/quality/requirements-traceability.md` and `docs/quality/test-matrix.md` — **supporting navigation/verification references only**; they never override the three authoritative documents above.
- Existing code is never authoritative over these documents.

Conflict handling:

- Code vs spec → spec wins.
- Plan vs spec → **STOP and report the mismatch** before implementation.
- User-requested product changes that conflict with spec are spec-change requests; do not silently bypass the spec in code.
- If the three project documents disagree, stop at the conflict rather than guessing or reconciling it in code.

### What to read for one implementation task

Do not reload all project documentation by default.

1. Read this `AGENTS.md` if not already supplied.
2. Identify the **single current numbered task** in `docs/implementation-plan.md`.
3. Read that task and its acceptance criteria.
4. Read only the relevant sections of `docs/spec.md`.
5. When useful, search the quality references by current task number or requirement/test ID; do not read them end-to-end by default.
6. Read only direct interfaces, source files, tests, and configuration needed for that task.
7. Broaden context only when evidence or an explicit subsystem boundary requires it.

Do not repeatedly re-read the full spec, plan, traceability matrix, or test matrix within one task.

---

## 2. Execution Budget and Anti-Runaway Rules

These rules override generic workflows that would otherwise continue automatically through multiple project tasks.

### One numbered task per session

- Execute **exactly one numbered implementation-plan task** per agent session unless the user explicitly authorizes a larger batch.
- Do not begin the next numbered task automatically.
- “Continue the project” is not permission to execute the entire remaining plan.
- After the current task reaches a terminal state, report it and **STOP**.
- Recover future progress from repository/git/test state; never replay completed work merely because context was compacted.

### Skill policy

For implementation work:

1. Use `test-driven-development` for deterministic feature logic, bug fixes, parsers, and behavior changes where applicable.
2. A deliberately failing TDD red test is **expected** and does not trigger debugging by itself.
3. For an **unexpected** bug, test failure, build/package/integration failure, or surprising behavior, use `systematic-debugging` before making further fixes.
4. Before claiming a task complete/fixed/passing, use `verification-before-completion` and fresh verification evidence.
5. Use `executing-plans` only if useful for the **current numbered task**, never as permission to continue through the whole project plan.
6. Do not start subagent-driven development, parallel agents, or other autonomous agents unless the user explicitly authorizes them for the current task.

### Failure circuit breaker

For one underlying blocker/root problem:

- reproduce and gather evidence before fixing;
- do not guess repeatedly;
- after root-cause investigation, attempt at most **3 materially different fixes**;
- cosmetic variations of the same approach do not reset the count;
- after 3 failed materially different fixes, **STOP** — no Fix #4 without user authorization.

When tripped, report: blocker, reproduction, evidence/root-cause hypothesis, the three attempts and results, and the smallest next investigation/decision.

### No-progress circuit breaker

**STOP and report `BLOCKED`** if 3 consecutive diagnostic iterations produce all three of the following:

- no new material evidence;
- no meaningful repository/configuration change;
- no improvement in test/build/acceptance state.

One diagnostic iteration means one bounded evidence-gathering action or one small hypothesis test followed by evaluation of its result. Do not continue by merely re-reading, re-running unchanged commands, reformulating the same hypothesis, or searching the same area with different wording.

### Task-complexity escalation gate

**STOP** if the current task materially expands beyond the implementation plan, for example:

- an unplanned subsystem becomes necessary;
- a second independent architectural blocker appears;
- a schema/interface redesign is required;
- a local task becomes a cross-cutting refactor;
- a new major dependency/framework/runtime is required;
- completing the task would change an approved V1 product boundary.

Do not silently enlarge the task.

### Command/output discipline

Prefer targeted commands:

```text
pytest tests/unit/services/test_todo_service.py -q
rg "TodoService" src tests
git diff -- src/deskboard/services/todo_service.py tests/unit/services/test_todo_service.py
git status --short
bounded head/tail/log ranges
```

Avoid by default:

```text
full-repository pytest -vv during diagnosis
recursive repository dumps
full large-log dumps
re-reading every project file after each edit
```

Rules:

- targeted tests first; broader suites only at the task verification gate;
- never recursively inspect `.venv`, `node_modules`, `dist`, `build`, installer output, caches, generated QtWebEngine assets, or large logs unless evidence specifically requires it;
- prefer `rg`, scoped `git diff`, bounded ranges, and focused test paths;
- do not rerun the same failing command unless code/config/evidence materially changed or a rerun is needed to prove reproducibility;
- if output is unexpectedly huge, stop/narrow the command rather than ingesting the whole output.
- do not wait for hours/days, repeatedly poll, or keep an agent session alive merely to satisfy long-running manual acceptance; run bounded smoke checks, write exact manual steps, return `AWAITING_MANUAL_ACCEPTANCE`, and let the user provide later evidence.

### Context and scope discipline

- Keep context limited to the current task, relevant spec, direct interfaces, implementation files, tests, and evidence.
- Use repository files, tests, commits/diffs, and task definitions as durable state.
- After compaction, recover from current task + `git status` + scoped `git diff` + relevant `git log` + current tests.
- Do not load unrelated historical logs/transcripts/generated artifacts “for completeness.”
- Do not add out-of-task features or unrelated refactors.
- Do not introduce a major dependency/framework/service/runtime merely for convenience.

---

## 3. Required Task-End States

Every implementation session ends in exactly one state.

### VERIFIED COMPLETE

Use only when all automated checks and all acceptance checks available in the current environment have passed.

```text
Task: <number/name>
Status: COMPLETE
Changed: <scoped files>
Verification: <fresh commands and concrete pass results>
Known issues: <none or explicitly bounded items>
Next: <next task number only; do not start it>
```

### AWAITING MANUAL ACCEPTANCE

Use when implementation and available automated checks pass, but required real-Windows/manual acceptance cannot be truthfully performed in the current environment.

```text
Task: <number/name>
Status: AWAITING_MANUAL_ACCEPTANCE
Changed: <scoped files>
Automated verification: <fresh commands and concrete pass results>
Manual acceptance required: <exact steps and expected result>
Known issues: <none or explicitly bounded items>
Next: <same task remains open until acceptance>
```

Do not call the task COMPLETE until required manual acceptance exists.

### BLOCKED

```text
Task: <number/name>
Status: BLOCKED
Blocker: <specific root problem>
Evidence: <reproduction/error evidence>
Attempts: <bounded list, max 3 materially different fixes>
Recommendation: <smallest next investigation/decision>
```

Never substitute “mostly done”, “should work”, or “probably fixed”.

---

## 4. V1 Architecture and Product Guardrails

Detailed behavior belongs in `docs/spec.md`. The following are non-negotiable red lines.

### Platform and runtime

- Windows 10/11 64-bit only.
- Python 3.12.x development baseline.
- Personal-use stability before public release.
- Main Dashboard: PySide6 + **one** `QWebEngineView` + local HTML/CSS/ES Modules + bundled GridStack + QWebChannel.
- Settings/admin: native PySide6 Widgets; no second QWebEngineView.
- SQLite is the only persistent database.
- Network providers use lightweight direct HTTP; **AKShare is not V1**.
- Runtime frontend assets are local; no CDN and no localhost HTTP server.
- PyInstaller **onedir** + Inno Setup is the V1 packaging path.

### V1 exclusions

Do not add without an approved spec change:

- cloud/accounts/sync;
- notifications/reminders;
- auto-update or portable build;
- plugin/custom-widget system;
- data import/export or automatic DB backup;
- multi-monitor architecture or edge auto-hide;
- WorkerW/desktop-icon embedding;
- arbitrary security-code entry, finance charts/history/news.

### Widget boundary

V1 widget types are exactly:

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

At most one instance of each widget type per Profile.

### Dependency direction

```text
UI
 ↓
Application Services
 ↓
Repositories / Providers
 ↓
SQLite / External HTTP
```

Allowed:

```text
Dashboard JS → QWebChannel Bridge → TodoService → TodoRepository → SQLite
SettingsPage → CourseService → CourseRepository → SQLite
DataRefreshService → Provider → normalized result → CacheRepository
AgendaService → TodoService + CourseService
```

Forbidden:

```text
Dashboard JS → SQLite
Provider → UI
Provider → SQLite
Repository → SettingsWindow
QWebChannel Bridge → raw SQL
Widget → external HTTP
```

Python is the source of truth. JavaScript holds only render-state mirrors. Do not expose raw SQLite rows or third-party provider fields to JS, and do not poll Python from JS.

---

## 5. Data-Source and Refresh Guardrails

### Mainland-China direct access

Every V1 Weather/Gold/FX/China-index/US-index source must be validated on ordinary mainland-China internet access:

- no VPN;
- no proxy/Clash dependency;
- no required end-user API key or account.

A failing source must be replaced or the catalog item deferred; do not add proxy configuration as the workaround. US indices do not weaken this rule.

### Refresh/cache

- Automatic network refresh is fixed at **60 minutes**.
- Cached successful data renders immediately when available.
- Fresh cache is not refetched merely because the app restarted.
- Network I/O never blocks the Qt GUI thread; prefer lightweight `QThreadPool + QRunnable`.
- Failed refresh never destroys the last successful payload.
- Success payload and attempt/error state remain separate.
- No short-interval auto-retry loop and no generic connectivity-probe gate.
- One provider group has at most one active request; no refresh queue in V1.
- Globally enabled network items refresh regardless of Profile visibility.
- The Dashboard has **one global** network-status indicator, not per-widget dots.

---

## 6. Desktop, Layout, Profile, and Persistence Guardrails

Desktop layer model:

```text
ordinary application windows
            ↑
         DeskBoard
            ↑
       Windows desktop
```

- No WorkerW/behind-icons integration.
- Dashboard is frameless, no normal taskbar button/close button, transparent outer window, primary display only in V1.
- Locked Mode: true Windows pointer pass-through, view-only.
- Interaction Mode: content interaction, no GridStack editing.
- Layout Edit Mode: foreground layout/window editing; normal Todo interaction disabled.
- Dashboard topology uses a fixed **12-column GridStack**; outer-window resize must not responsive-reflow widget topology.
- Profile stores visual/spatial state only, not Todo/Course/city/finance selections/cache.
- Profile management is in Settings only.

Persistent paths:

```text
%LOCALAPPDATA%\DeskBoard\data\deskboard.db
%LOCALAPPDATA%\DeskBoard\logs\
```

- SQLite foreign keys ON.
- Explicit lightweight schema-version migrations.
- DeskBoard-owned persistent user configuration lives in SQLite; do not add QSettings/JSON/YAML/TOML as a second application config store. Windows registry entries used only for OS integration such as autostart are exempt.
- No automatic DB backups in V1.
- Lightweight rotating logs; no render/mouse/heartbeat noise.

---

## 7. Performance and Dependency Guardrails

Performance target:

- idle CPU close to zero;
- short refresh spikes acceptable;
- no continuous memory growth;
- roughly <200 MB total working memory is preferred, not a hard acceptance limit;
- one QWebEngineView only;
- no high-frequency network calls, JS polling, or continuous decorative animation;
- hide/show does not destroy/recreate QWebEngine.

Expected core dependencies:

- PySide6
- requests
- bundled GridStack
- pytest
- ruff
- PyInstaller

BeautifulSoup4 may be added only when a selected HTML provider genuinely benefits from it.

Do not add without spec-level justification:

```text
AKShare, pandas, NumPy, SQLAlchemy, Alembic,
FastAPI/Flask/Django, aiohttp/custom asyncio-Qt integration,
Pydantic, React/Vue, Node/Vite/Webpack runtime/build pipeline,
Redis, Celery, APScheduler, Electron
```

---

## 8. Testing, Phase 0, Packaging, and Git Gates

### Testing

Use focused automated coverage for deterministic areas defined by the spec/plan, including Todo, teaching-week/Course occurrence rules, Agenda/timetable metadata, Profile rules, repositories/migrations, provider parsers with saved fixtures, presentation/ViewModels, and cache/status behavior.

- Normal `pytest` must not depend on live internet.
- Fresh verification is required before completion claims.
- Real Windows/manual acceptance is required where mocks cannot prove behavior: Z-order, pointer pass-through, tray, QWebEngine/GridStack behavior, packaging/install/uninstall, sleep/wake/long-run behavior, and mainland direct provider reachability.
- If the environment cannot perform required real acceptance, use `AWAITING_MANUAL_ACCEPTANCE`.

### Phase 0 stop gate

Tasks 0 and 1 in `docs/implementation-plan.md` together form the Phase 0 risk gate. Formal feature work must not begin until they validate:

1. Windows bottommost + pointer pass-through;
2. one QWebEngine + QWebChannel + GridStack integration;
3. actual CPU/RAM baseline;
4. PyInstaller onedir packaging of the WebEngine spike;
5. native Settings window coexisting with Dashboard;
6. viable mainland-China-direct sources for mandatory V1 categories.

If a core Phase 0 assumption fails, stop and update the affected spec/plan before feature implementation.

### Packaging/release

```text
PyInstaller onedir
→ Inno Setup
→ DeskBoard-Setup-x.x.x.exe
```

V1 has no automatic update or portable ZIP. Public GitHub release occurs only after personal-use stability and a data-source release gate (access, upstream terms, attribution, redistribution/commercial limitations, disclaimer).

Never claim trading-grade, real-time, investment-grade, or guaranteed financial data.

### Git side effects

Local `git status/diff/log` and task-level local checkpoints are allowed when consistent with repository workflow.

Never automatically push, merge, publish, create a release, or modify a shared remote branch without explicit user request.

---

## 9. Completion Discipline

For the current numbered task:

1. identify exact scope and acceptance criteria;
2. read only relevant spec/direct interfaces;
3. write the focused failing test first where applicable;
4. confirm the **expected** red failure;
5. implement the minimum change;
6. run focused tests;
7. on unexpected failure, perform systematic root-cause debugging;
8. enforce the 3-fix and no-progress breakers;
9. stop if task scope/architecture materially expands;
10. run broader verification only at the task gate;
11. perform required manual acceptance where possible;
12. use fresh evidence before any completion claim;
13. checkpoint at an appropriate functional boundary;
14. report exactly one terminal state: `COMPLETE`, `AWAITING_MANUAL_ACCEPTANCE`, or `BLOCKED`;
15. **STOP**.

Do not start the next implementation-plan task in the same session unless the user explicitly authorizes it.
