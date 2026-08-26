# Task 31 manual acceptance

Run the current source entry on an ordinary Windows 10/11 session after closing
any older DeskBoard process. These checks require the real native Settings,
Dashboard QWebEngine page, window hit-testing, and a restart.

## Timetable schemes

1. On a fresh or migrated sample database, confirm there is one starter scheme
   named `UIBE` and one active sample semester named `样例`; the UIBE scheme is
   bound to that semester and its eight editable period rows are visible.
2. Open Settings → Courses and create two additional semesters and two
   reusable schemes.
3. Select each semester in the list. The timetable-scheme combo, selected
   scheme name, axis mode, count, and period rows must follow the selected
   semester; binding a scheme must immediately refresh that view.
4. Bind one scheme to both semesters, switch the active semester, then switch
   Profile. The selected scheme and its rows must remain unchanged; changing a
   Profile must not change timetable configuration.
5. Create a custom scheme with a non-eight count, gaps, and arbitrary actual
   times. Save it, open the weekly timetable, and confirm the first/last bounds,
   labels, and course blocks use the saved times. Try missing, duplicate,
   overlapping, and out-of-range rows; invalid edits must not become active.
   In the period editor, there must be one visible period-number column (no
   duplicate row-number strip), no row/control overlap, and the error text must
   appear beside the Save button when validation fails. A valid save must also
   refresh the open Dashboard timetable immediately.
6. Select Uniform day, first accept the default `00:00–24:00`, then save a
   custom range and guide count. Confirm guide bands are equal visual guides,
   carry no artificial period labels, and courses/Todos remain at their actual
   clock times. Items wholly outside the range must be absent.
7. Delete a bound scheme. Cancel the first confirmation; then confirm the
   deletion. Affected semesters must become unbound and the timetable must show
   configure-first without invented school times. Today Agenda must still work.
8. Confirm the semester, recurring-course, one-off-course, and scheme lists
   each occupy about six to seven rows rather than expanding through the empty
   page area. Long entries should stay on one line with right-side ellipsis;
   hovering shows the complete text. On a migrated database, the built-in entry
   is named `UIBE`; edit a period, click Save scheme, and confirm the existing
   period data is retained after refresh.

## Settings preview

1. In Profiles, select several light/dark themes and at least one font without
   saving. The native Settings shell/page and Dashboard must update in the same
   interaction, with no unexpected black Windows night-mode surfaces; text,
   table headers, selected rows, and time controls must remain readable on
   purple/dark palettes.
2. Close Settings without Save Appearance and reopen it. The stored Profile
   theme/font must be restored; only Save Appearance may persist the preview.
3. Open Settings → Courses → Timetable under each light theme. In the period
   table, the Period/Start/End headers, period numbers, time values, input
   caret, and validation status must all be readable against their backgrounds.
   Hover ordinary and primary buttons, combo boxes, and time controls; if a
   control becomes light, its text must switch to a dark readable color.
4. Confirm the four additional theme names are `Terra Signal`, `Frontier
   Foundry`, `Astral Transit`, and `Coastal Tide` (Chinese: `大地信号`、`边境铸造`、
   `星际航线`、`海岸潮汐`), with no third-party game title or company name in
   the selectable labels.
5. Switch the Dashboard between compact and wide windows. Widget text should
   stay readable, and the weekly timetable should enlarge its title, headers,
   course/Todo blocks, and metadata when width is available without clipping
   at compact width.

## Dashboard Todo / Agenda

1. In the default Chinese Dashboard, confirm the widget title is `今日日程`
   and the single agenda list heading is `今日事项`; the old English labels
   and separate `定时事项` section must not be shown in this view.
2. Compare Todo and Agenda rows. Content, metadata, empty states, wrapping,
   font size, line height, and muted colors should match. Timed rows must show
   their time after the title; date-only rows must not show an empty time column.
3. Click the Agenda `+`, enter content, and press Enter. A new item must appear
   in the unified `今日事项` list. It must be a today-planned Todo, and it must
   remain available after a refresh.

## Layout Edit

1. Enter Layout Edit at a normal width. Confirm the normal DeskBoard title,
   mode, status dot, and Open Settings button temporarily give way to a
   dedicated edit bar in the same title-row area. The bar must show Save and
   Cancel on the first row and the visibility controls on a separate row; it
   must not cover the grid.
2. Click Save, Cancel, and each visibility control. These clicks must remain
   clickable and must not move the native window. Drag from the blank title or
   instruction area of the edit bar; the window must move across the full
   first row, not only at its upper edge. Resize handles must remain functional.
3. After Save or Cancel, confirm the normal title/mode/status/settings row is
   restored. Repeat at a narrow window width: Save/Cancel must remain visible,
   visibility controls must wrap without a horizontal scrollbar, and no control
   may overlap.
4. In Interaction mode, click a Todo and toggle its checkbox. The mode label
   must remain `interaction`; a Todo update must not switch the Dashboard to
   Locked mode.

Record screenshots or a short observation for `MAN-TT-08..11`, `MAN-SET-05`,
`MAN-SET-15`, and `MAN-LAYOUT-04` before closing Task 31.

## Dashboard viewport

1. With all visible widgets fitting in the window, confirm the Dashboard has no
   outer vertical scrollbar, does not reserve a scrollbar gutter, and has no
   persistent empty grid tail caused by hidden widgets.
2. In Layout Edit, drag or resize a visible widget below the available window
   area. The viewport should then become vertically scrollable; when the widget
   is moved back so all visible content fits, the scrollbar should disappear.

## Default Profile recovery

1. Close any running DeskBoard instance and start the updated application once
   so the Default recovery runs. In Settings → Profiles, confirm that the
   built-in `Default` entry still exists and that user Profile `1` is still
   present.
2. Switch between Profile `1` and `Default`. Default must show the same
   Dashboard widget visibility, positions, sizes, window geometry, and widget
   display configuration as Profile `1`; Default's own theme, font, and
   opacity must remain unchanged.
3. While Default is active, enter Layout Edit and press Save. The existing
   Save As behavior must remain: a new user Profile is requested rather than
   overwriting Default. Rename and Delete must still reject the built-in
   Default. Profile `1` must remain unchanged after this check.

## Localization follow-up

1. Start with the persisted default language. In Settings, verify that the
   ordinary UI labels are Chinese, including `当前模式`, `课程`, `保存方案`,
   `取消`, `刷新`, `节次`, `开始`, and `结束`. DeskBoard, Windows, and actual
   font/data-source names may remain proper names.
2. Change the language selector to English. The Settings navigation, page
   controls, course editor, profile/weather/finance/data-status text, dialog
   buttons, and Dashboard titles/placeholders should update immediately;
   `Current mode`, `Weekly Timetable`, `Todo`, and `Today Agenda` should be
   English rather than stale Chinese.
3. Switch back to Chinese without restarting. Open the course period editor,
   Todo editor, and a profile/weather dialog; confirm their titles, buttons,
   validation messages, and status text are Chinese and no ordinary English
   labels such as `Current` remain.
4. Restart DeskBoard and confirm the selected language persists in both the
   native Settings window and the Dashboard.
