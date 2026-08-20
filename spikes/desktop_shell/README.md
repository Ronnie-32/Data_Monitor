# Task 0 — Windows / QWebEngine / Packaging Risk Spike

This is a throwaway shell proof. It is deliberately not production code and
does not create DeskBoard services, repositories, settings persistence, tray
integration, or business widgets.

## What it proves

- `main.py` creates one `QWebEngineView` in a frameless, transparent, small
  panel and a separate native Qt Widgets `SettingsWindow`.
- The Dashboard starts in `interaction`; Settings can switch to `locked`.
  Locked applies Qt `WindowTransparentForInput` and the Windows
  `WS_EX_TRANSPARENT` candidate style. This is a candidate only until the
  manual Windows pointer test below passes.
- The Dashboard uses `WindowStaysOnBottomHint` as the candidate layer model:
  ordinary app windows above DeskBoard above the desktop. The exact Windows
  Z-order behavior is intentionally recorded as manual evidence, not claimed
  by this source code.
- `index.html` loads all UI scripts from disk: `qwebchannel.js`, local
  GridStack 12.3.3, and local CSS. It has three fake widgets at fixed
  12-column coordinates `(0,0,4,2)`, `(4,0,4,2)`, and `(8,0,4,2)`.
- JavaScript sends `web-channel-ready` and button commands to Python. Python
  returns an acknowledgement and emits `pythonValueChanged`, which JavaScript
  displays. The Python `currentValue()` call demonstrates the reverse value
  path after channel setup.
- Settings has explicit Show/Hide controls. The same WebEngine view is kept
  alive; visibility events and bridge events are written to a small evidence
  file in `%TEMP%` when the process exits.

## Local assets and licensing

The vendored UI assets are intentionally small and pinned:

| Asset | Version/source | License evidence |
| --- | --- | --- |
| `vendor/gridstack/gridstack-all.js` and `gridstack.min.css` | GridStack `12.3.3`, obtained from its npm release tarball | `vendor/gridstack/LICENSE` and `gridstack-all.js.LICENSE.txt` |
| `qwebchannel.js` | Qt WebChannel client script, npm convenience package `qwebchannel@6.2.0` | LGPL header is retained at the top of the file; package provenance is recorded in `vendor/qwebchannel/README.md` |

The `qwebchannel` npm package is community-maintained. Before public GitHub
release, re-check Qt upstream provenance and redistribution/attribution terms
as required by the project release gate.

## Bounded evidence from the Codex Windows environment

Recorded on 2026-08-20 on Windows 11 64-bit (build 22631), Python 3.12.7,
PySide6 6.8.3, and PyInstaller 6.21.0:

- source-mode and packaged `--smoke` runs both exited `0`;
- the packaged local page reported `page_loaded: true`, received the
  JavaScript command `web-channel-ready`, and emitted Python-originated values;
- the packaged page URL was an onedir-local `file:///.../_internal/index.html`;
- one Dashboard `QWebEngineView` and one QtWebEngine child process were
  observed; Settings remained a native Qt Widgets window;
- the onedir build includes the local HTML, QWebChannel script, GridStack
  JavaScript/CSS/license files, and QtWebEngine runtime resources;
- the Conda Python baseline required explicitly collecting `ffi.dll`,
  `libcrypto-3-x64.dll`, and `liblzma.dll`; after adding them, the packaged
  smoke completed successfully.

Ten-second idle samples of the packaged process tree:

| State | Working set | CPU seconds during 10 s | Normalized CPU | Processes |
| --- | ---: | ---: | ---: | --- |
| Interaction | 281.3 MiB | 0.000 | 0.000% | app + 1 QtWebEngine child |
| Locked | 279.4 MiB | 0.000 | 0.000% | app + 1 QtWebEngine child |
| Dashboard hidden | 253.7 MiB | 0.000 | 0.000% | app + 1 QtWebEngine child |

Memory is above the preferred roughly 200 MiB baseline but is not a hard
failure under the specification. Idle CPU met the close-to-zero target in
these bounded samples. These short samples do not prove long-run memory trend.

Codex-launched QtWebEngine processes run inside an additional host sandbox.
In this environment the page failed to load with the default Chromium sandbox
but loaded with `QTWEBENGINE_CHROMIUM_FLAGS=--no-sandbox`; `--disable-gpu`
alone did not help. This environment limitation is not baked into the spike.
A normal user-launched Windows run without either flag remains required before
Task 0 can close.

## Run from a real Windows desktop

```powershell
.venv\Scripts\python.exe spikes\desktop_shell\main.py
```

