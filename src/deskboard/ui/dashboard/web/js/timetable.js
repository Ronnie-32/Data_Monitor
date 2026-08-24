const WEEKDAY_COUNT = 7;

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

function parseClock(value) {
  if (typeof value !== "string") return null;
  const match = /^(\d{2}):(\d{2})$/.exec(value);
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (hours > 23 || minutes > 59) return null;
  return hours * 60 + minutes;
}

function validIsoDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    return null;
  }
  return value;
}

function addDays(value, offset) {
  const date = validIsoDate(value);
  if (!date) return null;
  const parsed = new Date(`${date}T00:00:00Z`);
  parsed.setUTCDate(parsed.getUTCDate() + offset);
  return parsed.toISOString().slice(0, 10);
}

function percentage(value, lower, upper) {
  return Math.max(0, Math.min(100, ((value - lower) / (upper - lower)) * 100));
}

function eventGeometry(item, dates, lower, upper) {
  if (!item || !dates.has(item.date)) return null;
  const start = parseClock(item.start);
  if (start === null || upper <= lower) return null;

  const isPoint = item.timeKind === "point" || item.end === null || item.end === undefined;
  if (isPoint) {
    if (start < lower || start > upper) return null;
    return {
      dayIndex: dates.get(item.date),
      top: percentage(start, lower, upper),
      height: 0,
      point: true,
    };
  }

  const end = parseClock(item.end);
  if (end === null || end <= start || end <= lower || start >= upper) return null;
  const visibleStart = Math.max(start, lower);
  const visibleEnd = Math.min(end, upper);
  return {
    dayIndex: dates.get(item.date),
    top: percentage(visibleStart, lower, upper),
    height: Math.max(0.8, percentage(visibleEnd, lower, upper) - percentage(visibleStart, lower, upper)),
    point: false,
  };
}

function renderEvent(item, geometry) {
  const node = document.createElement("article");
  node.className = "timetable-event";
  node.classList.add(item.type === "course" ? "is-course" : "is-todo");
  if (item.completed) node.classList.add("is-completed");
  if (item.conflict) node.classList.add("is-conflict");
  if (geometry.point) node.classList.add("is-point");
  else node.classList.add("is-range");
  node.dataset.eventId = String(item.id ?? "");
  node.style.top = `${geometry.top}%`;
  if (!geometry.point) node.style.height = `${geometry.height}%`;

  node.append(textNode("div", "timetable-event-title", item.title || ""));
  const meta = document.createElement("div");
  meta.className = "timetable-event-meta";
  const timeText = item.end ? `${item.start}–${item.end}` : (item.start || "");
  if (timeText) meta.append(textNode("span", "timetable-event-time", timeText));
  if (item.classroom) meta.append(textNode("span", "timetable-event-classroom", item.classroom));
  if (item.conflict) meta.append(textNode("span", "timetable-event-conflict", "冲突"));
  if (meta.childElementCount) node.append(meta);
  node.setAttribute("aria-label", `${item.title || "事项"} ${timeText}`.trim());
  return node;
}

function renderReferenceLines(axis, days, periods, lower, upper) {
  const axisTrack = document.createElement("div");
  axisTrack.className = "timetable-axis-track";
  axis.replaceChildren(axisTrack);
  days.replaceChildren();

  const dayTracks = [];
  for (let index = 0; index < WEEKDAY_COUNT; index += 1) {
    const column = document.createElement("div");
    column.className = "timetable-day-column";
    const track = document.createElement("div");
    track.className = "timetable-day-track";
    column.append(track);
    days.append(column);
    dayTracks.push(track);
  }

  (Array.isArray(periods) ? periods : []).forEach((period) => {
    const start = parseClock(period.start);
    if (start === null || start < lower || start > upper) return;

    const top = `${percentage(start, lower, upper)}%`;
    const axisMarker = document.createElement("div");
    axisMarker.className = "timetable-axis-marker";
    axisMarker.style.top = top;
    axisMarker.append(textNode("span", "timetable-axis-label", String(period.period)));
    axisTrack.append(axisMarker);

    dayTracks.forEach((track) => {
      const line = document.createElement("div");
      line.className = "timetable-period-line";
      line.style.top = top;
      track.append(line);
    });
  });

  return dayTracks;
}

function renderHeaders(container, headers) {
  container.replaceChildren();
  const values = Array.isArray(headers) ? headers : [];
  for (let index = 0; index < WEEKDAY_COUNT; index += 1) {
    container.append(textNode("div", "timetable-day-header", values[index] || "—"));
  }
}

export function createTimetableOverlay() {
  const overlay = document.getElementById("timetable-overlay");
  const closeButton = document.getElementById("timetable-close");
  const weekLabel = document.getElementById("timetable-week-label");
  const ready = document.getElementById("timetable-ready");
  const empty = document.getElementById("timetable-empty");
  const headers = document.getElementById("timetable-headers");
  const axis = document.getElementById("timetable-axis");
  const days = document.getElementById("timetable-days");
  let mode = "interaction";
  let currentModel = null;

  function close() {
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
  }

  function open() {
    if (mode !== "interaction") return;
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
  }

  function render(model) {
    currentModel = model || null;
    if (!currentModel) return;
    weekLabel.textContent = currentModel.weekLabel || "";
    const lower = parseClock(currentModel.visibleStart);
    const upper = parseClock(currentModel.visibleEnd);
    const dates = new Map();
    const weekStart = validIsoDate(currentModel.weekStart);
    if (weekStart) {
      for (let index = 0; index < WEEKDAY_COUNT; index += 1) {
        const day = addDays(weekStart, index);
        if (day) dates.set(day, index);
      }
    }

    const needsConfiguration = Boolean(currentModel.configurationRequired)
      || lower === null
      || upper === null
      || upper <= lower
      || dates.size !== WEEKDAY_COUNT;
    ready.hidden = needsConfiguration;
    empty.hidden = !needsConfiguration;
    if (needsConfiguration) {
      empty.textContent = "尚未配置 1–8 节课时，请先到设置中完成配置。";
      axis.replaceChildren();
      days.replaceChildren();
      open();
      return;
    }

    renderHeaders(headers, currentModel.headers);
    const dayTracks = renderReferenceLines(
      axis,
      days,
      currentModel.periods,
      lower,
      upper,
    );
    (Array.isArray(currentModel.events) ? currentModel.events : []).forEach((item) => {
      const geometry = eventGeometry(item, dates, lower, upper);
      if (!geometry || !dayTracks[geometry.dayIndex]) return;
      dayTracks[geometry.dayIndex].append(renderEvent(item, geometry));
    });
    open();
  }

  closeButton.addEventListener("click", close);

  function setMode(nextMode) {
    mode = nextMode || "interaction";
    if (mode !== "interaction") close();
  }

  close();
  return { render, setMode, close, get currentModel() { return currentModel; } };
}
