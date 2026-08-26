# DeskBoard Dashboard visual/readability baseline

Status: implementation baseline for the Task 23 manual gate.

This document records the values implemented in the Dashboard. The screenshots and real Windows observations required by `MAN-UI-01..14`, `MAN-TODO-03`, `MAN-TT-07`, and `MAN-PERF-06` still need to be confirmed in a normal desktop session before this task can be marked complete.

## Default Profile arrangement

The Dashboard uses a fixed 48-column GridStack topology with 20–32px vertical cells. The web fallback layout materializes all eight V1 widget types when a Profile has not yet stored a row for a newer widget. Coordinates are zero-based and are not reflowed when the outer window is resized. Existing 12-column Profile coordinates are scaled by four during the schema migration.

| Widget | x | y | w | h | Visual role |
| --- | ---: | ---: | ---: | ---: | --- |
| `todo` | 0 | 0 | 24 | 12 | primary task list with a compact header and scrollable content |
| `today_agenda` | 24 | 0 | 24 | 12 | timed and date-only agenda with a compact readable height |
| `weather` | 0 | 12 | 48 | 3 | wide primary-city / multi-city weather summary; grows with populated content |
| `gold` | 0 | 15 | 12 | 3 | compact gold reference card; grows with populated content |
| `fx` | 12 | 15 | 12 | 3 | compact FX reference card; grows with populated content |
| `china_indices` | 24 | 15 | 12 | 3 | compact A-share reference card; grows with populated content |
| `us_indices` | 36 | 15 | 12 | 3 | compact U.S. reference card; grows with populated content |
| `finance_overview` | 0 | 18 | 48 | 3 | optional combined view, hidden by default to avoid repeating category cards |

Information cards occupy one compact row by default, so empty or short data does not leave a large blank rectangle. A populated card grows to the content-required height, up to 3 grid rows; longer lists remain reachable through its own thin scrollbar. The combined Finance Overview remains supported in Layout Edit, but is hidden by default because it repeats the same enabled items already shown by those category cards.

## Accepted-size candidate and thresholds

The implementation enforces a conservative overall native Dashboard minimum of **360 × 220 CSS pixels**. This permits a compact Profile containing only Weather and Todo while retaining enough room for the shell and one-column widget cards. The previous **960 × 720** size remains a comfortable all-widget review size, not a hard lower bound. The layout viewport scrolls vertically when the fixed 48-column board has more rows than the current panel can show; it never compresses the row pixels just to make every card fit at once.

The following per-widget minimums are the visual baseline used by the CSS and default layout. They describe the widget rectangle, not the outer window:

| Widget | Minimum readable rectangle | Rationale |
| --- | --- | --- |
| `todo` | 340 × 280 | keeps checkbox, two-line content/meta, and a useful scroll viewport |
| `today_agenda` | 340 × 280 | keeps time column, title, conflict metadata, and a useful scroll viewport |
| `weather` | 720 × 150 | keeps the primary city reading and range without a shell title |
| `gold` | 145 × 145 | one or more compact finance rows with a readable name/value pair |
| `fx` | 145 × 145 | one or more compact finance rows; overflow remains reachable when necessary |
| `china_indices` | 210 × 145 | provides room for the longer index name and value |
| `us_indices` | 145 × 145 | one compact index row with an explicit signed change |
| `finance_overview` | 210 × 145 | reveals more global-order items as width/height grows |

Size adaptation is derived from actual pixel dimensions and is never persisted as a generic mode:

| Presentation | Threshold | Derived behavior |
| --- | --- | --- |
| compact | widget content width `< 240px` | tighter data-row spacing and smaller readings |
| normal | width `240–479px` | normal typography and direct data rows |
| expanded | width `≥ 480px` | larger headings/readings and more comfortable direct data rows |

CSS container units are used for smooth typography rather than a single jump at
the outer widget width. Information cards keep every weather/finance row in the
DOM instead of slicing data; the layout controller measures the list
`scrollHeight` and grows a card only up to 3 grid rows, after which the card's
thin inner scrollbar provides access to the remaining rows. Grid coordinates,
Profile data, and the `displayMode` configuration remain separate from these
pixel decisions.

Typography is derived from the nearest live card/container rather than from the
outer window. `clamp()` plus container-width units scale headings, content,
metadata, and readings continuously within readable minimum/maximum bounds.
Finance name/value pairs remain a two-column single-line heading even below
`240px`; only genuinely overlong text is right-elided, while Todo and Today
Agenda content may wrap when its own text cannot fit. Information cards render
all selected rows, use a bounded default length, and expose a thin inner
scrollbar only when the selected data exceeds that length.

## Shared visual tokens