The Settings window opens once at startup. Choose `Locked (pass-through)` to
test pointer pass-through, or `Interaction` to click the local Dashboard
button. Stop the process with Ctrl+C in the launching console after testing;
the evidence helper
prints a JSON object containing the path to:

```text
%TEMP%\deskboard-task0-spike-evidence.json
```

For a bounded launch smoke (still requiring a GUI-capable Windows session):

```powershell
.venv\Scripts\python.exe spikes\desktop_shell\main.py --smoke
```

For bounded performance observations, `--auto-exit-seconds=N` accepts 1–300
seconds. Add `--start-locked` for Locked mode or `--start-hidden` to hide the
Dashboard after startup while keeping the native Settings window and process
alive. These switches support repeatable measurement; they do not replace the
manual pointer and Z-order checks.

On this Codex Windows VM, Chromium's GPU virtualization and sandbox are not
available, so the reproducible environment-only probe is:

```powershell
$env:QTWEBENGINE_CHROMIUM_FLAGS = "--disable-gpu --no-sandbox"
.venv\Scripts\python.exe spikes\desktop_shell\main.py --smoke
```

That workaround is not a product recommendation. A normal Windows 10/11
desktop run must be tested without it; if a real user machine needs the flag,
record that as a packaging/security blocker instead of silently baking it
into the app.

## Manual acceptance record (must be completed by the user)

These checks cannot be truthfully replaced by a mocked or headless test.

| ID | Procedure | Expected result | Observation / date |
| --- | --- | --- | --- |
| MAN-WIN-01 | Launch source and packaged spike on Windows 10/11 64-bit | Both launch; packaged output does not require the development Python process | **Pending packaged run** |
| MAN-WIN-02 | Inspect the Dashboard and its local page/QWebChannel behavior | Exactly one Dashboard `QWebEngineView` exists; local GridStack page and QWebChannel render | **Pending real Windows run** |
| MAN-WIN-03 | Open/focus Settings while Dashboard exists | Settings is native Qt Widgets, coexists correctly, and creates no second WebEngine | **Pending real Windows run** |
| MAN-WIN-04 | Open Notepad and Explorer over the panel; click desktop; use Win+D and restore | Ordinary application windows cover the Dashboard; Dashboard remains above the desktop | **Pending real Windows run** |
| MAN-WIN-05 | Inspect taskbar and Dashboard chrome | Frameless transparent panel has no close button and no normal taskbar entry | **Pending real Windows run** |
| MAN-WIN-07 | Switch Locked and click/drag a desktop item beneath the Dashboard; then switch Interaction | Locked passes input through; Interaction receives intended Dashboard input | **Pending real Windows run** |
| MAN-PERF-01 | With three widgets, observe Task Manager while Locked and Interaction are idle | CPU is close to zero; no continuous growth | **Pending measured baseline** |
| MAN-PERF-02 | Record total process-tree working set, hide/show behavior, and WebEngine child count | Measurement is recorded; one QWebEngineView remains and hiding does not recreate it | **Pending measured baseline** |
| MAN-PACK-01 | Build and launch the onedir output below | Local page, GridStack, QWebChannel, and native Settings all work without Python installed | **Pending real packaged run** |

Task 0 Step 3 additionally requires resizing the outer Dashboard several times:
the three widgets must retain `(x, y, w, h)` while only their pixel dimensions
change. Record that observation with the Windows evidence above.

If any Z-order or true pointer pass-through requirement fails, stop the Phase 0
gate and update the spec/plan before production feature work.

## PyInstaller onedir proof

The spec explicitly uses `COLLECT`, so this is an onedir build:

```powershell
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm spikes\desktop_shell\spike.spec
dist\deskboard-task0-spike\deskboard-task0-spike.exe --smoke
```

The spec includes the HTML, local QWebChannel script, and the GridStack JS,
CSS, and license directory. PyInstaller's Qt hooks collect the WebEngine
runtime/process/resources.

## Static smoke checks

From the repository root:

```powershell
.venv\Scripts\python.exe -m py_compile spikes\desktop_shell\main.py
Select-String -Path spikes\desktop_shell\index.html -Pattern 'https?://|GridStack.init|column: 12|qwebchannel.js'
Select-String -Path spikes\desktop_shell\main.py -Pattern 'QWebEngineView|QWebChannel|WindowTransparentForInput|WindowStaysOnBottomHint'
```

The first command checks Python syntax. The latter two are bounded source
checks; they do not replace WebEngine rendering, Z-order, pointer, packaging,
or performance acceptance.
