# DeskBoard

DeskBoard 是一个面向 Windows 的本地桌面信息看板。它以轻量、低打扰的方式把待办、课程安排、今日 agenda、天气和少量经过验证的金融参考数据放在桌面上：看板位于 Windows 桌面之上、普通应用窗口之下，不需要账号、云端服务或常驻浏览器。

本文按 DeskBoard V1 的产品目标和当前实现编写，既面向日常使用者，也面向需要继续维护、构建和发布项目的开发者。

> 当前发布状态：**尚未公开发布**。Task 28 的个人稳定性与性能人工证据仍为
> `AWAITING_MANUAL_ACCEPTANCE`；Task 29 只整理发布材料和门禁记录，不代表已经获得公开发布批准。

## 设计目标

- Windows 10/11 64 位优先，使用 Windows 系统本地时间。
- 本地优先、无账号、无云同步，个人数据只保存在本机 SQLite 中。
- 看板常驻桌面但不遮挡普通应用，空闲时保持接近零 CPU 活动。
- Python 负责业务真相，前端只负责显示、布局和轻量交互。
- 所有网络数据都经过缓存、状态记录和来源验证；网络失败不破坏上一份成功数据。
- 先保证个人日常稳定使用，再进行公开 GitHub 发布和数据源条款复核。

## 功能

### 桌面看板与三种模式

DeskBoard 的主 Dashboard 是无边框、透明外壳的桌面面板，使用单个 `QWebEngineView` 加载本地页面。

| 模式 | 行为 |
|---|---|
| Locked | 只读，真正将鼠标事件穿透给桌面或下面的窗口；不能操作待办、滚动或编辑布局 |
| Interaction | 可以快速添加、完成、编辑、删除、排序待办；布局固定，不会误触拖动看板 |
| Layout Edit | 临时进入前台编辑状态，可移动/缩放看板和 GridStack 小组件，保存或取消后恢复原来的日常模式 |

看板只运行在主显示器上，不使用 WorkerW/桌面图标背后嵌入，也不强制铺满整个桌面。

### 内置小组件

V1 固定提供以下八类小组件，每个 Profile 中同一类型最多一个实例：

| 类型 | 作用 |
|---|---|
| `weather` | 展示主城市或多城市天气摘要，包括天气状况、当前温度、高低温和风力 |
| `todo` | 展示未完成待办以及今天完成的待办 |
| `today_agenda` | 合并今天的课程和带计划时间的待办，按时间生成只读 agenda |
| `gold` | 展示 Au99.99 等经过验证的黄金参考行情 |
| `fx` | 展示 USD/CNY、EUR/CNY、JPY/CNY、HKD/CNY 等常用人民币汇率参考值 |
| `china_indices` | 展示上证、深证成指、创业板、沪深 300 等主要 A 股指数 |
| `us_indices` | 展示道琼斯、标普 500、纳斯达克综合等经过来源门禁的美国指数 |
| `finance_overview` | 将启用的金融参考项目按全局顺序汇总展示 |

金融功能是轻量参考信息，不提供行情图表、历史曲线、新闻、交易、下单或任意代码输入。

### Todo

Todo 是轻量个人清单，不包含项目管理系统的复杂字段。

- 支持快速添加、勾选完成/取消完成、拖动手动排序和右键菜单。
- 支持 Deadline：日期、时间、日期+时间。
- 支持计划时间：仅日期、日期+点时间、日期+起止时间。
- 只有计划时间会进入 Today Agenda 或周课表，Deadline 本身不会把待办放入 agenda。
- 新待办默认放在顶部；完成、Deadline 和计划时间都不会改变 Todo 列表的手动顺序。
- 详情编辑使用原生 Qt 对话框，删除需要确认。
- Settings 中提供 Incomplete 和 Completed history 两个视图，可恢复或永久删除已完成记录。

Todo 不提供优先级、标签、子任务、重复任务、提醒、通知、附件或项目分组。

### 学期、课程、Agenda 与周课表

- 支持多个学期，但同一时间最多一个 active semester。
- 支持按周重复课程、单次课程和指定日期的临时取消。
- 当前教学周根据 Windows 本地日期和学期起始周一实时计算，不单独持久化。
- 支持全局八个大节的起止时间；未完成八节配置时，课表不会擅自猜测时间范围。
- Today Agenda 是由 `CourseService + TodoService` 派生出的只读视图，不建立通用 event 表。
- 周课表是单个 Dashboard 网页内的临时 overlay，固定显示当前自然周周一至周日，不创建第二个 WebEngine。
- 课程使用实际起止时间；课程与 Todo 冲突时允许重叠，课程获得视觉优先级，Todo 仍保持可见。

