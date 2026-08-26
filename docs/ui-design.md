# DeskBoard 界面设计说明

本文记录 Task 30 的界面方向，便于后续维护时保持一致。项目只借鉴公开设计系统的原则，不复制第三方图片、字体文件或组件代码。

## 设计方向

- 设置页采用“侧栏导航 + 页面标题区 + 卡片式内容”的桌面应用结构，优先保证定位、层级和键盘焦点。
- Dashboard 使用语义化颜色：背景、卡片、分隔线、正文、次要文字、强调色、焦点环、成功/失败状态分别维护，主题只替换这些 token。
- 默认主题保持清爽浅色；同时提供深色和高对比主题。深色主题不是纯黑大面积铺满，而是使用分层表面和低饱和强调色，减少刺眼反差。
- 字体选择使用 Windows 常见字体和可选回退字体，不下载资源。小字号避免过细字重，中文和英文都要保持可读。
- 不使用持续动画、毛玻璃、远程 CDN 或第二个 QWebEngineView。

## 主题目录

| Key | 中文名 | 方向 |
| --- | --- | --- |
| `mist_blue` | 雾蓝晨光 | 浅色、冷静、默认 |
| `mint_breeze` | 薄荷清风 | 浅色、清新 |
| `almond_sand` | 杏仁暖沙 | 浅色、温暖 |
| `lavender_cloud` | 淡紫暮云 | 浅色、柔和 |
| `ocean_night` | 深海夜航 | 深色、蓝青 |
| `graphite_night` | 石墨夜色 | 深色、中性 |
| `rose_dusk` | 玫瑰暮色 | 深色、暖色 |
| `high_contrast` | 高对比度 | 深色、高辨识度 |
| `terra_signal` | 大地信号 · Terra Signal | 深色、黑白灰与警示黄 |
| `endfield_industrial` | 边境铸造 · Frontier Foundry | 深色、工业蓝灰与橙色 |
| `starrail_astral` | 星际航线 · Astral Transit | 深色、星际靛蓝与青金 |
| `wuthering_tide` | 海岸潮汐 · Coastal Tide | 深色、潮汐青绿与雾灰 |

## 字体目录

| Key | 中文名 | CSS 回退方向 |
| --- | --- | --- |
| `system_ui` | 系统界面 | Segoe UI Variable、Segoe UI、微软雅黑 |
| `yahei` | 微软雅黑 | Microsoft YaHei UI、Microsoft YaHei |
| `noto_sans` | Noto Sans | Noto Sans、Segoe UI |
| `source_han_sans` | 思源黑体 | Source Han Sans SC、微软雅黑 |
| `source_han_serif` | 思源宋体 | Source Han Serif SC、Georgia |

## 参考资料

- [Microsoft Fluent 2 Design System](https://fluent2.microsoft.design/)：参考桌面应用的层级、组件和焦点顺序组织方式。
- [Apple Human Interface Guidelines — Typography](https://developer.apple.com/design/human-interface-guidelines/typography)：参考字重、字号层级和最小可读性。
- [Apple Human Interface Guidelines — Color](https://developer.apple.com/design/human-interface-guidelines/color)：参考语义化颜色、对比度和不能只依赖颜色传达状态。
- [Apple Human Interface Guidelines — Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)：参考高对比、可辨识焦点和辅助信息。

四套扩展主题只使用项目自制的 CSS 色板、渐变和界面语言，不绑定具体
品牌，也不打包第三方 Logo、截图、角色图或其他外部素材。
