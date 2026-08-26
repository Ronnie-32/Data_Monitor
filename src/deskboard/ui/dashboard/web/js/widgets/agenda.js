import { normalizeLanguage, translate } from "../i18n.js";

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

function renderItem(item, language) {
  const row = document.createElement("li");
  row.className = "agenda-item";
  if (item.completed) row.classList.add("is-completed");
  if (item.conflict) row.classList.add("is-conflict");

  const body = document.createElement("div");
  const titleLine = document.createElement("div");
  titleLine.className = "agenda-content";
  titleLine.append(textNode("span", "agenda-title-text", item.title || ""));
  const time = timeText(item);
  if (time) titleLine.append(textNode("time", "agenda-inline-time", time));
  body.append(titleLine);
  const meta = document.createElement("div");
  meta.className = "agenda-meta";
  if (item.classroom) meta.append(textNode("span", "agenda-classroom", item.classroom));
  if (item.conflict) {
    meta.append(textNode("span", "agenda-conflict", translate("agenda.conflict", language)));
  }
  if (meta.childElementCount) body.append(meta);
  row.append(body);
  return row;
}

function renderList(list, items, emptyText, language) {
  list.replaceChildren();
  if (!items.length) {
    list.append(textNode("li", "agenda-empty", emptyText));
    return;
  }
  items.forEach((item) => list.append(renderItem(item, language)));
}

export function createAgendaWidget(bridge) {
  const title = document.getElementById("agenda-title");
  const addButton = document.getElementById("agenda-add");
  const addForm = document.getElementById("agenda-add-form");
  const addInput = document.getElementById("agenda-add-input");
  const list = document.getElementById("agenda-list");
  let agenda = { timedItems: [], dateOnlyItems: [] };
  let language = "zh_CN";

  function applyLanguage() {
    title.textContent = translate("widget.today_agenda", language);
    addButton.setAttribute("aria-label", translate("agenda.add", language));
    addInput.placeholder = translate("agenda.placeholder", language);
    addInput.setAttribute("aria-label", translate("agenda.content", language));
    const heading = document.getElementById("agenda-heading");
    if (heading) heading.textContent = translate("agenda.heading", language);
  }

  function render(nextAgenda) {
    agenda = nextAgenda || { timedItems: [], dateOnlyItems: [] };
    const items = [
      ...Array.from(agenda.timedItems || []),
      ...Array.from(agenda.dateOnlyItems || []),
    ];
    renderList(list, items, translate("agenda.empty", language), language);
  }

  title.addEventListener("click", () => {
    if (interactionEnabled()) bridge.requestWeeklyTimetable();
  });

  addButton.addEventListener("click", () => {
    if (!interactionEnabled()) return;
    addForm.classList.toggle("is-open");
    if (addForm.classList.contains("is-open")) addInput.focus();
  });
  addForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const content = addInput.value.trim();
    if (!interactionEnabled() || !content) return;
    bridge.addTodayTodo(content);
    addInput.value = "";
    addForm.classList.remove("is-open");
  });

  function setMode() {
    title.disabled = !interactionEnabled();
    addButton.disabled = !interactionEnabled();
    addForm.classList.remove("is-open");
  }

  function setLanguage(nextLanguage) {
    language = normalizeLanguage(nextLanguage);
    applyLanguage();
    render(agenda);
  }

  applyLanguage();
  return { render, setMode, setLanguage };
}
