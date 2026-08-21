function interactionEnabled() {
  return document.body.dataset.mode === "interaction";
}

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

export function createTodoWidget(bridge) {
  const list = document.getElementById("todo-list");
  const addButton = document.getElementById("todo-add");
  const addForm = document.getElementById("todo-add-form");
  const addInput = document.getElementById("todo-add-input");
  const menu = document.getElementById("todo-context-menu");
  let items = [];
  let contextTodo = null;
  let draggedId = null;

  function closeMenu() {
    menu.classList.remove("is-open");
    contextTodo = null;
  }

  function render(nextItems) {
    items = Array.from(nextItems || []);
    list.replaceChildren();
    if (items.length === 0) {
      list.append(textNode("li", "todo-empty", "暂无待办"));
      return;
    }

    items.forEach((todo) => {
      const row = document.createElement("li");
      row.className = `todo-item${todo.completed ? " is-completed" : ""}`;
      row.dataset.todoId = String(todo.id);
      row.draggable = interactionEnabled();

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "todo-check";
      checkbox.checked = Boolean(todo.completed);
      checkbox.disabled = !interactionEnabled();
      checkbox.setAttribute("aria-label", `切换待办：${todo.content}`);
      checkbox.addEventListener("change", () => {
        if (interactionEnabled()) bridge.toggleTodo(todo.id);
      });

      const body = document.createElement("div");
      body.append(textNode("div", "todo-content", todo.content));
      const meta = document.createElement("div");
      meta.className = "todo-meta";
      if (todo.deadlineText) {
        const deadline = textNode("span", "todo-deadline", todo.deadlineText);
        if (todo.overdue) deadline.classList.add("is-overdue");
        meta.append(deadline);
      }
      if (todo.plannedText) meta.append(textNode("span", "todo-planned", todo.plannedText));
      body.append(meta);
      row.append(checkbox, body);

      row.addEventListener("contextmenu", (event) => {
        if (!interactionEnabled()) return;
        event.preventDefault();
        contextTodo = todo;
        menu.querySelector('[data-action="toggle"]').textContent = todo.completed
          ? "Mark incomplete"
          : "Mark complete";
        menu.style.left = `${event.clientX}px`;
        menu.style.top = `${event.clientY}px`;
        menu.classList.add("is-open");
      });
      row.addEventListener("dragstart", () => {
        if (!interactionEnabled()) return;
        draggedId = todo.id;
        row.classList.add("is-dragging");
      });
      row.addEventListener("dragend", () => {
        draggedId = null;
        row.classList.remove("is-dragging");
      });
      row.addEventListener("dragover", (event) => {
        if (interactionEnabled() && draggedId !== null) event.preventDefault();
      });
      row.addEventListener("drop", (event) => {
        if (!interactionEnabled() || draggedId === null || draggedId === todo.id) return;
        event.preventDefault();
        const orderedIds = items.map((item) => item.id);
        const from = orderedIds.indexOf(draggedId);
        const to = orderedIds.indexOf(todo.id);
        orderedIds.splice(to, 0, orderedIds.splice(from, 1)[0]);
        bridge.reorderTodos(orderedIds);
      });
      list.append(row);
    });
  }

  addButton.addEventListener("click", () => {
    if (!interactionEnabled()) return;
    addForm.classList.toggle("is-open");
    if (addForm.classList.contains("is-open")) addInput.focus();
  });
  addForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const content = addInput.value.trim();
    if (!interactionEnabled() || !content) return;
    bridge.addQuickTodo(content);
    addInput.value = "";
    addForm.classList.remove("is-open");
  });
  menu.addEventListener("click", (event) => {
    const action = event.target.closest("button")?.dataset.action;
    if (!interactionEnabled() || !contextTodo || !action) return;
    if (action === "toggle") bridge.toggleTodo(contextTodo.id);
    if (action === "edit") {
      window.dispatchEvent(new CustomEvent("todo-editor-requested", { detail: contextTodo.id }));
    }
    if (action === "delete") {
      window.dispatchEvent(new CustomEvent("todo-delete-requested", { detail: contextTodo.id }));
    }
    closeMenu();
  });
  document.addEventListener("click", (event) => {
    if (!menu.contains(event.target)) closeMenu();
  });

  function setMode() {
    closeMenu();
    addForm.classList.remove("is-open");
    render(items);
  }

  return { render, setMode };
}