### Profile 与布局

Profile 保存 Dashboard 的视觉和空间状态：

- 看板位置和尺寸；
- 小组件位置、尺寸和显隐；
- 主题、透明度和小组件显示模式；
- 天气小组件的单城市/多城市显示偏好。

内置 `Default` Profile 不能删除，最多可创建 8 个用户 Profile。Todo、学期课程、天气城市、金融项目选择、缓存和网络状态都是全局数据，不会随 Profile 切换。

V1 提供四个浅色主题：

- 雾蓝晨光（Mist Blue）；
- 薄荷清风（Mint Breeze）；
- 杏仁暖沙（Almond Sand）；
- 淡紫暮云（Lavender Cloud）。

布局基于固定 48 列 GridStack 细网格，纵向 cell 高度保持在 20–32px。调整外层看板大小时，小组件拓扑不响应式重排，只改变像素显示尺寸；旧 12 列 Profile 会在迁移时按 4 倍坐标转换。

### 天气、金融数据与缓存

- 天气首要支持中国大陆城市，默认验收城市包括北京和上海。
- 数据源要求普通中国大陆网络可直连，不依赖 VPN、代理、Clash、API Key 或账号。
- 自动刷新间隔固定为 60 分钟，网络请求在 Qt GUI 线程之外执行。
- 启动时先显示缓存；缓存未过期时不会因为重启而强制重复请求。
- 每个 Provider 组独立成功或失败，失败时保留上一份成功 payload。
- Dashboard 只显示一个全局网络状态点：灰色表示未知/刷新中，绿色表示启用项全部成功，红色表示至少一项失败。
- 详细错误、最后尝试时间、最后成功时间、来源和手动刷新入口只放在 Settings 的 Data Status 页面。

金融数值使用中国市场习惯的方向颜色：上涨为红色、下跌为绿色，并显示明确的 `+`/`-` 符号。数据仅作信息参考，不代表实时、交易级、投资级或收益保证。

当前实现使用经过早期来源门禁的固定 Provider；公开发布前必须重新执行大陆直连检查，并完成每个来源的署名、缓存和再分发许可复核：

| 数据类别 | Provider 来源 |
|---|---|
| Weather | 中国天气网城市天气索引和正式逐日预报页 |
| Gold | 上海黄金交易所每日行情页 |
| FX | 中国外汇交易中心公开汇率接口 |
| A-share / U.S. indices | 腾讯公开批量行情接口 |

Provider 只使用已选定的单一来源，不在运行时拼接无界的多源 fallback。当前审计结论和待办见
[数据源审计](docs/data-sources.md)；在书面许可或替代来源完成前，不得将这些来源宣称为公开发布已清除。

### Settings、托盘和单实例

原生 PySide6 Settings 不创建第二个 `QWebEngineView`，包含以下页面：

```text
General / Profiles / Weather / Finance
Todo / Courses / Data Status / About
```

系统托盘提供：

- 显示/隐藏 Dashboard；
- 切换 Locked / Interaction；
- 打开 Settings；
- 退出 DeskBoard。

程序使用单实例保护。第二次启动不会创建第二个窗口，而是将已有实例的 Settings 窗口调到前台。Windows 自启动可在 Settings 中开启，默认关闭，不需要 Windows 服务或管理员权限。

## 使用方式

### 使用安装版

1. 运行 `DeskBoard-Setup-x.y.z.exe`。
2. 按安装向导完成安装；普通运行不需要管理员权限。
3. 启动 DeskBoard，Dashboard 会显示在主显示器桌面上，系统托盘图标同时出现；首次启动会自动打开一次 Settings。
4. 首次使用时在 Settings 中配置 Profile、天气城市、金融项目、学期、八个大节时间和课程。
5. 日常使用通过 Dashboard 和托盘切换模式；低频配置统一在 Settings 中完成。

卸载程序不会静默删除 `%LOCALAPPDATA%\DeskBoard` 下的个人数据。是否删除用户数据应由卸载流程明确提示。

### 从源码运行

开发环境要求：

- Windows 10/11 64 位；
- Python 3.12.x；
- Qt WebEngine 能正常启动的桌面会话。

