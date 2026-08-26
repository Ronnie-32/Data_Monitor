# DeskBoard V1 发布检查清单

本清单对应 Task 29、`docs/spec.md` §17.3/§26/§28/§29，以及
`docs/quality/test-matrix.md` 的 `MAN-REL-01..06`、`REV-SCOPE-01`、`REV-SCOPE-08`。

## 当前状态

| 字段 | 记录 |
| --- | --- |
| 审计日期 | 2026-08-25 |
| 版本 | `0.1.0`（`pyproject.toml`、`installer/deskboard.iss`） |
| 发布状态 | `NOT_RELEASED` / `AWAITING_MANUAL_ACCEPTANCE` |
| Task 28 前置 | 未关闭；见 [稳定性验收清单](v1-stability-checklist.md) |
| 当前安装器 | `dist/installer/DeskBoard-Setup-0.1.0.exe` 已成功编译；用户已确认下载安装/卸载无问题，Task 28 其余稳定性证据仍按清单单独记录 |
| 外部副作用 | 源代码仓库可在用户明确授权后 push；本清单不把源码 push 视为正式 Release，也不自动创建 GitHub Release 或上传安装包 |

`NOT_RELEASED` 是正式数据产品发布的硬停止状态。它不阻止在保守免责声明下公开学习向源代码，但不能把当前仓库或安装器称为已完成正式发行版本。

## 门禁结果

| ID | 门禁 | 当前结果 | 证据/下一步 |
| --- | --- | --- | --- |
| `MAN-REL-01` | Task 28 个人稳定性已接受 | `OPEN` | Task 28 仍缺 CPU/RAM、长时、睡眠/唤醒、边界和最终安装版证据；先完成 [v1-stability-checklist.md](v1-stability-checklist.md) |
| `MAN-REL-02` | 所有来源在大陆直连条件下复核 | `AWAITING_MANUAL_ACCEPTANCE` | Task 1 有 2026-08-20 历史 PASS；本轮无代理探测受本机 Schannel `SEC_E_NO_CREDENTIALS` 阻断，不能计为当前 PASS；详见 [data-sources.md](data-sources.md) |
| `MAN-REL-03` | 署名与条款复核 | `OPEN` | Weather/CFETS 明确存在授权边界；SGE/Tencent 的当前端点公开许可仍未确认 |
| `MAN-REL-04` | 不可接受来源已替换/删除/延期 | `OPEN` | 在许可或替代来源完成前，Weather/地点目录/Gold/FX/indices 不得标记为公开发布清除 |
| `MAN-REL-05` | 无 secrets、API key、私有数据和开发机绝对路径 | `PASS_STATIC` | 见本清单“静态复核”；发布前仍需对最终 release tree 重跑 |
| `MAN-REL-06` | README/About 没有过度数据声明 | `PASS_STATIC` | README 已明确未发布、非实时/非投资建议和来源限制；About/安装包最终复核仍待执行 |
| `REV-SCOPE-01` | 未加入 V1 排除项 | `PASS_STATIC` | 本任务只改文档；不新增 Provider、代理配置、API key、云服务、自动更新或 portable build |
| `REV-SCOPE-08` | 没有自动更新检查器 | `PASS_STATIC` | About、运行时和 installer 未加入 auto-update；发布前继续搜索最终树 |

## 文档交付物

- [x] README 说明当前功能边界、安装/源码运行、Settings/Profile/Todo/course 工作流、数据目录、日志位置和数据免责声明。
- [x] README 链接到来源审计、稳定性清单和发布清单。
- [x] [docs/data-sources.md](data-sources.md) 逐项记录 Weather、地点目录、Gold、FX、A-share indices、U.S. indices 的端点、访问证据、条款和处理动作。
- [x] 本清单记录 `MAN-REL-01..06`、范围审查、停止条件和最终证据字段。
- [ ] Task 28 人工证据归档并接受。
- [ ] 所有来源取得适用于公开发布的条款/书面授权，或完成代码级替换/延期。

## 安装、启动和日常使用核对

在干净的 Windows 10/11 x64 用户环境中使用最终安装器；不要把开发机上的源码运行结果当作安装版证据。

