"""Small dependency-free localization helpers for the native Settings shell."""

from __future__ import annotations

from collections.abc import Iterable

SUPPORTED_LANGUAGES = ("zh_CN", "en_US")

# The Settings pages predate localization and contain a mixture of English and
# Chinese labels. Keeping the pairs here lets the shell retranslate existing
# widgets without adding a second UI framework or duplicating page logic.
_TEXT_PAIRS = {
    "DeskBoard Settings": "DeskBoard 设置",
    "General": "常规",
    "Profiles": "配置方案",
    "Weather": "天气",
    "Finance": "金融",
    "Todo": "待办",
    "Courses": "课程",
    "Data Status": "数据状态",
    "About": "关于",
    "Dashboard visibility and daily mode": "看板显示与日常模式",
    "Dashboard": "看板",
    "Show Dashboard": "显示看板",
    "Hide Dashboard": "隐藏看板",
    "Mode": "运行模式",
    "Locked": "锁定",
    "Interaction": "交互",
    "Current mode: interaction": "当前模式：交互",
    "Current mode: locked": "当前模式：锁定",
    "Current mode: layout_edit": "当前模式：布局编辑",
    "Enter Layout Edit": "进入布局编辑",
    "Start DeskBoard with Windows": "随 Windows 启动 DeskBoard",
    "Autostart unavailable": "自启动不可用",
    "Autostart enabled": "已启用自启动",
    "Autostart disabled": "已关闭自启动",
    "Exit DeskBoard": "退出 DeskBoard",
    "Language": "语言",
    "Simplified Chinese": "简体中文",
    "English": "英语",
    "Visual and spatial Dashboard Profiles": "看板的视觉与空间配置",
    "New Profile name": "新配置名称",
    "Create Profile": "新建配置",
    "e.g. Work, Study, Evening": "例如：工作、学习、晚间",
    "Weather display mode for this Profile": "此配置的天气显示模式",
    "Primary city detail": "主城市详情",
    "Multi-city summary": "多城市摘要",
    "Save Weather Display": "保存天气显示",
    "Switch": "切换",
    "Save Current": "保存当前配置",
    "Save As": "另存为",
    "Rename": "重命名",
    "Delete": "删除",
    "Restore Default": "恢复默认",
    "Theme": "主题",
    "Font": "字体",
    "Save Appearance": "保存外观",
    "Mist Blue": "雾蓝晨光",
    "Mint Breeze": "薄荷清风",
    "Almond Sand": "杏仁暖沙",
    "Lavender Cloud": "淡紫暮云",
    "Ocean Night": "深海夜航",
    "Graphite Night": "石墨夜色",
    "Rose Dusk": "玫瑰暮色",
    "High Contrast": "高对比度",
    "Terra Signal": "大地信号",
    "Frontier Foundry": "边境铸造",
    "Astral Transit": "星际航线",
    "Coastal Tide": "海岸潮汐",
    "System UI": "系统界面",
    "Microsoft YaHei": "微软雅黑",
    "Noto Sans": "Noto Sans",
    "Source Han Sans": "思源黑体",
    "Source Han Serif": "思源宋体",
    "Global weather cities": "全局天气城市",
    "Search mainland-China locations (Chinese / pinyin):": "搜索中国大陆城市（中文 / 拼音）：",
    "Add Selected Location": "添加所选城市",
    "Global validated finance items": "全局已验证金融项目",
    "Refresh All": "全部刷新",
    "Open Log Folder": "打开日志文件夹",
    "Courses and timetable": "课程与课表",
    "Semesters": "学期",
    "Weekly recurring courses": "每周重复课程",
    "One-off courses and reschedules": "单次课程与调课",
    "Global class periods (1–8)": "全局课程节次（1–8）",
    "Timetable header": "课表表头",
    "Reusable timetable schemes": "可复用课表方案",
    "Timetable schemes": "课表方案",
    "Add scheme": "新增方案",
    "Duplicate": "复制",
    "Scheme editor (Save / Cancel)": "方案编辑（保存 / 取消）",
    "Custom school periods": "自定义学校节次",
    "Uniform day (no school times)": "均匀日（不使用学校节次）",
    "Name": "名称",
    "Axis": "轴模式",
    "Guide / period count": "参考带 / 节次数",
    "Uniform day range": "均匀日范围",
    "Custom period rows": "自定义节次行",
    "Save scheme": "保存方案",
    "Bind selected scheme": "绑定所选方案",
    "Timetable scheme": "课表方案",
    "Unbound / configure first": "未绑定 / 请先配置",
    "Edit details": "编辑详情",
    "Restore to incomplete": "恢复为未完成",
    "Mark complete": "标记完成",
    "Delete permanently": "永久删除",
    "Version": "版本",
    "Profile service unavailable": "配置服务不可用",
    "Weather display": "天气显示",
    "Settings": "设置",
    "Monday": "周一",
    "Tuesday": "周二",
    "Wednesday": "周三",
    "Thursday": "周四",
    "Friday": "周五",
    "Saturday": "周六",
    "Sunday": "周日",
    "e.g. Suzhou, suzhou, Chaoyang": "例如：苏州、suzhou、朝阳",
    "Local preferences, Profiles, and data sources": "本地偏好、配置方案与数据源",
    "Dashboard appearance": "看板外观",
    "Dashboard theme and font": "看板主题与字体",
    "Theme and font preview immediately; save Appearance to persist.": (
        "主题和字体会立即预览；点击保存外观后持久化。"
    ),
    "Enter a name for the new Profile": "请输入新配置名称",
    "Preview applied; click Save Appearance to persist.": "预览已应用；点击保存外观后持久化。",
    "Dashboard preview failed": "看板预览失败",
    "Configured global cities": "已配置的全局城市",
    "Primary city": "主城市",
    "Move Up": "上移",
    "Move Down": "下移",
    "Add City": "添加城市",
    "Remove City": "移除城市",
    "Preferences": "偏好设置",
    # Course editors and their validation feedback.
    "Weekday only": "仅显示星期",
    "Weekday + date": "星期 + 日期",
    "Date only": "仅显示日期",
    "Edit Semester": "编辑学期",
    "Start Monday": "起始周一",
    "Total weeks": "总周数",
    "Semester name must not be empty": "学期名称不能为空",
    "Start date must be a Monday": "开始日期必须是周一",
    "Edit Recurring Course": "编辑每周重复课程",
    "Semester": "学期",
    "Course name": "课程名称",
    "Weekday": "星期",
    "Start time": "开始时间",
    "End time": "结束时间",
    "Start week": "开始周",
    "End week": "结束周",
    "Classroom": "教室",
    "Course name must not be empty": "课程名称不能为空",
    "End time must be later than start time": "结束时间必须晚于开始时间",
    "End week must not be before start week": "结束周不能早于开始周",
    "Edit One-off Course": "编辑单次课程",
    "Course date": "课程日期",
    "Cancel Course Occurrence": "取消课程安排",
    "Recurring course": "每周重复课程",
    "Occurrence date": "课程日期",
    "Choose a recurring course": "请选择每周重复课程",
    "Add": "添加",
    "Edit": "编辑",
    "Active semester": "当前学期",
    "Use": "使用",
    "Cancel occurrence": "取消本次课程",
    "Restore occurrence": "恢复本次课程",
    "Recurring": "每周课程",
    "One-off": "单次课程",
    "to": "至",
    "Period": "节次",
    "Start": "开始",
    "End": "结束",
    "Timetable": "课表",
    "Column labels": "列标题",
    "Course service unavailable": "课程服务不可用",
    "Custom period editor is incomplete": "自定义节次编辑器未完成",
    "Timetable scheme created": "课表方案已创建",
    "copy": "副本",
    "Timetable scheme duplicated": "课表方案已复制",
    "Rename timetable scheme": "重命名课表方案",
    "Scheme name:": "方案名称：",
    "Timetable scheme renamed": "课表方案已重命名",
    "timetable scheme": "课表方案",
    "Timetable scheme deleted; affected semesters are unbound": (
        "课表方案已删除；受影响的学期已解除绑定"
    ),
    "Select a timetable scheme before saving": "保存前请先选择课表方案",
    "Timetable scheme saved": "课表方案已保存",
    "Timetable scheme edits cancelled": "已取消课表方案编辑",
    "Semester timetable scheme binding saved": "学期课表方案绑定已保存",
    "Semester saved": "学期已保存",
    "Semester updated": "学期已更新",
    "semester": "学期",
    "Semester deleted": "学期已删除",
    "Active semester updated": "当前学期已更新",
    "Recurring course saved": "每周重复课程已保存",
    "Recurring course updated": "每周重复课程已更新",
    "recurring course": "每周重复课程",
    "Recurring course deleted": "每周重复课程已删除",
    "Occurrence cancelled": "本次课程已取消",
    "Restore Course Occurrence": "恢复课程安排",
    "Occurrence restored": "本次课程已恢复",
    "One-off course saved": "单次课程已保存",
    "One-off course updated": "单次课程已更新",
    "one-off course": "单次课程",
    "One-off course deleted": "单次课程已删除",
    "Class periods saved": "课程节次已保存",
    "Class-period edits cancelled": "已取消课程节次编辑",
    "Save failed: ": "保存失败：",
    "Delete course data?": "删除课程数据？",
    "This cannot be undone.": "此操作无法撤销。",
    "No active semester": "没有当前学期",
    "weeks": "周",
    "custom": "自定义",
    "uniform": "均匀日",
    "configured": "已配置",
    "not configured": "未配置",
    # Profile, weather, finance, todo, and diagnostics copy.
    "Select a Profile first, then customize its Dashboard theme and font.": (
        "请先选择配置方案，再自定义看板主题和字体。"
    ),
    "Built-in Default": "内置 Default",
    "User Profile": "用户配置",
    "Save As Profile": "另存为配置方案",
    "Rename Profile": "重命名配置方案",
    "Delete Profile": "删除配置方案",
    "Profile name:": "配置方案名称：",
    "Incomplete": "未完成",
    "Completed history": "已完成记录",
    "Found matching locations; select one to add": "找到匹配城市，请选择后添加",
    "No matching weather location": "没有匹配的天气城市",
    "Selected weather location is no longer available": "所选天气城市已不可用",
    "Location already added": "城市已添加",
    "Weather service unavailable": "天气服务不可用",
    "cities; primary is global": "个城市；主城市为全局设置",
    "Add Weather City": "添加天气城市",
    "City key:": "城市键：",
    "Display name:": "显示名称：",
    "Weather source city ID (numeric; Suzhou also accepts suzhou):": (
        "天气源城市 ID（数字；苏州也可填写 suzhou）："
    ),
    "Remove Weather City": "移除天气城市",
    "Remove the selected weather city?": "移除所选天气城市？",
    "Weather data source sync failed": "天气数据源同步失败",
    "Finance service unavailable": "金融服务不可用",
    "enabled; order is global": "项已启用；顺序为全局设置",
    "Item": "项目",
    "Group": "分组",
    "Source": "来源",
    "Last attempt": "最近尝试",
    "Last success": "最近成功",
    "Status": "状态",
    "Readable error": "可读错误",
    "Network diagnostics and manual refresh. The Dashboard has no refresh controls.": (
        "网络诊断与手动刷新。看板不提供刷新控件。"
    ),
    "Data refresh service unavailable": "数据刷新服务不可用",
    "network items": "个网络项目",
    "Log folder is unavailable": "日志文件夹不可用",
    "Unable to open log folder: ": "无法打开日志文件夹：",
    "Unable to open log folder": "无法打开日志文件夹",
    "Refresh ": "刷新",
    "China indices": "中国指数",
    "US indices": "美国指数",
    "unknown": "未知",
    "disabled": "已禁用",
    "never": "未刷新",
    "refreshing": "刷新中",
    "success": "成功",
    "error": "错误",
    "Dashboard visibility and shell mode": "看板显示与外壳模式",
    "Layout Edit": "布局编辑",
    "This page is a native shell for a later task.": "此页面是后续任务的原生设置界面。",
    "Current": "当前",
    "current": "当前",
    "Weekly Timetable": "每周课表",
    "Save": "保存",
    "Cancel": "取消",
    "Set": "设置",
    "Edit Todo": "编辑待办",
    "Todo details": "待办详情",
    "Content": "内容",
    "Deadline date": "截止日期",
    "Deadline time": "截止时间",
    "Planned date": "计划日期",
    "Planned start": "计划开始",
    "Planned end": "计划结束",
    "Invalid Todo": "待办内容无效",
    "Delete Todo permanently?": "永久删除待办？",
    "Todo content must not be empty": "待办内容不能为空",
    "planned end requires a planned start": "设置计划结束时间前必须先设置计划开始时间",
    "planned end must be later than planned start": "计划结束时间必须晚于计划开始时间",
    "Gold": "黄金",
    "FX": "汇率",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {}
for _english, _chinese in _TEXT_PAIRS.items():
    _TRANSLATIONS[_english] = {"en_US": _english, "zh_CN": _chinese}
    _TRANSLATIONS[_chinese] = {"en_US": _english, "zh_CN": _chinese}


def translate_text(value: str, language: str) -> str:
    """Translate one known static label and leave user/content data untouched."""

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported Settings language: {language}")
    return _TRANSLATIONS.get(value, {}).get(language, value)


def translate_mode_value(value: object, language: str) -> str:
    """Translate an AppMode value without importing the application layer."""

    mode = getattr(value, "value", value)
    source = {
        "locked": "Locked",
        "interaction": "Interaction",
        "layout_edit": "Layout Edit",
    }.get(str(mode), str(mode))
    return translate_text(source, language)


def current_mode_text(value: object, language: str) -> str:
    """Return the localized status shown below the mode radio buttons."""

    translated_mode = translate_mode_value(value, language)
    if language == "zh_CN":
        return f"当前模式：{translated_mode}"
    return f"Current mode: {translated_mode}"


def translate_widget_tree(root, language: str) -> None:
    """Retranslate known Qt labels below ``root`` while preserving user data."""

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported Settings language: {language}")
    from PySide6.QtWidgets import (
        QAbstractButton,
        QComboBox,
        QGroupBox,
        QLabel,
        QLineEdit,
        QListWidget,
        QTableWidget,
        QTabWidget,
        QWidget,
    )

    widgets: Iterable[QWidget] = (root, *root.findChildren(QWidget))
    for widget in widgets:
        if isinstance(widget, QComboBox):
            _translate_combo(widget, language)
        elif isinstance(widget, QListWidget):
            _translate_list(widget, language)
        elif isinstance(widget, QTabWidget):
            _translate_tabs(widget, language)
        elif isinstance(widget, QTableWidget):
            _translate_table_headers(widget, language)
        elif isinstance(widget, QGroupBox):
            _set_translated(widget, "title", widget.title(), language)
        elif isinstance(widget, QAbstractButton):
            _set_translated(widget, "text", widget.text(), language)
        elif isinstance(widget, QLabel):
            _set_translated(widget, "text", widget.text(), language)
        elif isinstance(widget, QLineEdit):
            _set_translated(
                widget,
                "placeholderText",
                widget.placeholderText(),
                language,
            )


def _set_translated(widget, setter: str, current: str, language: str) -> None:
    if not current and widget.property("_deskboard_i18n_source") is None:
        return
    source = widget.property("_deskboard_i18n_source")
    if not isinstance(source, str):
        source = current
        widget.setProperty("_deskboard_i18n_source", source)
    getattr(widget, f"set{setter[0].upper()}{setter[1:]}")(
        translate_text(source, language)
    )


def _translate_combo(combo, language: str) -> None:
    source_items = combo.property("_deskboard_i18n_items")
    if not isinstance(source_items, list) or len(source_items) != combo.count():
        source_items = [combo.itemText(index) for index in range(combo.count())]
        combo.setProperty("_deskboard_i18n_items", source_items)
    for index, source in enumerate(source_items):
        combo.setItemText(index, translate_text(str(source), language))


def _translate_list(list_widget, language: str) -> None:
    source_items = list_widget.property("_deskboard_i18n_items")
    if not isinstance(source_items, list) or len(source_items) != list_widget.count():
        source_items = [list_widget.item(index).text() for index in range(list_widget.count())]
        list_widget.setProperty("_deskboard_i18n_items", source_items)
    for index, source in enumerate(source_items):
        list_widget.item(index).setText(translate_text(str(source), language))


def _translate_tabs(tab_widget, language: str) -> None:
    source_tabs = tab_widget.property("_deskboard_i18n_tabs")
    if not isinstance(source_tabs, list) or len(source_tabs) != tab_widget.count():
        source_tabs = [tab_widget.tabText(index) for index in range(tab_widget.count())]
        tab_widget.setProperty("_deskboard_i18n_tabs", source_tabs)
    for index, source in enumerate(source_tabs):
        tab_widget.setTabText(index, translate_text(str(source), language))


def _translate_table_headers(table, language: str) -> None:
    source_headers = table.property("_deskboard_i18n_headers")
    if not isinstance(source_headers, list) or len(source_headers) != table.columnCount():
        source_headers = [
            table.horizontalHeaderItem(index).text()
            if table.horizontalHeaderItem(index) is not None
            else ""
            for index in range(table.columnCount())
        ]
        table.setProperty("_deskboard_i18n_headers", source_headers)
    for index, source in enumerate(source_headers):
        item = table.horizontalHeaderItem(index)
        if item is not None:
            item.setText(translate_text(str(source), language))
