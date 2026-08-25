# DeskBoard V1 稳定性与性能验收清单

本清单对应 Task 28、`docs/spec.md` §24/§27/§28，以及
`docs/quality/test-matrix.md` 中的 `MAN-PERF-01..07`、
`MAN-STAB-01..08`、`REV-DONE-01`、`REV-PERF-01`、`REV-SCOPE-01`。

Task 28 是稳定性验收门，不是新增功能阶段。除非出现可复现的具体缺陷，
不修改生产代码；如果修复需要实质性实现或调试，应另开经用户授权的任务。

## 1. 验收记录信息

| 字段 | 记录 |
| --- | --- |
| 验收日期 | 2026-08-25 |
| 当前分支/提交 | `main` / `e2ecd79` |
| Windows 版本/架构 | Windows 11 10.0.22631，x64（PyInstaller build log） |
| Python 版本 | `3.12.7` |
| PySide6 / PyInstaller | `6.8.3` / `6.21.0` |
| 验收构建 | `dist\DeskBoard` onedir；`DeskBoard-Setup-0.1.0.exe` 已存在 |
| 数据目录 | `%LOCALAPPDATA%\DeskBoard\data\` |
| 日志目录 | `%LOCALAPPDATA%\DeskBoard\logs\` |
| 总体状态 | `AWAITING_MANUAL_ACCEPTANCE`，直到长时/Windows 人工证据补齐 |

状态只能填写 `PASS`、`FAIL` 或 `AWAITING_MANUAL_ACCEPTANCE`。未实际观察到的场景
不得填写 `PASS`。

## 2. 运行前冻结与自动化门禁

### 2.1 范围冻结

- [x] Task 27 的安装/启动/卸载/数据保留/自启动/权限证据已由用户确认并归档。
- [ ] 没有为 Task 28 增加 V1 widget、Provider、依赖、配置存储或后台服务。
- [ ] 当前工作区中的无关用户改动、`README*` 和 `TEMP_HANDOFF.md` 未被清理或混入任务提交。
- [x] `git diff --check` 通过；只把本任务相关的清单/记录纳入 Task 28 变更。

### 2.2 自动化命令

在仓库根目录执行。正常 `pytest` 不应依赖 live internet。

```powershell
$env:PYTHONPATH=(Resolve-Path 'src').Path
$env:QTWEBENGINE_DISABLE_SANDBOX='1'
\.venv\Scripts\python.exe -m pytest -q
```

记录：

| 检查 | 命令/产物 | 结果 | 证据 |
| --- | --- | --- | --- |
| 完整 pytest | `python -m pytest -q` | `FAIL / ENVIRONMENT` | exit 1；`test_real_qwebchannel_invokes_layout_save_slot` 触发 Windows `0x80000003`；unit 运行另见下方 |
| 可复现确定性子集 | presenter/provider/startup/autostart/worker，排除 ACL 用例 | `PASS` | `56 passed in 1.27s` |
| Python 编译 | `\.venv\Scripts\python.exe -m compileall -q src tests` | `PASS` | `COMPILEALL_PASS` |
| JS 语法 | 对 10 个 `.js` 执行 `node --check` | `PASS` | `JS_FILES=10; NODE_CHECK_PASS` |
| Schema migration smoke | SQLite fresh DB → `migrate` | `PASS` | `schema_version=2` |
| 静态范围/性能复核 | `REV-SCOPE-01`、`REV-PERF-01`、`REV-DONE-01` | `AWAITING_MANUAL_ACCEPTANCE` | 非 vendor JS/CSS 无 polling/animation/fetch；daily Windows visibility guard 有 500ms Qt timer，需实机 CPU 证据 |
| 差异空白 | `git diff --check` | `PASS` | exit 0；仅有工作区换行提示 |
| Ruff | `.venv\Scripts\ruff.exe check src tests installer\deskboard.spec` | `BASELINE` | 3 个既有 import-order 问题，未在 Task 28 越界修复 |

### 2.3 生产构建与有界 smoke

构建只允许清理脚本声明的 `build\DeskBoard` 和 `dist\DeskBoard` 输出；不要用
递归删除仓库或其父目录的命令。

```powershell
.\scripts\build.ps1 -Clean -SkipInstaller
.\scripts\smoke_test.ps1 -DisableQtWebEngineSandbox
```

如果需要重建安装器，在已安装 Inno Setup 6 且确认目标路径后执行：

```powershell
.\scripts\build.ps1 -Clean
```

记录构建和 smoke 的 stdout/stderr、产物路径、退出码，以及 smoke 证据目录。
Smoke 只证明有界启动、SQLite/log 路径和本地 WebEngine/GridStack 资源存在，
不能替代安装器 GUI、QWebChannel、指针穿透、睡眠/唤醒或长时间使用验收。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| PyInstaller onedir | `PASS` | fresh `scripts\build.ps1 -Clean -SkipInstaller`；`dist\DeskBoard\DeskBoard.exe` |
| 本地 frontend/GridStack/WebEngine 资源 | `PASS` | build script 找到 `index.html`、`gridstack-all.js`；QtWebEngine hidden imports 已进入 spec |
| 隔离 `LOCALAPPDATA` 启动 | `FAIL / ENVIRONMENT` | `scripts\smoke_test.ps1 -DisableQtWebEngineSandbox -TimeoutSeconds 15`；`build\smoke\20260825-124724-19376\`，15 秒未退出 |
| Inno Setup installer（Task 27 产物） | `RECORDED` | `dist\installer\DeskBoard-Setup-0.1.0.exe`，127,031,669 bytes |

## 3. CPU/RAM 有界基线

基线应在正常 Windows 桌面会话记录。先关闭其他 DeskBoard 实例；若出现
`QLocalServerPrivate::addListener: Access denied`，记录为环境/已有实例问题，
不要删除 endpoint、批量杀进程或修改产品逻辑绕过。

### 3.1 采样方法

1. 启动最终 onedir/已安装构建，等待首屏和启动刷新完成。
2. 分别在 Locked idle、Interaction idle、Dashboard hidden 三种状态保持至少
   60 秒；每 10 秒记录 `DeskBoard`、`QtWebEngineProcess` 的 CPU 百分比、工作集
   （WS）和私有内存（PM）。
3. 在一次手动/自动刷新期间额外采样 60 秒，记录峰值与恢复到 idle 的时间。
4. CPU 以“采样期间是否持续非零/异常升高”判断；一次刷新造成的短峰值允许。
   内存以“是否持续单调增长”判断；约 200 MB 是偏好值而不是硬失败阈值。

可用 PowerShell 采样命令（按实际进程名调整）：

```powershell
Get-Process -Name DeskBoard,QtWebEngineProcess -ErrorAction SilentlyContinue |
  Select-Object Id,ProcessName,CPU,WorkingSet64,PrivateMemorySize64
