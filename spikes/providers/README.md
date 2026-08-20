# Task 1：中国大陆直连数据源门禁

状态：**COMPLETE**。用户于 2026-08-20 在 VPN、系统代理和 Clash
关闭的普通中国大陆网络完成修正版 `--record` 验收；北京、上海及全部
必选类别均 PASS，美股三项候选也通过。

本目录是数据源可行性 spike，不是生产 Provider。脚本只访问列出的固定来源，使用 `ProxyHandler({})` 禁用 urllib 的环境/系统代理发现，不需要 API Key、账户或代理，也不做运行时多源 fallback。

天气首选城市为北京和上海，两座城市均属于必测项。

## 运行

在仓库根目录执行：

```powershell
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --record
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --offline
```

`--record` 保存成功的原始响应到 `tests/fixtures/providers/`；`--offline` 完全不联网，只重放相同解析器。每个响应上限 256 KiB，请求超时 10 秒。

## 固定来源与字段语义

| 类别 | 来源 | 归一化结果 | Task 1 状态 |
|---|---|---|---|
| Weather | 中国天气网城市天气索引 + 同站正式逐日预报页；北京 `101010100`、上海 `101020100` | 索引取实况 condition/current/wind，逐日页取当天预测 high/low；归一化区间再用当前实况扩展，保证 `low <= current <= high`；°C | 两城均强制验证；避免简版索引高低温失真 |
| Gold | 上海黄金交易所每日行情页 | Au99.99 每日收盘价、涨跌、涨跌幅；CNY/g | 必选；周末/节假日只在同一来源内有限回看 10 天 |
| FX | 中国外汇交易中心 `CcprHisNew` | USD/EUR/JPY/HKD 统一为每 1 外币对应 CNY；上游 `100JPY/CNY` 除以 100 | 必选；查询最近 14 天记录 |
| A-share indices | 腾讯公开批量报价 | 上证、深证成指、创业板、沪深300的点位、涨跌、涨跌幅 | 必选候选 |
| U.S. indices | 同一腾讯批量报价 | 道琼斯、标普500、纳斯达克综合 | 条件项，必须单独通过大陆直连人工门禁 |

固定入口：

- Weather: `http://d1.weather.com.cn/weather_index/{city_id}.html`
- Weather daily high/low: `http://www.weather.com.cn/weather/{city_id}.shtml`
- Gold: `https://www.sge.com.cn/sjzx/quotation_daily_new`
- FX: `https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew`
- Indices: `https://qt.gtimg.cn/q=s_sh000001,s_sz399001,s_sz399006,sh000300,us.DJI,us.INX,us.IXIC`

## 失败与发布边界

连接失败、超时、响应过大、编码或字段异常会输出有界的单行 `FAIL`；任何必选类别失败时退出码为 1。脚本不会删除已有 fixture，也不会切换到第二来源。美股三项不完整时输出 `DEFER`，不伪装成已通过。

本次 Codex 运行只能证明当前 Windows 环境中显式绕过代理后的技术可达性，不能代替“普通中国大陆网络、VPN/代理/Clash 均关闭”的人工验收。GitHub 发布前还必须逐项复核上游条款、署名、缓存/再分发限制，并保留“非实时保证、非投资建议”声明。

## 人工验收

确认 VPN、系统代理和 Clash 已关闭后，在普通中国大陆网络执行：

```powershell
Remove-Item Env:HTTP_PROXY,Env:HTTPS_PROXY,Env:ALL_PROXY -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --record
.\.venv\Scripts\python.exe spikes\providers\check_sources.py --offline
```

预期：北京、上海均打印包含 condition/current/high/low/wind 的 `PASS weather/...`；黄金、四项 FX、四项 A 股指数均 `PASS`；美股三项完整时打印 `PASS us_indices candidate`，否则明确 `DEFER`。离线运行应走相同解析路径并通过。