- [ ] 安装到当前用户目录，不需要管理员权限。
- [ ] 启动后 Dashboard、托盘和 Settings 可用，且只创建一个 Dashboard `QWebEngineView`。
- [ ] 首次启动只自动打开一次 Settings；日常启动恢复可见性、模式和 active Profile。
- [ ] Locked、Interaction、Layout Edit 的行为符合 README/spec；普通应用窗口的 Z-order、真正指针穿透和托盘行为需要截图/短记录。
- [ ] Settings 的 Profiles、Weather、Finance、Todo、Courses、Data Status、About 页面可用；关闭 Settings 不退出 DeskBoard。
- [ ] Todo 快速添加、完成/取消、详情编辑、删除确认、排序和完成历史可用。
- [ ] 课程、今日 Agenda、教学周和课表在 Windows 本地日期下可用。
- [ ] `%LOCALAPPDATA%\DeskBoard\data\deskboard.db` 和 `logs\` 正常创建，卸载不静默删除个人数据。
- [ ] 自启动默认 OFF；打开/关闭只影响当前用户且不需要 Windows 服务。

## 来源与许可核对

按 [data-sources.md](data-sources.md) 逐项完成，不得用“网页能打开”替代授权结论：

1. 在关闭 VPN、系统代理、Clash 的普通中国大陆网络中运行来源检查；记录日期、端点和原始输出摘要。
2. 逐项打开官方来源的版权/服务/数据许可页面，记录允许的请求、缓存、存储、公开展示和再分发范围。
3. 对没有明确公开许可的 Weather、Weather 地点目录、SGE、CFETS、Tencent 数据，取得书面确认，或从代码和发布包中删除/延期对应功能。
4. 只在来源清除后更新 README/About 的来源和署名文本；不得写“实时”“交易级”“投资级”“保证准确”等描述。

建议的人工技术复核命令（在干净的临时 checkout 或专门的证据环境中执行；不要把 live 响应自动提交到仓库）：

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -match '(?i)proxy' } |
  Select-Object Name,Value
netsh winhttp show proxy
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --record
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --offline
```

## Secrets、路径和范围静态复核

发布前对最终 release tree 重跑以下检查；下面的模式是筛查器，不是安全审计替代品：

```powershell
Get-ChildItem -File -Recurse -Include *.py,*.ps1,*.iss,*.spec,*.toml,*.md,*.html,*.js,*.css |
  Select-String -Pattern '(?i)(api[_-]?key|secret|password|token\s*=|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|C:\\Users\\|E:\\)' |
  Where-Object { $_.Path -notmatch '(?i)(README_files|__pycache__|dist|build)' }
```

Expected result: no embedded credential, private local data, or developer-machine absolute path. A documented command example such as `%LOCALAPPDATA%\DeskBoard` or `.venv` is not a secret; review every match manually.

Static scope checks must also confirm:

- no `QSettings`/JSON/YAML/TOML application config store;
- no WorkerW, localhost server, CDN, proxy/VPN/Clash configuration, API-key/account flow;
- no AKShare, auto-update, portable ZIP, notification, cloud/sync, finance chart/history/news or arbitrary security-code feature;
- no new background service or high-frequency polling introduced by documentation work.

## Build and release evidence

- [x] `pyproject.toml` and installer metadata currently agree on `0.1.0`.
- [x] PyInstaller onedir and Inno Setup compilation have historical Task 27 evidence.
- [ ] Rebuild the final onedir and installer from the exact release commit.
- [ ] Start the installed build from a clean user environment; retain exit/startup/log evidence.
- [ ] Verify install, ordinary non-admin operation, Settings, single instance, autostart, data directory and uninstall data retention.
- [ ] Run final automated verification; distinguish environment failures from product passes.
- [ ] Review the final Git tree and package contents; remove private/generated files that are not release assets.
- [ ] Only after every required checkbox is closed, create a formal GitHub Release, upload an installer, or claim a cleared data product. A source-only push may proceed only with explicit user authorization and conservative source/data disclaimers.

## Stop conditions

Stop and keep `NOT_RELEASED` if any of the following occurs:

- Task 28 remains unaccepted.
- A mandatory source cannot be reached from the required mainland-direct environment.
- A source's terms prohibit or do not clearly permit the intended public use, and no written permission or replacement exists.
- The final tree contains a secret, private local data, developer-only absolute path, or prohibited V1 feature.
- The installed build or required Windows acceptance fails.

### Final sign-off record

```text
Task: 29
Version: <version>
Commit: <exact release commit>
Task 28 accepted by: <name/date/evidence>
Source access evidence: <path/date>
Source terms/permissions: <path/date>
Installer evidence: <path/date>
Automated verification: <commands/results>
MAN-REL-01..06: <PASS/FAIL/AWAITING_MANUAL_ACCEPTANCE per case>
Scope review: <PASS/FAIL and reviewer/date>
External release authorization: <explicit user authorization or NOT AUTHORIZED>
Final decision: <RELEASED / NOT_RELEASED>
```
