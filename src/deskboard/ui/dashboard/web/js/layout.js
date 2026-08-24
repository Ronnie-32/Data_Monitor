const GRID_COLUMNS = 12;
export const LAYOUT_EDGE_PADDING_PX = 0;
export const LAYOUT_HORIZONTAL_GAP_PX = 4;
const MIN_CELL_HEIGHT_PX = 48;

const FALLBACK_LAYOUT = [
  { widgetKey: "todo", visible: true, x: 1, y: 0, w: 5, h: 6 },
  { widgetKey: "today_agenda", visible: true, x: 6, y: 0, w: 5, h: 6 },
  { widgetKey: "weather", visible: true, x: 1, y: 6, w: 10, h: 3 },
];

export function computeMaxRows(containerHeight, cellHeight) {
  const height = Number(containerHeight);
  const cell = Number(cellHeight);
  if (!Number.isFinite(height) || !Number.isFinite(cell) || cell <= 0) return 1;
  return Math.max(1, Math.floor(Math.max(0, height) / cell));
}

export function computeGridMetrics(containerHeight, preferredCellHeight, requiredRows = 1) {
  const height = Number(containerHeight);
  const preferred = Number(preferredCellHeight);
  if (!Number.isFinite(height) || height <= 0) {
    return { maxRows: 1, cellHeight: 1 };
  }
  requiredRows = Math.max(1, integerValue(requiredRows, 1));
  if (!Number.isFinite(preferred) || preferred <= 0) {
    return { maxRows: requiredRows, cellHeight: height / requiredRows };
  }
  const naturalRows = computeMaxRows(height, preferred);
  const maxRows = Math.max(naturalRows, requiredRows);
  return { maxRows, cellHeight: height / maxRows };
}

export function clampGridItemToBoard(item, maxRows, columns = GRID_COLUMNS) {
  const rowLimit = Math.max(1, integerValue(maxRows, 1));
  const columnLimit = Math.max(1, integerValue(columns, GRID_COLUMNS));
  const w = Math.min(columnLimit, Math.max(1, integerValue(item?.w, 1)));
  const h = Math.min(rowLimit, Math.max(1, integerValue(item?.h, 1)));
  const x = Math.min(columnLimit - w, Math.max(0, integerValue(item?.x, 0)));
  const y = Math.min(rowLimit - h, Math.max(0, integerValue(item?.y, 0)));
  return { x, y, w, h };
}

function integerValue(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.trunc(number) : fallback;
}

