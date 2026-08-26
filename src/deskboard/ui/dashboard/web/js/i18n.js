const TEXT = {
  zh_CN: {
    "mode.interaction": "交互",
    "mode.locked": "锁定",
    "mode.layout_edit": "布局编辑",
    "widget.todo": "待办",
    "widget.today_agenda": "今日日程",
    "widget.weather": "天气",
    "widget.gold": "黄金",
    "widget.fx": "汇率",
    "widget.china_indices": "A 股指数",
    "widget.us_indices": "美国指数",
    "widget.finance_overview": "金融总览",
    "layout.title": "布局编辑",
    "layout.hint": "拖卡片移动，拖边缘或角点调整大小",
    "layout.save": "保存",
    "layout.cancel": "取消",
    "shell.settings": "打开设置",
    "shell.drag": "拖动看板",
    "todo.add": "快速添加待办",
    "todo.placeholder": "输入待办内容，按回车保存",
    "todo.content": "待办内容",
    "todo.toggle": "切换待办",
    "todo.empty": "暂无待办",
    "agenda.add": "添加今日日程",
    "agenda.placeholder": "输入今日日程，按回车保存",
    "agenda.content": "今日日程内容",
    "agenda.heading": "今日事项",
    "agenda.empty": "暂无今日日程",
    "agenda.conflict": "时间冲突",
    "menu.edit": "编辑详情",
    "menu.incomplete": "标记未完成",
    "menu.complete": "标记完成",
    "menu.delete": "删除",
    "finance.unknown": "未知项目",
    "finance.noData": "暂无数据",
    "weather.unknownCity": "未知城市",
    "weather.noWeather": "暂无天气",
    "weather.noData": "暂无数据",
    "weather.high": "高",
    "weather.low": "低",
    "weather.windEmpty": "风力暂无数据",
    "network.checking": "网络状态：检查中",
    "network.ok": "网络状态：网络正常",
    "network.error": "网络状态：网络异常",
    "timetable.title": "每周课表",
    "timetable.close": "关闭",
    "timetable.axis": "节次",
    "timetable.empty": "尚未配置有效课表方案，请先到设置中完成配置。",
    "timetable.item": "事项",
    "timetable.conflict": "冲突",
    "aria.todo": "待办数据",
    "aria.agenda": "今日日程数据",
    "aria.weather": "天气数据",
    "aria.gold": "黄金数据",
    "aria.fx": "汇率数据",
    "aria.china_indices": "A 股指数数据",
    "aria.us_indices": "美国指数数据",
    "aria.finance_overview": "金融数据总览",
    "aria.viewport": "看板部件区域",
    "aria.widgets": "看板部件",
  },
  en_US: {
    "mode.interaction": "Interaction",
    "mode.locked": "Locked",
    "mode.layout_edit": "Layout Edit",
    "widget.todo": "Todo",
    "widget.today_agenda": "Today Agenda",
    "widget.weather": "Weather",
    "widget.gold": "Gold",
    "widget.fx": "FX",
    "widget.china_indices": "A-share Indices",
    "widget.us_indices": "U.S. Indices",
    "widget.finance_overview": "Finance Overview",
    "layout.title": "Layout Edit",
    "layout.hint": "Drag cards to move; drag an edge or corner to resize",
    "layout.save": "Save",
    "layout.cancel": "Cancel",
    "shell.settings": "Open Settings",
    "shell.drag": "Drag Dashboard",
    "todo.add": "Quickly add a todo",
    "todo.placeholder": "Enter a todo and press Enter to save",
    "todo.content": "Todo content",
    "todo.toggle": "Toggle todo",
    "todo.empty": "No todos",
    "agenda.add": "Add to today’s agenda",
    "agenda.placeholder": "Enter an agenda item and press Enter to save",
    "agenda.content": "Today’s agenda item",
    "agenda.heading": "Today’s Items",
    "agenda.empty": "No items for today",
    "agenda.conflict": "Time conflict",
    "menu.edit": "Edit details",
    "menu.incomplete": "Mark incomplete",
    "menu.complete": "Mark complete",
    "menu.delete": "Delete",
    "finance.unknown": "Unknown item",
    "finance.noData": "No data",
    "weather.unknownCity": "Unknown city",
    "weather.noWeather": "No weather",
    "weather.noData": "No data",
    "weather.high": "High",
    "weather.low": "Low",
    "weather.windEmpty": "No wind data",
    "network.checking": "Network status: checking",
    "network.ok": "Network status: online",
    "network.error": "Network status: unavailable",
    "timetable.title": "Weekly Timetable",
    "timetable.close": "Close",
    "timetable.axis": "Period",
    "timetable.empty": "No valid timetable scheme is configured. Finish setup in Settings first.",
    "timetable.item": "Item",
    "timetable.conflict": "Conflict",
    "aria.todo": "Todo data",
    "aria.agenda": "Today’s agenda data",
    "aria.weather": "Weather data",
    "aria.gold": "Gold data",
    "aria.fx": "FX data",
    "aria.china_indices": "A-share index data",
    "aria.us_indices": "U.S. index data",
    "aria.finance_overview": "Finance overview data",
    "aria.viewport": "Dashboard widget viewport",
    "aria.widgets": "Dashboard widgets",
  },
};