在仓库根目录执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest ruff pyinstaller
```

运行开发版：

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
python -m deskboard
```

也可以使用已安装的命令行入口：

```powershell
deskboard
```

如果 PowerShell 禁止执行本地脚本，可只对当前用户放开虚拟环境激活脚本权限，或直接使用虚拟环境解释器：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
$env:PYTHONPATH = (Resolve-Path 'src').Path
.\.venv\Scripts\python.exe -m deskboard
```

### 日常操作建议

1. 首次启动先打开 Settings → General，确认 Dashboard 显示和当前模式。
2. 在 Settings → Profiles 选择或创建布局 Profile。
3. 在 Settings → Weather 设置城市顺序和主城市。
4. 在 Settings → Finance 启用并排序需要展示的参考项目。
5. 在 Settings → Courses 新建学期、配置八个大节、添加重复课程或单次课程。
6. 回到 Dashboard，在 Interaction 模式用 `+` 快速添加 Todo；需要完整字段时右键选择 Edit details。
7. 需要调整看板位置或小组件大小时进入 Layout Edit，完成后选择 Save 或 Cancel。
8. 网络异常时先查看 Settings → Data Status；已有缓存仍会继续显示。

## 数据与日志位置

DeskBoard 的运行数据统一保存于：

```text
%LOCALAPPDATA%\DeskBoard\
├─ data\
│  └─ deskboard.db
└─ logs\
   ├─ deskboard.log
   ├─ deskboard.log.1
   └─ deskboard.log.2
```

SQLite 开启外键约束，并通过 `schema_meta` 保存 schema 版本。数据库迁移使用显式、轻量、事务化的 migration；应用配置不另设 QSettings、JSON、YAML 或 TOML 存储。

日志使用有大小上限的 rotating handler，只记录启动、迁移、数据库、WebEngine、Provider 和刷新错误等诊断信息，不记录高频渲染或鼠标心跳噪声。

## 技术架构

DeskBoard 是模块化单体桌面应用，依赖方向固定为：

```text
Dashboard JS / Native Settings
             │
             ▼
       QWebChannel Bridge
             │
             ▼
      Application Services
          │          │
          ▼          ▼
     Repositories   Providers
          │          │
          ▼          ▼
        SQLite     Direct HTTP