- Outer page inset: `12px`.
- Dashboard surface inset: `20px`.
- Outer rounding: `16px`; widget rounding: `12px`; control rounding: `8px`.
- Grid divider/gap: `2px` per side; GridStack item top/bottom inset: `2px` per side, preserving a visible fine-grid separation without creating blank bands.
- The layout editor keeps an unlimited row count, uses a finer stable 20–32px cell-height range derived from the grid width, and puts the GridStack board inside a separate scrollable viewport. Pushed widgets remain reachable instead of being clipped outside the Dashboard.
- Weather, FX, Gold, index, and Finance Overview cards omit the shell title and put the data list at the top of the card. Todo and Today Agenda retain their titles and interaction scroll behavior.
- Layout Edit shows resize handles on every edge/corner and uses friendly visibility labels; dragging and resizing stay inside the web grid so the outer window does not jump.
- Layout Edit adds a faint 48-column/row guide and a dashed drop placeholder so middle/right placement is visible while a card is being moved.
- The layout editor preserves a requested horizontal grid column. If an old Profile contains an overlap, only the colliding later item is moved down at the same `x`; the whole board is not globally compacted back to the left.
- The native layout-edit drag bar is limited to its visible center strip, and its 4px window resize gutter does not cover GridStack's item resize handle.
- The base font stack is local Windows `Segoe UI Variable Text`, then `Segoe UI` and `Microsoft YaHei UI`; no remote font is loaded.
- Widget regions use light semi-transparent fills; text and icons remain opaque.
- Borders and timetable lines are subtle theme-derived dividers; the only shadow is a low-spread panel/context-menu shadow.
- There is no acrylic/mica blur, decorative animation, high-frequency polling, or runtime remote asset.

## Themes and Profile opacity behavior

The Profile theme catalog includes the following light, dark, and high-contrast keys, plus four original token-based genre-inspired variants:

| Theme key | Display name | Direction |
| --- | --- | --- |
| `mist_blue` | Mist Blue / 雾蓝晨光 | cool blue surface and blue accent |
| `mint_breeze` | Mint Breeze / 薄荷清风 | pale mint surface and green-teal accent |
| `almond_sand` | Almond Sand / 杏仁暖沙 | warm sand surface and ochre accent |
| `lavender_cloud` | Lavender Cloud / 淡紫暮云 | pale lavender surface and violet accent |
| `ocean_night` | Ocean Night / 深海夜航 | dark blue surface and cyan accent |
| `graphite_night` | Graphite Night / 石墨夜色 | dark neutral surface and soft blue accent |
| `rose_dusk` | Rose Dusk / 玫瑰暮色 | dark berry surface and rose accent |
| `high_contrast` | High Contrast / 高对比度 | black surface and high-visibility focus |
| `terra_signal` | Terra Signal / 大地信号 | industrial charcoal and warning yellow |
| `endfield_industrial` | Frontier Foundry / 边境铸造 | slate machinery tones and safety orange |
| `starrail_astral` | Astral Transit / 星际航线 | astral indigo, cyan, and warm starlight |
| `wuthering_tide` | Coastal Tide / 海岸潮汐 | coastal blue-green and signal cyan |

All themes use the same semantic text, completion, status, and financial-direction tokens. The four named variants are original CSS token combinations and do not include game logos, screenshots, character art, or other third-party assets. Profile `panelOpacity` is clamped to the persisted `0..1` domain in the web render layer. It changes only the surface/widget background alpha; text, controls, borders, and status indicators do not become translucent. The default is `1.0`.

## Semantic readability treatments

- A completed Todo uses a pale/light green background and a native checkbox check. It is not struck through. The same treatment is used in Agenda and timetable renderings.
- Finance positive/up values use red and keep an explicit `+`; negative/down values use green and keep an explicit `-`. These tokens are shared by all themes.
- In the weekly timetable, courses have visual priority (`z-index: 2` and the theme accent); Todos remain visible in a narrower secondary lane (`z-index: 3`) with a light warm conflict indication. Point Todos retain a thin marker, range Todos retain a normal block, and completed items retain the pale-green treatment.
- Timed Agenda and timetable items remain normally visible after their start time; elapsed time does not add an automatic grey state.

## Manual gate fixture set

The manual review should render all eight widget types with local/fixture data: at least three incomplete Todos, one completed-today Todo, one timed course, one date-only item, Beijing and Shanghai weather, one gold item, three FX items, three A-share indices, three U.S. indices, and a mixed Finance Overview. Repeat the full fixture review at 960 × 720, a normal 1200 × 840, and a larger 1440 × 960 window. Also create a compact Profile with only Weather and Todo visible and verify it at 360 × 220. Then switch each Profile through all twelve themes and at least three opacity values.
