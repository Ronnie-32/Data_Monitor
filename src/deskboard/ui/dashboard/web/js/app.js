import { connectDashboardBridge, subscribeDashboardBridge } from "./bridge.js";
import { createLayoutController } from "./layout.js";
import { createStore } from "./store.js";
import { createTimetableOverlay } from "./timetable.js";
import { createAgendaWidget } from "./widgets/agenda.js";
import { createTodoWidget } from "./widgets/todo.js";

const store = createStore();

function setMode(mode, todoWidget, agendaWidget, timetableOverlay, layoutController) {
  const currentMode = mode || "interaction";
  document.body.dataset.mode = currentMode;
  document.getElementById("mode").textContent = currentMode;
  todoWidget.setMode();
  agendaWidget.setMode();
  timetableOverlay.setMode(currentMode);
  layoutController.setMode(currentMode);
}

function renderState(state, todoWidget, agendaWidget, timetableOverlay, layoutController) {
  todoWidget.render(state.todos || []);
  agendaWidget.render(state.agenda || {});
  layoutController.applyProfile(state.profile || {});
  if (state.app && state.app.mode) {
    setMode(state.app.mode, todoWidget, agendaWidget, timetableOverlay, layoutController);
  }
}

function start(bridge) {
  const todoWidget = createTodoWidget(bridge);
  const agendaWidget = createAgendaWidget(bridge);
  const timetableOverlay = createTimetableOverlay();
  const layoutController = createLayoutController(bridge);

  store.subscribe((state) =>
    renderState(state, todoWidget, agendaWidget, timetableOverlay, layoutController),
  );
  subscribeDashboardBridge(bridge, {
    stateChanged: (state) => store.replace(state),
    profileChanged: (profile) => store.merge({ profile }),
    todosChanged: (todos) => store.merge({ todos }),
    agendaChanged: (agenda) => store.merge({ agenda }),
    timetableChanged: (model) => timetableOverlay.render(model),
    modeChanged: (mode) =>
      setMode(mode, todoWidget, agendaWidget, timetableOverlay, layoutController),
  });
  document.getElementById("settings").addEventListener("click", () => {
    bridge.openSettings();
  });

  bridge.requestInitialState();
}

connectDashboardBridge(start);
