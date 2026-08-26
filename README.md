# DeskBoard

DeskBoard 是一个面向 Windows 10/11 64 位的本地桌面信息看板。它把个人待办、课程安排、今日 Agenda、天气和少量金融参考信息放在桌面上，适合日常查看，不需要账号、云端服务或常驻浏览器。

> 当前状态：个人学习版，公开发布门禁尚未关闭。Task 28 的稳定性人工证据、数据源大陆直连复核和第三方数据条款复核完成前，请把当前构建当作测试版本，不要用于交易、风控或其他需要受监管数据质量的场景。

本项目仅用于非商业学习、研究与技术探讨，不提供交易、投资、天气安全或其他专业建议。“非商业”不等于自动获得第三方数据的访问、缓存、署名或再分发授权。

## 适合怎样使用

- 想在桌面上快速查看 Todo、今天的课程和计划事项。
- 想在不打开浏览器的情况下查看天气和少量参考行情。
- 想保存不同的桌面布局、主题和字体。
- 想在本机保存数据，不使用账号、云同步或远程数据库。

## 安装与第一次启动

### 安装版（推荐）

从项目发布页下载 `DeskBoard-Setup-x.y.z.exe` 后：

1. 双击安装包，按向导安装到当前用户目录；正常运行不需要管理员权限。
2. 从开始菜单或桌面快捷方式启动 DeskBoard。
3. 首次启动打开 Settings 后，先在 `Profiles` 选择主题、字体和布局。
4. 在 `Weather`、`Finance`、`Courses` 和 `Todo` 中完成自己的配置。
5. 回到 Dashboard，日常使用 `Interaction` 模式；只在调整布局时使用 `Layout Edit`。

仓库默认不提交 `build/`、`dist/` 等本地构建产物。维护者可按“从源码构建”章节生成同名安装包。

### 三种模式

| 模式 | 用途 |
| --- | --- |
| `Locked` | 只查看信息；看板进行鼠标穿透，避免误触 |
| `Interaction` | 添加、完成、编辑、删除 Todo，或查看可交互内容 |
| `Layout Edit` | 移动/缩放小组件，完成后选择保存或取消 |

日常使用建议保持 `Interaction` 或 `Locked`。切换模式、显示/隐藏看板、打开 Settings 和退出程序都可以通过系统托盘完成。

## 功能

| 功能 | 说明 |
| --- | --- |
| Todo | 添加、完成/取消完成、编辑、删除、排序和完成历史 |
| Today Agenda | 汇总当天课程与带计划时间的 Todo；只读展示 |
| Courses | 学期、重复课程、单次课程、取消记录和当前周课表 |
| Weather | 城市天气、当前温度、高低温和风力摘要 |
| Gold / FX | 黄金和人民币汇率参考值 |
| China / U.S. Indices | 主要 A 股和美国指数参考值 |
| Finance Overview | 按全局顺序汇总已启用的金融参考项目 |
| Profiles | 保存看板位置、大小、组件布局、显隐、主题、字体和显示偏好 |

Todo 的 Deadline 不会自动生成 Agenda 项目；只有计划日期/时间会进入当天 Agenda 或周课表。课程与 Todo 时间重叠时会保留两者，并显示冲突信息，不会自动改期。

## Settings 使用顺序

Settings 是低频配置入口，包含：

`General` · `Profiles` · `Weather` · `Finance` · `Todo` · `Courses` · `Data Status` · `About`

建议按下面顺序配置：

1. `General`：确认看板显示、透明度、语言和自启动选项。
2. `Profiles`：选择或创建 Profile，设置主题、字体和布局。
3. `Weather` / `Finance`：选择城市、金融项目和显示顺序。
4. `Courses`：创建学期，配置课表时间，再添加课程。
5. `Todo`：管理未完成事项和完成历史。
6. `Data Status`：查看最近成功时间、最近失败原因和手动刷新状态。

网络数据按固定 60 分钟周期刷新。启动时会优先显示已有成功缓存；刷新失败不会清除上一份成功数据。

## 数据、隐私和限制

- 个人 Todo、课程、Profile、缓存和日志保存在本机，不上传到 DeskBoard 服务器。
- SQLite 数据库：`%LOCALAPPDATA%\DeskBoard\data\deskboard.db`
- 运行日志：`%LOCALAPPDATA%\DeskBoard\logs\`
- 自启动默认关闭，只写入当前 Windows 用户的 Run 设置，不需要 Windows 服务。
- 卸载程序默认保留 `%LOCALAPPDATA%\DeskBoard` 中的个人数据；请按自己的需要清理。
- V1 不包含账号、云同步、通知提醒、自动更新、插件、数据导入导出、交易下单、金融历史曲线、新闻或多显示器架构。
- 当前只支持主显示器；天气和金融来源可能延迟、缺失或临时不可用。

天气、黄金、汇率和指数均只是参考信息。数据不承诺实时、交易级、投资级、完整、准确或连续可用，也不构成投资建议、交易依据或任何收益保证。当前来源、访问证据和条款风险见[数据源审计](docs/data-sources.md)。

## 从源码运行

开发环境要求：

- Windows 10/11 64 位；
- Python 3.12.x；
- 能正常启动 Qt WebEngine 的桌面会话。

在 PowerShell 中执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install pytest ruff pyinstaller

$env:PYTHONPATH = (Resolve-Path 'src').Path
.\.venv\Scripts\python.exe -m deskboard
```

如果只想验证入口而不打开完整交互界面，可以使用项目已有的测试和 smoke 脚本；正常测试不依赖实时网络。

## 从源码构建安装包

需要先安装 Inno Setup 6，并确保 `ISCC.exe` 在 PATH 或默认安装目录中。构建完整 onedir 和安装包：

```powershell
.\scripts\build.ps1 -Clean
```

只构建 PyInstaller onedir、不编译 Inno Setup：

```powershell
.\scripts\build.ps1 -Clean -SkipInstaller
```

输出位置：

- onedir：`dist\DeskBoard\DeskBoard.exe`
- 安装包：`dist\installer\DeskBoard-Setup-0.1.0.exe`

对已构建的 onedir 做隔离数据目录 smoke 检查：

```powershell
.\scripts\smoke_test.ps1 -DisableQtWebEngineSandbox
```

`build/` 和 `dist/` 只属于本机生成物，已在 `.gitignore` 中排除。正式发行前还必须在干净 Windows 用户环境中验证安装、启动、非管理员运行、自启动和卸载后的数据保留。

## 相关文档

- [产品规范](docs/spec.md)
- [实现计划](docs/implementation-plan.md)
- [界面设计说明](docs/ui-design.md)
- [数据源审计](docs/data-sources.md)
- [稳定性验收清单](docs/v1-stability-checklist.md)
- [发布检查清单](docs/release-checklist.md)
- [Task 30/31 Windows 人工验收步骤](docs/task30-manual-acceptance.md)、[Task 31 补充步骤](docs/task31-manual-acceptance.md)

## 维护者说明

DeskBoard 使用 PySide6、单个 QWebEngineView、本地 HTML/CSS/ES Modules、GridStack、SQLite 和 direct HTTP Provider。Python 是业务真相，Dashboard JavaScript 只负责渲染和轻量交互。项目不使用 AKShare、运行时 CDN、云服务、账号体系或自动更新。

在 Task 28 稳定性证据和 Task 29 数据源/条款门禁关闭前，仓库中的构建和文档只能视为公开准备材料，不应宣传为稳定 V1 或已清除来源授权的正式发行版。
