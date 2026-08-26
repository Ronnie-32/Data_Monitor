import { connectDashboardBridge, subscribeDashboardBridge } from "./bridge.js";
import {
  applyDashboardLanguage,
  modeLabel,
  normalizeLanguage,
  translate,
} from "./i18n.js";
import { createLayoutController } from "./layout.js";
import { createStore } from "./store.js";
import { createTimetableOverlay } from "./timetable.js";
import { createAgendaWidget } from "./widgets/agenda.js";
import { createFinanceWidget } from "./widgets/finance.js";
import { createWeatherWidget } from "./widgets/weather.js";
import { createTodoWidget } from "./widgets/todo.js";

const store = createStore();
const SUPPORTED_THEMES = new Set([
  "mist_blue",
  "mint_breeze",
  "almond_sand",
  "lavender_cloud",
  "ocean_night",
  "graphite_night",
  "rose_dusk",
  "high_contrast",
  "terra_signal",
  "endfield_industrial",
  "starrail_astral",
  "wuthering_tide",
]);
const FONT_FAMILIES = {
  system_ui: '"Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif',
  yahei: '"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif',
  noto_sans: '"Noto Sans", "Segoe UI", "Microsoft YaHei UI", sans-serif',
  source_han_sans: '"Source Han Sans SC", "Microsoft YaHei UI", sans-serif',
  source_han_serif: '"Source Han Serif SC", "Georgia", "Microsoft YaHei UI", serif',
};

function applyProfileVisuals(profile) {
  const theme = SUPPORTED_THEMES.has(profile?.themeKey) ? profile.themeKey : "mist_blue";
  const fontKey = Object.prototype.hasOwnProperty.call(FONT_FAMILIES, profile?.fontKey)
    ? profile.fontKey
    : "system_ui";
  const opacity = profile?.panelOpacity;
  const normalizedOpacity = typeof opacity === "number"
    && Number.isFinite(opacity)
    && opacity >= 0
    && opacity <= 1
    ? opacity
    : 1;
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.font = fontKey;
  document.documentElement.style.setProperty(
    "--dashboard-font-family",
    FONT_FAMILIES[fontKey],
  );
  document.documentElement.style.setProperty("--panel-opacity", String(normalizedOpacity));
}

function setMode(
  mode,
  todoWidget,
  agendaWidget,
  weatherWidget,
  financeWidgets,
  timetableOverlay,
  layoutController,
  language,
) {
  const currentMode = mode || "interaction";
  document.body.dataset.mode = currentMode;
  document.getElementById("mode").textContent = modeLabel(currentMode, language);
  todoWidget.setMode();
  agendaWidget.setMode();
  weatherWidget.setMode();
  financeWidgets.forEach((widget) => widget.setMode());
  timetableOverlay.setMode(currentMode);
  layoutController.setMode(currentMode);
}

function renderNetworkStatus(status, language) {
  const dot = document.getElementById("network-status-dot");
  if (!dot) return;
  const state = ["grey", "green", "red"].includes(status?.state) ? status.state : "grey";
  const key = state === "green" ? "network.ok" : state === "red" ? "network.error" : "network.checking";
  dot.dataset.state = state;
  dot.title = translate(key, language);
  dot.setAttribute("aria-label", dot.title);
}

function renderState(
  state,
  todoWidget,
  agendaWidget,
  weatherWidget,
  financeWidgets,
  timetableOverlay,
  layoutController,
  languageRef,
) {
  const nextLanguage = normalizeLanguage(state.app?.language);
  if (nextLanguage !== languageRef.value) {
    languageRef.value = nextLanguage;
    applyDashboardLanguage(languageRef.value);
    todoWidget.setLanguage?.(languageRef.value);
    agendaWidget.setLanguage?.(languageRef.value);
    weatherWidget.setLanguage?.(languageRef.value);
    financeWidgets.forEach((widget) => widget.setLanguage?.(languageRef.value));
    timetableOverlay.setLanguage?.(languageRef.value);
    layoutController.setLanguage?.(languageRef.value);
  }
  todoWidget.render(state.todos || []);
  agendaWidget.render(state.agenda || {});
  weatherWidget.render(state.weather || {});
  financeWidgets.forEach((widget) => widget.render(state.finance || {}));
  renderNetworkStatus(state.networkStatus || {}, languageRef.value);
  applyProfileVisuals(state.profile || {});
  layoutController.applyProfile(state.profile || {});
  if (state.app && state.app.mode) {
    setMode(
      state.app.mode,
      todoWidget,
      agendaWidget,
      weatherWidget,
      financeWidgets,
      timetableOverlay,
      layoutController,
      languageRef.value,
    );
  }
}

function syncModeToStore(mode) {
  const currentApp = store.getState().app || {};
  store.merge({ app: { ...currentApp, mode } });
}

function start(bridge) {
  const todoWidget = createTodoWidget(bridge);
  const agendaWidget = createAgendaWidget(bridge);
  const weatherWidget = createWeatherWidget();
  const financeWidgets = ["gold", "fx", "china_indices", "us_indices", "overview"].map(
    (category) => createFinanceWidget(category),
  );
  const timetableOverlay = createTimetableOverlay();
  const layoutController = createLayoutController(bridge);
  const languageRef = { value: "zh_CN" };
  applyDashboardLanguage(languageRef.value);

  store.subscribe((state) =>
    renderState(
      state,
      todoWidget,
      agendaWidget,
      weatherWidget,
      financeWidgets,
      timetableOverlay,
      layoutController,
      languageRef,
    ),
  );
  subscribeDashboardBridge(bridge, {
    stateChanged: (state) => store.replace(state),
    profileChanged: (profile) => store.merge({ profile }),
    todosChanged: (todos) => store.merge({ todos }),
    agendaChanged: (agenda) => store.merge({ agenda }),
    weatherChanged: (weather) => store.merge({ weather }),
    financeChanged: (finance) => store.merge({ finance }),
    networkStatusChanged: (networkStatus) => store.merge({ networkStatus }),
    timetableChanged: (model) => timetableOverlay.render(model),
    modeChanged: syncModeToStore,
    languageChanged: (language) => {
      const currentApp = store.getState().app || {};
      store.merge({ app: { ...currentApp, language } });
    },
  });
  document.getElementById("settings").addEventListener("click", () => {
    bridge.openSettings();
  });

  bridge.requestInitialState();
}

connectDashboardBridge(start);