```

核心边界如下：

- Dashboard JS 不访问 SQLite，不请求外部网络，也不承载业务真相。
- QWebChannel Bridge 只转发命令和事件，不写 SQL、不解析 Provider 响应。
- Service 层承载 Todo、课程、Agenda、Profile、刷新和状态规则。
- Repository 只负责 SQLite 持久化，并按表明确所有权。
- Provider 只负责请求、解析和归一化，不写数据库、不更新 UI。
- Python 生成 Dashboard 初始状态和 ViewModel；JavaScript 只保存渲染态镜像。
- Settings 复用同一组 Services，避免 Dashboard 和设置页出现两套业务规则。

主要运行时依赖：

```text
Python 3.12.x
PySide6 / Qt WebEngine / QWebChannel
requests
sqlite3、dataclasses 等 Python 标准库
本地打包的 GridStack
pytest / ruff
PyInstaller onedir / Inno Setup
```

项目不使用 AKShare、pandas、NumPy、ORM、Web 后端、Node/Vite 构建链、Electron、Redis、Celery 或运行时 CDN。

## 项目结构

当前仓库的主要目录职责如下：

```text
DeskBoard/
├─ docs/
│  ├─ spec.md                       # 产品行为和边界的权威说明
│  └─ implementation-plan.md        # 分阶段实现计划
├─ src/deskboard/
│  ├─ app/                          # 应用生命周期、模式、单实例
│  ├─ infrastructure/               # 路径、日志、时钟、后台任务、自启动
│  ├─ database/                     # SQLite 连接、schema、migrations
│  ├─ models/                       # Todo、课程、Profile、天气、金融模型
│  ├─ repositories/                 # SQLite 持久化边界
│  ├─ services/                     # 领域和应用服务
│  ├─ providers/                    # 天气、黄金、汇率、指数 Provider
│  ├─ presentation/                # Dashboard 状态和 ViewModel
│  └─ ui/
│     ├─ dashboard/                 # 唯一 QWebEngineView、Bridge、本地网页
│     ├─ settings/                  # 原生 Settings 页面
│     ├─ dialogs/                   # 原生编辑与确认对话框
│     └─ tray/                      # 系统托盘
├─ tests/
│  ├─ unit/                         # 领域、服务、仓储和解析器测试
│  ├─ integration/                  # Bridge、WebChannel、应用壳测试
│  └─ fixtures/providers/           # 离线 Provider 原始响应
├─ spikes/                          # Phase 0 风险验证，不是生产代码
├─ scripts/                         # 构建、冒烟和发布辅助脚本
├─ installer/                       # PyInstaller spec、Inno Setup 脚本
├─ pyproject.toml
└─ README.md
```

## 整个项目的构建过程

项目采用“先验证高风险假设，再实现领域功能，最后做真实 Windows 验收”的顺序。产品语义以 `docs/spec.md` 为准，任务顺序和验收门槛以 `docs/implementation-plan.md` 为准。

### 1. 先确定边界和架构

首先确定 V1 只做本地桌面看板，不引入账号、云同步、通知、插件、导入导出、金融交易、后台服务或多显示器架构。随后固定以下基础约束：

- PySide6 管理 Windows 外壳；
- 一个且只有一个生产 `QWebEngineView`；
- 本地 HTML/CSS/ES Modules + GridStack；
- 原生 PySide6 Settings；
- SQLite 是唯一应用持久化数据库；
- Direct HTTP Provider 负责外部数据；
- PyInstaller onedir + Inno Setup 是生产发布路线。

这一步的目的，是先冻结依赖方向和产品边界，避免在后续开发中把 Dashboard JS、Provider 或 Settings 变成新的业务中心。

### 2. Phase 0：风险门禁

正式业务功能开始前，先完成两个风险任务：

| 任务 | 先验证什么 | 产出 |
|---|---|---|
| Task 0 | Windows 桌面层级、鼠标穿透、单 QWebEngineView、QWebChannel、GridStack、原生 Settings、CPU/RAM 和 PyInstaller | `spikes/desktop_shell/`、Windows 人工验收记录、WebEngine onedir 冒烟包 |
| Task 1 | 天气、黄金、汇率、A 股和美股候选来源能否在普通中国大陆网络直连 | `spikes/providers/`、离线 fixture、来源与字段归一化记录 |

Task 0 解决“窗口壳是否可行”，Task 1 解决“数据源是否可用”。任何核心假设失败，都应先修订 spec/plan，再继续功能开发。

### 3. Phase 1：应用基础设施

对应 Task 2–5：

1. 建立 `src/deskboard` 可导入、可运行的 Python 包。
2. 建立 `LOCKED`、`INTERACTION`、`LAYOUT_EDIT` 三种合法模式。
3. 建立 `%LOCALAPPDATA%\DeskBoard\data`、`logs` 和数据库路径助手。
4. 加入低噪声 rotating 日志。
5. 创建 Dashboard、唯一 QWebEngineView、QWebChannel 和原生 Settings 外壳。
6. 实现系统托盘、单实例、第二次启动 handoff 和幂等退出。
7. 创建 SQLite schema、schema version、v001 migration、外键约束和 repository ownership。
8. 加入 Windows 本地时钟抽象，为日期和教学周规则提供可测试的时间边界。

这一阶段只解决“应用能稳定启动、退出、保存和诊断”，不把领域规则塞进窗口代码。

### 4. Phase 2：Todo

对应 Task 6–8：

1. 先为 Todo 的完成状态、排序、Deadline、计划日期/点时间/时间段和当天可见性写纯业务测试。
2. 实现 `Todo`/`TodoUpdate` 模型、`TodoRepository` 和 `TodoService`。
3. 实现 Todo Presenter，把 Python 领域对象转成 Dashboard ViewModel。
4. 通过 Bridge 支持快速添加、勾选、排序和 Interaction 模式右键菜单。
5. 使用原生 Qt 对话框实现详情编辑和删除确认。
6. 在 Settings 中加入未完成列表、完成历史、恢复和确认后永久删除。

Dashboard 和 Settings 始终复用同一个 TodoService，保证两处的完成、编辑和删除语义一致。

### 5. Phase 3：学期、课程、Agenda 和课表

对应 Task 9–12：

1. 实现学期、教学周、全局八节课时间、重复课程、取消记录和单次课程。
2. 用 Windows 本地日期生成指定日期/当前周的课程 occurrence。
3. 将课程 occurrence 与 Todo 的计划时间合并为 Today Agenda。
4. 生成 Python 拥有的 Agenda/Timetable ViewModel，前端只负责绘制。
5. 在单个 Dashboard Web 页面中显示当前周周一至周日课表 overlay。
6. 为课程/Todo 重叠提供冲突元数据，不阻止保存，也不自动改期。

Agenda 不做独立事件持久化，避免同一条信息在 Todo、课程和通用 event 表中重复存储。

### 6. Phase 4：Profile 和 GridStack 布局

对应 Task 13–14：

1. 实现内置 `Default` 和最多 8 个用户 Profile。
2. 明确 Profile 只保存位置、尺寸、显隐、主题、透明度和显示模式。
3. 实现 Layout Edit 的保存、取消、Default Save As、重命名、删除和恢复默认布局。
4. 固定 48 列 GridStack 拓扑，验证外层窗口尺寸变化不会导致布局重排。
5. 将 Layout Edit 与正常 Todo Interaction 解耦，避免拖动组件和拖动 Todo 相互冲突。

### 7. Phase 5：网络基础和天气

对应 Task 15–17：

1. 建立 `network_cache` 与 `network_state` 的分离模型。
2. 用后台 worker 执行网络请求，不阻塞 Qt GUI 线程。
3. 固定 60 分钟刷新周期，限制每个 Provider 组最多一个活动请求。
4. 启动时先渲染缓存，失败时保留最后成功 payload。
5. 接入通过来源门禁的天气 Provider，支持城市列表、主城市和多城市显示。
6. 在 Dashboard 只暴露一个全局状态点，在 Settings 暴露详细诊断和手动刷新。

### 8. Phase 6：金融参考数据

对应 Task 18–22：

1. 建立代码维护的 `FinanceCatalog`，用户只能选择已验证的固定项目。
2. 实现黄金、人民币汇率、A 股指数 Provider。
3. 对美股指数逐项执行中国大陆直连验证；不通过的项目明确延期或隐藏。
4. 将不同上游的报价单位归一化，例如汇率统一为“1 单位外币对应多少人民币”。
5. 实现 `gold`、`fx`、`china_indices`、`us_indices` 和 `finance_overview` Presenter/Widget。
6. 处理交易日关闭状态，只在能够可靠判断时显示“上一交易日收盘”。

金融 Provider 只请求、解析和归一化，不直接写 SQLite；缓存和状态由 NetworkRepository/DataRefreshService 负责。

### 9. Phase 7：视觉基线和 Settings

对应 Task 23–25：

1. 建立四套浅色主题和统一 CSS token。
2. 通过可读性门禁确定看板最小尺寸、文字层级、间距和透明度范围。
3. 完成 General、Profiles、Weather、Finance、Todo、Courses、Data Status、About 页面。
4. 将低频配置留在原生 Settings，将高频 Todo 操作保留在 Dashboard。
5. 验证前台只显示必要摘要，来源、错误、缓存时间和诊断信息放到后台页面。

### 10. Phase 8：运行时稳定性、打包和发布

对应 Task 26–29：

1. 加入启动恢复、日 rollover、窗口丢失恢复、睡眠/唤醒和 Windows 行为加固。
2. 生成 PyInstaller onedir，确保本地 HTML、QWebChannel、GridStack、Qt WebEngine 资源全部随包提供。
3. 在干净目录验证启动、单实例、Settings、数据目录、自启动和退出行为。
4. 使用 Inno Setup 生成标准安装程序，验证安装、升级式覆盖和卸载时的数据保护行为。
5. 运行完整自动化测试、lint、静态检查、构建冒烟和真实 Windows 手工验收。
6. 记录 CPU/RAM、长时间运行、网络失败恢复和缓存回退结果。
7. 发布前复核所有数据源的直连能力、署名、再分发限制、API Key/secret 泄漏和免责声明。

## 测试与质量检查

自动化测试不依赖实时互联网，Provider 使用保存的 fixture 重放。常用检查命令：

```powershell
# 全部自动化测试
.\.venv\Scripts\python.exe -m pytest -q

