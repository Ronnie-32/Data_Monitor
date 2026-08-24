function interactionEnabled() {
  return document.body.dataset.mode === "interaction";
}

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

function timeText(item) {
  if (!item.start) return "";
  return item.end ? `${item.start}–${item.end}` : item.start;
}

function renderItem(item) {
  const row = document.createElement("li");
  row.className = "agenda-item";
  if (item.completed) row.classList.add("is-completed");
  if (item.conflict) row.classList.add("is-conflict");

  const time = textNode("span", "agenda-time", timeText(item));
  const body = document.createElement("div");
  body.append(textNode("div", "agenda-content", item.title || ""));
  const meta = document.createElement("div");
  meta.className = "agenda-meta";
  if (item.classroom) meta.append(textNode("span", "agenda-classroom", item.classroom));
  if (item.conflict) meta.append(textNode("span", "agenda-conflict", "时间冲突"));
  if (meta.childElementCount) body.append(meta);
  row.append(time, body);
  return row;
}

function renderList(list, items, emptyText) {
  list.replaceChildren();
  if (!items.length) {
    list.append(textNode("li", "agenda-empty", emptyText));
    return;
  }
  items.forEach((item) => list.append(renderItem(item)));
}

export function createAgendaWidget(bridge) {
  const title = document.getElementById("agenda-title");
  const timedList = document.getElementById("agenda-timed-list");
  const dateOnlyList = document.getElementById("agenda-date-only-list");
  let agenda = { timedItems: [], dateOnlyItems: [] };

  function render(nextAgenda) {
    agenda = nextAgenda || { timedItems: [], dateOnlyItems: [] };
    renderList(timedList, Array.from(agenda.timedItems || []), "暂无定时事项");
    renderList(dateOnlyList, Array.from(agenda.dateOnlyItems || []), "暂无日期事项");
  }

  title.addEventListener("click", () => {
    if (interactionEnabled()) bridge.requestWeeklyTimetable();
  });

  function setMode() {
    title.disabled = !interactionEnabled();
  }

  return { render, setMode };
}
