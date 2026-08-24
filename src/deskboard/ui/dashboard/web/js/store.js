const EMPTY_STATE = {
  app: {},
  profile: {},
  widgets: {},
  todos: [],
  agenda: { timedItems: [], dateOnlyItems: [] },
  weather: {},
  finance: {},
  networkStatus: {},
};

export function createStore(initialState = EMPTY_STATE) {
  let state = initialState;
  const listeners = new Set();

  function notify() {
    listeners.forEach((listener) => listener(state));
  }

  return {
    getState() {
      return state;
    },
    replace(nextState) {
      state = nextState || EMPTY_STATE;
      notify();
    },
    merge(patch) {
      state = { ...state, ...patch };
      notify();
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
