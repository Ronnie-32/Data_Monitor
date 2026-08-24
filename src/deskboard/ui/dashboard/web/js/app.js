import { connectDashboardBridge, subscribeDashboardBridge } from "./bridge.js";
import { createLayoutController } from "./layout.js";
import { createStore } from "./store.js";
import { createTimetableOverlay } from "./timetable.js";
import { createAgendaWidget } from "./widgets/agenda.js";
import { createWeatherWidget } from "./widgets/weather.js";
import { createTodoWidget } from "./widgets/todo.js";

const store = createStore();

function setMode(mode, todoWidget, agendaWidget, weatherWidget, timetableOverlay, layoutController) {
  const currentMode = mode || "interaction";
  document.body.dataset.mode = currentMode;
  document.getElementById("mode").textContent = currentMode;
  todoWidget.setMode();
  agendaWidget.setMode();
  weatherWidget.setMode();
  timetableOverlay.setMode(currentMode);
  layoutController.setMode(currentMode);
}

function renderNetworkStatus(status) {
  const dot = document.getElementById("network-status-dot");
  if (!dot) return;
  const states = { grey: "检查中", green: "网络正常", red: "网络异常" };
  const state = ["grey", "green", "red"].includes(status?.state) ? status.state : "grey";
  dot.dataset.state = state;
  dot.title = `网络状态：${states[state]}`;
  dot.setAttribute("aria-label", dot.title);
}

function renderState(state, todoWidget, agendaWidget, weatherWidget, timetableOverlay, layoutController) {
  todoWidget.render(state.todos || []);
  agendaWidget.render(state.agenda || {});
  weatherWidget.render(state.weather || {});
  renderNetworkStatus(state.networkStatus || {});
  layoutController.applyProfile(state.profile || {});
  if (state.app && state.app.mode) {
    setMode(state.app.mode, todoWidget, agendaWidget, weatherWidget, timetableOverlay, layoutController);
  }
}

function start(bridge) {
  const todoWidget = createTodoWidget(bridge);
  const agendaWidget = createAgendaWidget(bridge);
  const weatherWidget = createWeatherWidget();
  const timetableOverlay = createTimetableOverlay();
  const layoutController = createLayoutController(bridge);

  store.subscribe((state) =>
    renderState(state, todoWidget, agendaWidget, weatherWidget, timetableOverlay, layoutController),
  );
  subscribeDashboardBridge(bridge, {
    stateChanged: (state) => store.replace(state),
    profileChanged: (profile) => store.merge({ profile }),
    todosChanged: (todos) => store.merge({ todos }),
    agendaChanged: (agenda) => store.merge({ agenda }),
    weatherChanged: (weather) => store.merge({ weather }),
    networkStatusChanged: (networkStatus) => store.merge({ networkStatus }),
    timetableChanged: (model) => timetableOverlay.render(model),
    modeChanged: (mode) =>
      setMode(mode, todoWidget, agendaWidget, weatherWidget, timetableOverlay, layoutController),
  });
  document.getElementById("settings").addEventListener("click", () => {
    bridge.openSettings();
  });

  bridge.requestInitialState();
}

connectDashboardBridge(start);