export function createLayoutController(bridge) {
  const gridElement = document.getElementById("widgets-grid");
  const toolbar = document.getElementById("layout-toolbar");
  const visibilityControls = document.getElementById("layout-visibility-controls");
  const saveButton = document.getElementById("layout-save");
  const cancelButton = document.getElementById("layout-cancel");

  const grid = window.GridStack.init(
    {
      column: 12,
      float: true,
      disableOneColumnMode: true,
      animate: false,
      margin: LAYOUT_EDGE_PADDING_PX,
      cellHeight: 72,
    },
    gridElement,
  );
  gridElement.dataset.columns = String(GRID_COLUMNS);

  function applyHorizontalGap() {
    const gap = `${LAYOUT_HORIZONTAL_GAP_PX}px`;
    gridElement.style.setProperty("--gs-item-margin-top", "0px");
    gridElement.style.setProperty("--gs-item-margin-bottom", "0px");
    gridElement.style.setProperty("--gs-item-margin-left", gap);
    gridElement.style.setProperty("--gs-item-margin-right", gap);
  }

  applyHorizontalGap();

  let editing = false;
  let profile = null;
  let boardRowCount = 1;

  function items() {
    return Array.from(gridElement.querySelectorAll(".grid-stack-item"));
  }

  function widgetKey(item) {
    return item.dataset.widgetKey;
  }

  function stateFor(key, states) {
    return states.get(key) || FALLBACK_LAYOUT.find((item) => item.widgetKey === key) || {
      widgetKey: key,
      visible: true,
      x: 0,
      y: 0,
      w: 1,
      h: 1,
    };
  }

  function applyVisible(item, visible) {
    item.classList.toggle("layout-item-hidden", visible === false);
    item.setAttribute("aria-hidden", visible === false ? "true" : "false");
  }

  function bottomRow(item) {
    return Math.max(0, integerValue(item?.y, 0)) + Math.max(1, integerValue(item?.h, 1));
  }

  function currentContentRows() {
    const nodes = grid.engine?.nodes || [];
    return Math.max(1, ...nodes.map(bottomRow));
  }

  function stateContentRows(states) {
    return Math.max(1, ...Array.from(states.values()).map(bottomRow));
  }

  function applyProfile(nextProfile) {
    profile = nextProfile || {};
    const states = new Map(
      (profile.widgets || []).map((item) => [item.widgetKey || item.widget_key, item]),
    );
    updateCellHeight(stateContentRows(states));
    grid.batchUpdate();
    items().forEach((item) => {
      const state = stateFor(widgetKey(item), states);
      const geometry = clampGridItemToBoard(state, currentMaxRows());
      grid.update(item, geometry);
      applyVisible(item, state.visible !== false);
    });
    grid.batchUpdate(false);
    renderVisibilityControls();
  }

  function snapshot() {
    const maxRows = currentMaxRows();
    return {
      columnCount: GRID_COLUMNS,
      widgets: items().map((item) => {
        const node = item.gridstackNode || {};
        const geometry = clampGridItemToBoard({
          x: node.x ?? item.getAttribute("gs-x") ?? 0,
          y: node.y ?? item.getAttribute("gs-y") ?? 0,
          w: node.w ?? item.getAttribute("gs-w") ?? 1,
          h: node.h ?? item.getAttribute("gs-h") ?? 1,
        }, maxRows);
        return {
          widgetKey: widgetKey(item),
          visible: !item.classList.contains("layout-item-hidden"),
          ...geometry,
        };
      }),
    };
  }

  function renderVisibilityControls() {
    if (!visibilityControls) return;
    visibilityControls.replaceChildren();
    if (!editing) return;
    items().forEach((item) => {
      const label = document.createElement("label");
      label.className = "layout-visibility-label";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !item.classList.contains("layout-item-hidden");
      checkbox.addEventListener("change", () => applyVisible(item, checkbox.checked));
      label.append(checkbox, document.createTextNode(widgetKey(item)));
      visibilityControls.append(label);
    });
  }

  function setMode(mode) {
    editing = mode === "layout_edit";
    if (toolbar) toolbar.hidden = !editing;
    updateCellHeight();
    if (editing) {
      grid.enable();
    } else {
      grid.disable();
    }
    document.body.dataset.layoutEditing = editing ? "true" : "false";
    renderVisibilityControls();
  }

  function updateCellHeight(requiredRows = 1) {
    if (!gridElement.clientWidth || typeof grid.cellHeight !== "function") return;
    const cellHeight = Math.max(
      MIN_CELL_HEIGHT_PX,
      Math.round((gridElement.clientWidth / GRID_COLUMNS) * 0.72),
    );
    const metrics = computeGridMetrics(
      gridElement.clientHeight,
      cellHeight,
      Math.max(boardRowCount, requiredRows, currentContentRows()),
    );
    boardRowCount = metrics.maxRows;
    grid.cellHeight(metrics.cellHeight);
    applyHorizontalGap();
    updateGridBounds(metrics.maxRows);
  }

  function currentMaxRows() {
    if (!gridElement.clientHeight) {
      return integerValue(grid.engine?.maxRow ?? grid.opts?.maxRow, 1);
    }
    return Math.max(boardRowCount, currentContentRows());
  }

  function updateGridBounds(maxRows = currentMaxRows()) {
    if (!gridElement.clientHeight || !grid.engine) return;
    grid.opts.maxRow = maxRows;
    grid.engine.maxRow = maxRows;
    grid.batchUpdate();
    grid.engine.nodes.forEach((node) => {
      const bounded = clampGridItemToBoard(node, maxRows);
      if (node.x !== bounded.x || node.y !== bounded.y || node.w !== bounded.w || node.h !== bounded.h) {
        grid.update(node.el, bounded);
      }
    });
    grid.batchUpdate(false);
  }

  grid.on("change", () => {
    const contentRows = currentContentRows();
    if (contentRows > boardRowCount) {
      boardRowCount = contentRows;
      updateCellHeight(contentRows);
    }
    // Dragging is render-only. Python receives one complete snapshot on Save.
  });
  saveButton?.addEventListener("click", () => {
    if (editing) bridge.saveLayout(snapshot());
  });
  cancelButton?.addEventListener("click", () => {
    if (editing) bridge.cancelLayoutEdit();
  });
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(updateCellHeight).observe(gridElement);
  }

  return {
    applyProfile,
    setMode,
    snapshot,
    getProfile: () => profile,
  };
}
