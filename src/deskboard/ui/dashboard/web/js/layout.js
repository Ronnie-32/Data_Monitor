import { normalizeLanguage, widgetLabel } from "./i18n.js";

const GRID_COLUMNS = 48;
export const LAYOUT_EDGE_PADDING_PX = 0;
export const LAYOUT_HORIZONTAL_GAP_PX = 2;
export const LAYOUT_VERTICAL_GAP_PX = 2;
const MIN_CELL_HEIGHT_PX = 20;
const MAX_CELL_HEIGHT_PX = 32;
const MAX_INFO_WIDGET_ROWS = 3;
const WIDGET_LABELS = {
  todo: "待办",
  today_agenda: "今日日程",
  weather: "天气",
  gold: "黄金",
  fx: "汇率",
  china_indices: "A 股指数",
  us_indices: "美国指数",
  finance_overview: "金融总览",
};

const FALLBACK_LAYOUT = [
  { widgetKey: "todo", visible: true, x: 0, y: 0, w: 24, h: 12 },
  { widgetKey: "today_agenda", visible: true, x: 24, y: 0, w: 24, h: 12 },
  { widgetKey: "weather", visible: true, x: 0, y: 12, w: 48, h: 3 },
  { widgetKey: "gold", visible: true, x: 0, y: 15, w: 12, h: 3 },
  { widgetKey: "fx", visible: true, x: 12, y: 15, w: 12, h: 3 },
  { widgetKey: "china_indices", visible: true, x: 24, y: 15, w: 12, h: 3 },
  { widgetKey: "us_indices", visible: true, x: 36, y: 15, w: 12, h: 3 },
  { widgetKey: "finance_overview", visible: false, x: 0, y: 18, w: 48, h: 3 },
];

export function computePreferredCellHeight(containerWidth, columns = GRID_COLUMNS) {
  const width = Number(containerWidth);
  const columnCount = Math.max(1, integerValue(columns, GRID_COLUMNS));
  if (!Number.isFinite(width) || width <= 0) return MIN_CELL_HEIGHT_PX;
  const preferred = Math.round((width / columnCount) * 0.9);
  return Math.min(MAX_CELL_HEIGHT_PX, Math.max(MIN_CELL_HEIGHT_PX, preferred));
}

export function clampGridItemToBoard(item, maxRows = 0, columns = GRID_COLUMNS) {
  const rowLimit = Math.max(0, integerValue(maxRows, 0));
  const columnLimit = Math.max(1, integerValue(columns, GRID_COLUMNS));
  const w = Math.min(columnLimit, Math.max(1, integerValue(item?.w, 1)));
  const rawHeight = Math.max(1, integerValue(item?.h, 1));
  const h = rowLimit > 0 ? Math.min(rowLimit, rawHeight) : rawHeight;
  const x = Math.min(columnLimit - w, Math.max(0, integerValue(item?.x, 0)));
  const rawY = Math.max(0, integerValue(item?.y, 0));
  const y = rowLimit > 0 ? Math.min(rowLimit - h, rawY) : rawY;
  return { x, y, w, h };
}

function integerValue(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.trunc(number) : fallback;
}