```

### 3.2 基线记录

| 场景 | 采样窗口 | DeskBoard CPU/WS/PM | QtWebEngineProcess CPU/WS/PM | 结论 | 证据 |
| --- | --- | --- | --- | --- | --- |
| `MAN-PERF-01` Locked idle | 未能进入正常应用状态 | 未采样 | 未采样 | `AWAITING_MANUAL_ACCEPTANCE` | QLocalServer 环境门阻断 |
| `MAN-PERF-01` Interaction idle | 未能进入正常应用状态 | 未采样 | 未采样 | `AWAITING_MANUAL_ACCEPTANCE` | QLocalServer 环境门阻断 |
| `MAN-PERF-05` Dashboard hidden | 未能进入正常应用状态 | 未采样 | 未采样 | `AWAITING_MANUAL_ACCEPTANCE` | 需正常 GUI 会话 |
| `MAN-PERF-04` refresh spike | 未能进入正常应用状态 | 未采样 | 未采样 | `AWAITING_MANUAL_ACCEPTANCE` | 需正常 GUI 会话 |
| `MAN-PERF-02` final working set | 未能进入正常应用状态 | 未采样 | 未采样 | `AWAITING_MANUAL_ACCEPTANCE` | 不能以 smoke hang 进程代替 final app |
| `MAN-PERF-03/07` long-run trend | 未执行 | 未采样 | 未采样 | `AWAITING_MANUAL_ACCEPTANCE` | 用户个人使用证据 |

## 4. 稳定性与人工验收场景

每个场景都要记录开始时间、构建、操作、预期、实际、状态和证据路径。长时、
睡眠/唤醒、自然跨日和多日使用不在当前 agent 会话中等待；没有用户证据时
保持 `AWAITING_MANUAL_ACCEPTANCE`。

| ID | 操作 | 预期结果 | 状态/证据 |
| --- | --- | --- | --- |
| `MAN-PERF-01` | Locked idle，观察 60 秒 | CPU 接近零，仅有正常采样噪声 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-PERF-02` | 记录最终应用工作集/私有内存 | 记录实际值；约 200 MB 仅为偏好参考 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-PERF-03` | 正常个人使用数小时/数日并重复记录内存 | 无持续、无界内存增长 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-PERF-04` | 手动刷新或等待一次 60 分钟刷新 | 有界短峰值允许；窗口仍响应，结束后回到 idle | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-PERF-05` | 隐藏 Dashboard，跨一次刷新边界后再显示 | 刷新继续；同一 QWebEngineView 未销毁重建 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-PERF-06` | Locked/Interaction idle 观察 UI 与前端行为 | 无连续装饰动画、无高频 JS polling/网络轮询 | `PASS static / AWAITING_MANUAL_ACCEPTANCE CPU` |
| `MAN-PERF-07` | 反复显示/隐藏并观察进程列表 | 无进程倍增或明显资源泄漏 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-01` | 使用最终安装版进行约定的个人日常使用 | 无崩溃、阻塞、重大数据损坏 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-02` | 隐藏 Dashboard 跨 60 分钟刷新边界 | 网络调度不受可见性影响 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-03` | 在刷新前断网，刷新后恢复网络并再次刷新 | 保留旧缓存，失败状态可见，恢复后成功数据不损坏 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-04` | 运行跨本地午夜 | Completed-today、Agenda 和日期派生状态切到新日期 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-05` | 观察/模拟 Sunday→Monday 与教学周边界 | Agenda/Timetable 教学周状态正确更新 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-06` | Windows 睡眠后唤醒 | 应用可用；刷新/日期状态恢复；无重复 worker/进程 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-07` | 循环显示/隐藏、Locked/Interaction、Profile 切换、Layout Edit Save/Cancel | 无状态损坏或持续资源增长 | `AWAITING_MANUAL_ACCEPTANCE` |
| `MAN-STAB-08` | 制造代表性 Provider 失败，查看 Settings Data Status 与日志 | 保留缓存；错误可诊断；日志/状态有可读原因 | `AWAITING_MANUAL_ACCEPTANCE` |

### 4.1 关键人工操作细则

- **断网/恢复：** 记录刷新前最后成功时间和缓存内容；断网时等待一次刷新，
  确认旧数据仍在、全局状态转红；恢复网络后从 Data Status 手动刷新，确认状态
  和 payload 恢复。不要把短暂 DNS/代理问题误判成 Provider 代码修复证据。
- **缓存失败回退：** 使用已有成功缓存后诱发一个 Provider 失败；失败不能覆盖
  `network_cache`，Settings 应同时显示 last success、last attempt 和 readable error。
- **跨日/教学周：** 记录系统本地时间和活动学期；检查日期事项、已完成 Todo、
  Agenda、课表标题/教学周，不用 JavaScript 秒级轮询作为验收依据。
- **手动系统时间变更：** 仅在可恢复的测试环境执行，记录变更前后时间；确认
  日期派生状态重算，不要求网络 Provider 的远端时间跟随本机时间。
- **Profile/Layout：** 在至少两个 Profile 间切换；进入 Layout Edit 后分别执行
  Save 和 Cancel，确认几何/可见性语义正确，日常模式恢复且没有连续 SQLite 写入。
- **Settings：** 重复打开/关闭 Settings；确认关闭 Settings 不退出 DeskBoard，且
  仍只有一个 Dashboard QWebEngineView。

## 5. 失败报告格式

```text
Task: 28
Case: MAN-PERF-xx / MAN-STAB-xx / REV-xxxx
Build: <commit and installed/onedir path>
Environment: <Windows version, Python/PySide6 if relevant>
Start/end: <local timestamps>
Reproduction: <smallest exact steps>
Expected: <spec/test-matrix expectation>
Actual: <observed result and exact error>
Evidence: <screenshot/log/command output path>
Classification: PRODUCT_BUG | ENVIRONMENT | TEST_HARNESS | NOT_REPRODUCED
Next action: <bounded investigation or user decision>
```

同一根因最多尝试三种实质不同的修复；环境错误不得通过删除用户数据、批量杀进程、
放宽产品安全边界或引入代理配置来绕过。

## 6. Task 28 结果汇总

| 类别 | 已有证据 | 尚缺证据 | 当前结论 |
| --- | --- | --- | --- |
| 自动化/构建 smoke | onedir build、静态检查和 56-test 子集通过；完整 pytest/packaged smoke 受环境阻断 | 正常 Windows 会话重跑 full pytest/smoke | `AWAITING_MANUAL_ACCEPTANCE` |
| CPU/RAM bounded baseline | 未采样 | 正常 Windows 采样 | `AWAITING_MANUAL_ACCEPTANCE` |
| 长时/多日/睡眠/跨边界 | 无 | 用户个人使用证据 | `AWAITING_MANUAL_ACCEPTANCE` |
| `REV-PERF-01` / `REV-SCOPE-01` | 非 vendor 前端无高频 polling/animation/fetch；依赖与 scope 搜索无实际禁用项；daily guard 为 500ms Qt timer | 实机 CPU 与长时趋势确认 | `AWAITING_MANUAL_ACCEPTANCE` |
| `REV-DONE-01` | Task 27/28 及此前任务的自动化/构建证据已记录 | 全部 required manual evidence | `AWAITING_MANUAL_ACCEPTANCE` |

在本表所有必需人工证据齐全前，不得宣称 V1 已完成或进入 Task 29 公共发布门。