# 代码风格和导入检查
.\.venv\Scripts\python.exe -m ruff check src tests

# Python 字节码编译检查
.\.venv\Scripts\python.exe -m compileall -q src tests

# 补丁空白检查
git diff --check
```

Provider 离线解析检查：

```powershell
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --offline
```

只有在已确认 VPN、系统代理和 Clash 均关闭的普通中国大陆网络中，才执行实时来源记录：

```powershell
Remove-Item Env:HTTP_PROXY,Env:HTTPS_PROXY,Env:ALL_PROXY -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --record
```

自动化测试不能替代以下真实 Windows 验收：窗口 Z-order、真正鼠标穿透、托盘交互、WebEngine 渲染、GridStack 拖拽手感、PyInstaller WebEngine 打包、安装卸载、睡眠唤醒和长时间运行。

## 构建 Windows 安装包

生产发布采用：

```text
PyInstaller onedir → Inno Setup → DeskBoard-Setup-x.y.z.exe
```

### 1. 构建 onedir

仓库提供 `scripts/build.ps1` 和 `installer/deskboard.spec`。直接构建：

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm installer\deskboard.spec
```

构建结果示例：

```text
dist\DeskBoard\DeskBoard.exe
dist\DeskBoard\_internal\...
```

onedir spec 必须显式或通过 Qt hook 收集：