export function createLayoutController(bridge) {
  const gridElement = document.getElementById("widgets-grid");
  const gridViewport = document.getElementById("widgets-grid-viewport");
  const toolbar = document.getElementById("layout-toolbar");
  const visibilityControls = document.getElementById("layout-visibility-controls");
  const saveButton = document.getElementById("layout-save");
  const cancelButton = document.getElementById("layout-cancel");

  const grid = window.GridStack.init(
    {
      column: GRID_COLUMNS,
      // Preserve intentional blank space and the user's x/y choice. The
      // collision engine still pushes an intersecting card out of the way.
      float: true,
      push: true,
      pushResize: true,
      alwaysShowResizeHandle: true,
      resizable: { handles: "n,e,s,w,ne,se,sw,nw" },
      maxRow: 0,
      disableOneColumnMode: true,
      animate: false,
      margin: LAYOUT_EDGE_PADDING_PX,
      cellHeight: 24,
    },
    gridElement,
  );
  gridElement.dataset.columns = String(GRID_COLUMNS);

  function applyHorizontalGap() {
    const horizontalGap = `${LAYOUT_HORIZONTAL_GAP_PX}px`;
    const verticalGap = `${LAYOUT_VERTICAL_GAP_PX}px`;
    gridElement.style.setProperty("--gs-item-margin-top", verticalGap);
    gridElement.style.setProperty("--gs-item-margin-bottom", verticalGap);
    gridElement.style.setProperty("--gs-item-margin-left", horizontalGap);
    gridElement.style.setProperty("--gs-item-margin-right", horizontalGap);
  }

  applyHorizontalGap();

  let editing = false;
  let profile = null;
  let language = "zh_CN";

  function installWindowDrag() {
    toolbar?.addEventListener("pointerdown", (event) => {
      if (!editing || event.button !== 0) return;
      const target = event.target;
      if (
        target
        && typeof target.closest === "function"
        && target.closest("button, input, label, select, textarea, a")
      ) return;
      if (typeof bridge.beginWindowDrag !== "function") return;
      event.preventDefault();
      bridge.beginWindowDrag(Math.trunc(event.screenX), Math.trunc(event.screenY));
    });
  }

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

  function nodesOverlap(left, right) {
    return (
      left.x < right.x + right.w
      && left.x + left.w > right.x
      && left.y < right.y + right.h
      && left.y + left.h > right.y
    );
  }

  function repairOverlappingNodes() {
    const nodes = grid.engine?.nodes || [];
    const maxPasses = Math.max(1, nodes.length * nodes.length);
    for (let pass = 0; pass < maxPasses; pass += 1) {
      let repaired = false;
      for (let index = 0; index < nodes.length; index += 1) {
        for (let other = index + 1; other < nodes.length; other += 1) {
          const left = nodes[index];
          const right = nodes[other];
          if (!nodesOverlap(left, right)) continue;

          // Preserve the user's horizontal choice. Only move the later
          // colliding item down, instead of globally reflowing the board.
          const moving = left.y > right.y
            || (left.y === right.y && left.x > right.x)
            ? left
            : right;
          const anchor = moving === left ? right : left;
          grid.update(moving.el, {
            x: moving.x,
            y: Math.max(moving.y, anchor.y + anchor.h),
            w: moving.w,
            h: moving.h,
          });
          repaired = true;
          break;
        }
        if (repaired) break;
      }
      if (!repaired) return;
    }
  }

  function fitInformationWidgets() {
    if (!grid.engine || !gridElement.clientWidth) return;
    const cellHeight = Number(grid.getCellHeight?.(true));
    if (!Number.isFinite(cellHeight) || cellHeight <= 0) return;

    const requestedSizes = [];
    items().forEach((item) => {
      if (!item.querySelector(".info-widget")) return;
      const list = item.querySelector(".weather-cities, .finance-items");
      const node = item.gridstackNode;
      if (!list || !node || item.classList.contains("layout-item-hidden")) return;
      const contentHeight = Number(list.scrollHeight || 0);
      if (!Number.isFinite(contentHeight) || contentHeight <= 0) return;
      const requiredRows = Math.min(
        MAX_INFO_WIDGET_ROWS,
        Math.max(1, Math.ceil((contentHeight + LAYOUT_VERTICAL_GAP_PX * 2) / cellHeight)),
      );
      if (requiredRows > node.h) {
        requestedSizes.push({ item, node, requiredRows });
      }
    });
    if (!requestedSizes.length) {
      syncVisibleGridHeight();
      return;
    }

    grid.batchUpdate();
    requestedSizes.forEach(({ item, node, requiredRows }) => {
      grid.update(item, {
        x: node.x,
        y: node.y,
        w: node.w,
        h: requiredRows,
      });
    });
    grid.batchUpdate(false);
    repairOverlappingNodes();
    syncVisibleGridHeight();
  }

  function applyProfile(nextProfile) {
    profile = nextProfile || {};
    const states = new Map(
      (profile.widgets || []).map((item) => [item.widgetKey || item.widget_key, item]),
    );
    updateCellHeight();
    grid.batchUpdate();
    items().forEach((item) => {
      const state = stateFor(widgetKey(item), states);
      const geometry = clampGridItemToBoard(state);
      grid.update(item, geometry);
      applyVisible(item, state.visible !== false);
    });
    grid.batchUpdate(false);
    repairOverlappingNodes();
    updateGridBounds();
    fitInformationWidgets();
    syncVisibleGridHeight();
    renderVisibilityControls();
  }

  function snapshot() {
    return {
      columnCount: GRID_COLUMNS,
      widgets: items().map((item) => {
        const node = item.gridstackNode || {};
        const geometry = clampGridItemToBoard({
          x: node.x ?? item.getAttribute("gs-x") ?? 0,
          y: node.y ?? item.getAttribute("gs-y") ?? 0,
          w: node.w ?? item.getAttribute("gs-w") ?? 1,
          h: node.h ?? item.getAttribute("gs-h") ?? 1,
        });
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
      checkbox.addEventListener("change", () => {
        applyVisible(item, checkbox.checked);
        fitInformationWidgets();
        syncVisibleGridHeight();
      });
      const key = widgetKey(item);
      label.append(
        checkbox,
        document.createTextNode(widgetLabel(key, language) || WIDGET_LABELS[key] || key),
      );
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
    syncVisibleGridHeight();
    document.body.dataset.layoutEditing = editing ? "true" : "false";
    renderVisibilityControls();
  }

  function setLanguage(nextLanguage) {
    language = normalizeLanguage(nextLanguage);
    renderVisibilityControls();
  }

  function updateCellHeight() {
    if (!gridElement.clientWidth || typeof grid.cellHeight !== "function") return;
    const cellHeight = computePreferredCellHeight(gridElement.clientWidth);
    const currentCellHeight = Number(grid.getCellHeight?.(true));
    if (!Number.isFinite(currentCellHeight) || Math.abs(currentCellHeight - cellHeight) > 0.5) {
      grid.cellHeight(cellHeight);
    }
    applyHorizontalGap();
    syncVisibleGridHeight();
  }

  function updateGridBounds() {
    if (!grid.engine) return;
    grid.opts.maxRow = 0;
    grid.engine.maxRow = 0;
    grid.batchUpdate();
    grid.engine.nodes.forEach((node) => {
      const bounded = clampGridItemToBoard(node);
      if (node.x !== bounded.x || node.y !== bounded.y || node.w !== bounded.w || node.h !== bounded.h) {
        grid.update(node.el, bounded);
      }
    });
    grid.batchUpdate(false);
  }

  function syncVisibleGridHeight() {
    if (!grid.engine) return;
    const cellHeight = Number(grid.getCellHeight?.(true));
    if (!Number.isFinite(cellHeight) || cellHeight <= 0) return;
    const visibleNodes = grid.engine.nodes.filter(
      (node) => !node.el?.classList.contains("layout-item-hidden"),
    );
    const rowCount = visibleNodes.reduce(
      (maximum, node) => Math.max(maximum, node.y + node.h),
      0,
    );
    gridElement.style.height = rowCount > 0 ? `${rowCount * cellHeight}px` : "0px";
  }

  grid.on("change", () => {
    // Dragging is render-only. Python receives one complete snapshot on Save.
  });
  function finishGridInteraction() {
    repairOverlappingNodes();
    updateGridBounds();
    updateCellHeight();
    fitInformationWidgets();
    syncVisibleGridHeight();
  }
  grid.on("dragstop", finishGridInteraction);
  grid.on("resizestop", finishGridInteraction);
  saveButton?.addEventListener("click", () => {
    if (editing) bridge.saveLayout(snapshot());
  });
  cancelButton?.addEventListener("click", () => {
    if (editing) bridge.cancelLayoutEdit();
  });
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(() => {
      updateCellHeight();
      fitInformationWidgets();
      syncVisibleGridHeight();
    }).observe(gridViewport || gridElement);
  }

  installWindowDrag();

  return {
    applyProfile,
    setMode,
    setLanguage,
    snapshot,
    getProfile: () => profile,
  };
}
