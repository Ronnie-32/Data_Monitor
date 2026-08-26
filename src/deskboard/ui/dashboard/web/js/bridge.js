export function connectDashboardBridge(onReady) {
  return new QWebChannel(qt.webChannelTransport, (channel) => {
    onReady(channel.objects.bridge);
  });
}

export function subscribeDashboardBridge(bridge, handlers) {
  bridge.stateChanged.connect(handlers.stateChanged);
  bridge.profileChanged.connect(handlers.profileChanged);
  bridge.todosChanged.connect(handlers.todosChanged);
  bridge.agendaChanged.connect(handlers.agendaChanged);
  bridge.weatherChanged.connect(handlers.weatherChanged);
  bridge.financeChanged.connect(handlers.financeChanged);
  bridge.networkStatusChanged.connect(handlers.networkStatusChanged);
  bridge.timetableChanged.connect(handlers.timetableChanged);
  bridge.modeChanged.connect(handlers.modeChanged);
  if (bridge.languageChanged && handlers.languageChanged) {
    bridge.languageChanged.connect(handlers.languageChanged);
  }
}