- `src/deskboard/ui/dashboard/web/` 本地页面；
- QWebChannel 客户端脚本；
- GridStack JavaScript、CSS 和许可证文件；
- Qt WebEngine 的 process、resources 和相关运行时文件。

### 2. 构建 Inno Setup 安装程序

安装 Inno Setup 后执行：

```powershell
iscc .\installer\deskboard.iss
```

最终产物为：

```text
dist\installer\DeskBoard-Setup-x.y.z.exe
```

### 3. 安装包验收

在没有开发环境依赖的干净测试目录或 Windows 用户环境中验证：

1. 安装程序能正常安装并创建开始菜单/启动入口。
2. 已安装程序不依赖 Python、源码目录或开发机环境变量。
3. Dashboard、Settings、托盘、单实例和三种模式均可用。
4. `%LOCALAPPDATA%\DeskBoard\data\deskboard.db` 和 `logs\deskboard.log` 正常生成。
5. 自启动默认关闭，开启后只作用于当前用户。
6. 卸载不会静默删除用户数据库和日志。
7. 网络失败时仍能显示最后成功缓存，并在 Data Status 中留下可读错误。

V1 不提供 portable ZIP、不提供自动更新，也不把代理/VPN 配置作为产品功能。

## 项目文档

- [产品规格说明](docs/spec.md)：用户可见行为、数据语义、架构边界和 V1 排除项。
- [实现计划](docs/implementation-plan.md)：Task 0–29 的构建顺序、文件范围和验收门槛。
- [需求追踪矩阵](docs/quality/requirements-traceability.md)：需求到任务/验证项的导航。
- [测试矩阵](docs/quality/test-matrix.md)：自动化测试和人工验收覆盖范围。
- [稳定性验收清单](docs/v1-stability-checklist.md)：Task 28 的 CPU/RAM、长时运行和 Windows 人工验收记录。
- [数据源审计](docs/data-sources.md)：当前 Provider、访问复核、条款和发布前处理。
- [发布检查清单](docs/release-checklist.md)：Task 29 的发布门禁、证据字段和停止条件。
- [桌面壳风险验证](spikes/desktop_shell/README.md)：QWebEngine、QWebChannel、GridStack、窗口层级和 onedir 验证。
- [数据源门禁](spikes/providers/README.md)：天气、黄金、汇率和指数来源的验证方式与离线 fixture。

## V1 明确不包含的内容

以下内容需要未来单独进行产品和架构评审，不属于 V1：

- 云端账号、登录、同步和远程数据库；
- 提醒、通知、闹钟和 Todo 重复规则；
- 标签、优先级、子任务、附件、项目管理；
- 插件/custom widget、用户脚本和任意金融代码输入；
- 金融图表、历史、新闻、交易和投资建议；
- 多显示器、边缘自动隐藏、WorkerW 桌面图标嵌入；
- 数据导入导出、自动数据库备份、自动更新和 portable ZIP；
- 运行时 CDN、localhost HTTP server、API Key 注册和代理配置。

## 数据声明

天气和金融信息依赖外部公开来源，可能存在延迟、缺失、口径差异或临时不可用。DeskBoard 只做个人桌面参考，不保证实时性、完整性、准确性或连续可用性，不构成投资、交易或其他专业建议。公开发布前应重新检查各来源的访问方式、署名要求、缓存与再分发限制。