export function normalizeLanguage(value) {
  return value === "en_US" ? "en_US" : "zh_CN";
}

export function translate(key, language = "zh_CN") {
  const normalized = normalizeLanguage(language);
  return TEXT[normalized][key] || TEXT.en_US[key] || key;
}

export function modeLabel(mode, language = "zh_CN") {
  return translate(`mode.${mode || "interaction"}`, language);
}

export function widgetLabel(widgetKey, language = "zh_CN") {
  return translate(`widget.${widgetKey}`, language);
}

export function applyDashboardLanguage(language = "zh_CN") {
  const normalized = normalizeLanguage(language);
  const documentLanguage = normalized === "en_US" ? "en-US" : "zh-CN";
  document.documentElement.lang = documentLanguage;
  document.body.dataset.language = normalized;

  setText("todo-title", translate("widget.todo", normalized));
  setText("agenda-title", translate("widget.today_agenda", normalized));
  setText("layout-toolbar-title", translate("layout.title", normalized));
  setText("layout-toolbar-hint", translate("layout.hint", normalized));
  setText("layout-save", translate("layout.save", normalized));
  setText("layout-cancel", translate("layout.cancel", normalized));
  setText("settings", translate("shell.settings", normalized));
  setText("timetable-title", translate("timetable.title", normalized));
  setText("timetable-close", translate("timetable.close", normalized));
  setText("agenda-heading", translate("agenda.heading", normalized));

  setAttribute("shell-drag-handle", "aria-label", translate("shell.drag", normalized));
  setAttribute("todo-add", "aria-label", translate("todo.add", normalized));
  setAttribute("todo-add-input", "placeholder", translate("todo.placeholder", normalized));
  setAttribute("todo-add-input", "aria-label", translate("todo.content", normalized));
  setAttribute("agenda-add", "aria-label", translate("agenda.add", normalized));
  setAttribute("agenda-add-input", "placeholder", translate("agenda.placeholder", normalized));
  setAttribute("agenda-add-input", "aria-label", translate("agenda.content", normalized));
  setAttribute("widgets-grid-viewport", "aria-label", translate("aria.viewport", normalized));
  setAttribute("widgets-grid", "aria-label", translate("aria.widgets", normalized));
  setAttribute("timetable-axis", "aria-label", translate("timetable.axis", normalized));

  ["todo", "agenda", "weather", "gold", "fx", "china_indices", "us_indices", "finance_overview"]
    .forEach((key) => {
      const selector = key === "todo"
        ? ".todo-widget"
        : key === "agenda"
          ? ".agenda-widget"
          : key === "weather"
            ? ".weather-widget"
            : `.finance-widget[data-finance-category="${key === "finance_overview" ? "overview" : key}"]`;
      const node = document.querySelector(selector);
      if (node) node.setAttribute("aria-label", translate(`aria.${key}`, normalized));
    });

  const menu = document.getElementById("todo-context-menu");
  if (menu) {
    setMenuText(menu, "edit", translate("menu.edit", normalized));
    setMenuText(menu, "toggle", translate("menu.incomplete", normalized));
    setMenuText(menu, "delete", translate("menu.delete", normalized));
  }
  const dot = document.getElementById("network-status-dot");
  if (dot) {
    const state = dot.dataset.state || "grey";
    const key = state === "green" ? "network.ok" : state === "red" ? "network.error" : "network.checking";
    dot.title = translate(key, normalized);
    dot.setAttribute("aria-label", dot.title);
  }
  return normalized;
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function setAttribute(id, attribute, value) {
  const node = document.getElementById(id);
  if (node) node.setAttribute(attribute, value);
}

function setMenuText(menu, action, value) {
  const button = menu.querySelector(`[data-action="${action}"]`);
  if (button) button.textContent = value;
}
