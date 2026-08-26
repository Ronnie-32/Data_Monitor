# DeskBoard V1 数据源与发布审计

审计日期：2026-08-25
适用范围：当前代码中实际注册的 Weather、Gold、FX、A-share indices、U.S. indices，以及随应用内置的 Weather 地点目录。

## 当前结论

当前结论分为两层：**学习向源代码可以公开；正式数据产品/安装包仍 NOT CLEARED**。原因有两类：

1. Task 28 的个人稳定性与性能人工证据仍是 `AWAITING_MANUAL_ACCEPTANCE`，尚未满足“先证明个人使用稳定，再公开发布”的前置条件。
2. 本轮能够确认来源页面和条款边界，但不能在当前执行会话中把所有来源标记为“普通中国大陆网络、无 VPN/代理/Clash 的实时直连 PASS”，也没有取得各来源面向公开发布的书面再分发许可。

这份文档记录的是发布边界，不是法律意见。技术上能够访问一个公开 URL，不等于项目取得了响应、缓存或派生数据的再分发许可；“公开可访问”也不等于“可以自由使用”。

## 审计规则与证据

- Provider 只请求、解析和归一化；当前实现没有运行时多源 fallback、用户 API key、账号登录或代理配置。
- 早期可行性记录见 [Task 1 数据源门禁](../spikes/providers/README.md)。该记录写明用户在 2026-08-20、关闭 VPN/系统代理/Clash 的普通中国大陆网络中完成过来源验收。
- 本轮 2026-08-25 检查到当前进程没有 `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` 环境变量，`netsh winhttp show proxy` 为 `Direct access (no proxy server)`。使用 `curl --noproxy '*'` 探测时，天气 HTTP 地址先返回 301 到 HTTPS；各 HTTPS 请求随后在本机 Schannel 以 `SEC_E_NO_CREDENTIALS (0x8009030E)` 失败。该结果只能分类为**当前环境无法完成复核**，不能证明上游来源在普通大陆网络不可用，也不能作为 PASS。
- 发布前必须在正常 Windows 中国大陆网络会话中重新执行实时来源检查，并保留日期、网络前提、端点、HTTP 状态、响应字段和输出摘要。
- 发现“未找到明确公开许可”时，默认按未清除处理：取得书面授权，或替换/删除/延期对应的公开发布功能。

## 当前发货来源

| 功能 | 代码中的来源/端点 | 当前访问证据 | 条款/署名结论 | 公开发布前动作 |
| --- | --- | --- | --- | --- |
| Weather 当前天气 | [中国天气网](https://www.weather.com.cn/)；`http://d1.weather.com.cn/weather_index/{city_id}.html` | Task 1 历史人工记录为 PASS；本轮因本机 TLS 凭据错误未完成复核 | 官方[版权声明](https://www.weather.com.cn/wzfw/banquan.shtml)要求未经书面许可不得变更、发行、转载、复制、镜像或利用内容/服务 | 取得适用于本 Provider 的书面许可，或替换/延期 Weather 公开发布 |
| Weather 日预报高低温 | [中国天气网](https://www.weather.com.cn/)；`http://www.weather.com.cn/weather/{city_id}.shtml` | 同上 | 同上；保留来源名称和链接不能替代书面许可 | 同上 |
| Weather 地点目录 | 当前代码内置 [hivefans Gist 快照](https://gist.github.com/hivefans/fcf4eed120e87968d9bf99e43e75ba56)，快照日期 `2026-08-25` | 离线内置，不代表上游实时可达 | Gist 页面显示为 `Uncategorized`，本次未找到明确许可证；不能把第三方快照当作可自由再分发资产 | 换成有明确许可的第一方/可再分发目录，取得权利人许可，或延期地点目录公开发布 |
| Gold / Au99.99 | [上海黄金交易所](https://www.sge.com.cn/)；`https://www.sge.com.cn/sjzx/quotation_daily_new` | Task 1 历史人工记录为 PASS；本轮 HTTPS 复核受本机 TLS 凭据错误阻断 | 官方主页标注 `Copyright ... All Right Reserved`；本次未找到该日行情端点的通用开放再分发许可。SGE 页面还会对含专有数据的栏目设置复制/出售/进一步传播限制，不能从“公开可见”推导出授权 | 向 SGE 确认 Au99.99 日行情抓取、缓存和公开分发权限；未获确认前延期公开 Gold |
| FX / USD/EUR/JPY/HKD | [中国货币网](https://www.chinamoney.com.cn/)；`https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew` | Task 1 历史人工记录为 PASS；本轮 HTTPS 复核受本机 TLS 凭据错误阻断 | [信息产品说明](https://www.chinamoney.com.cn/chinese/xxcpjjjsq/)称市场数据归交易中心所有；复制、传输、存储、使用、发布等需要书面许可。[媒体数据服务](https://www.chinamoney.com.cn/chinese/mtsjfu/)要求授权并注明来源 | 取得书面授权/许可，或替换/延期 FX 公开发布 |
| A-share indices | [腾讯财经入口](https://finance.qq.com/)；`https://qt.gtimg.cn/q=s_sh000001,s_sz399001,s_sz399006,sh000300` | Task 1 历史人工记录为 PASS；本轮 HTTPS 复核受本机 TLS 凭据错误阻断 | 本次未找到 `qt.gtimg.cn` 端点的公开再分发许可；[腾讯法律声明](https://www.tencent.net.cn/zh-cn/legal-statement/)保留其及合作伙伴内容的版权权利 | 取得适用于行情端点的书面许可，或切换到有明确许可的来源/延期 A 股指数 |
| U.S. indices | [腾讯财经入口](https://finance.qq.com/)；`https://qt.gtimg.cn/q=us.DJI,us.INX,us.IXIC` | Task 1 历史记录称候选项通过；本轮 HTTPS 复核受本机 TLS 凭据错误阻断 | 同 A-share；不能因为指数代码是美国市场就放宽大陆直连或再分发门禁 | 取得书面许可，或切换/延期 U.S. indices |

“Task 1 历史人工记录为 PASS”只表示当时的技术直连验收，不表示今日仍然可用，也不表示获得了公开分发许可。

## 对用户的声明

DeskBoard 的天气和金融数据只是本地桌面参考信息，可能延迟、缺失、临时不可用或与其他渠道口径不同。项目不承诺实时性、交易级、投资级、完整性、准确性或连续可用性；数据不构成投资、交易、天气安全或其他专业建议。不得把 Dashboard 数值用于下单、风控、定价或任何需要受监管数据质量的场景。

## 发布前必须完成

- Task 28 的稳定性清单所有必要人工证据由用户确认并关闭。
- 在普通中国大陆网络、VPN/代理/Clash 均关闭的条件下重新检查所有实际端点；失败项必须替换或延期。
- 为 Weather、Weather 地点目录、SGE、CFETS、Tencent 分别取得可留档的条款/授权结论。
- 将实际要求的来源名称、链接、署名和限制同步到 README 与 About 页面。
- 只有完成上述事项，才可把本文件中的“未清除”改为逐项 `CLEARED`，创建正式 GitHub Release、上传安装包或宣传为公开可用的数据产品。学习向源代码仓库可以在明确说明边界的前提下公开；这不代表第三方数据授权已经取得。
