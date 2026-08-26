import { normalizeLanguage, translate } from "../i18n.js";

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

function financeRow(item, language) {
  const row = document.createElement("article");
  row.className = "finance-item";
  row.dataset.direction = item.direction || "unknown";

  const heading = document.createElement("div");
  heading.className = "finance-item-heading";
  heading.append(
    textNode("h3", "finance-item-name", item.name || translate("finance.unknown", language)),
    textNode("strong", "finance-value", item.valueText || translate("finance.noData", language)),
  );

  const meta = document.createElement("div");
  meta.className = "finance-meta";
  if (item.changePercentText) {
    meta.append(textNode("span", "finance-change", item.changePercentText));
  }
  if (item.secondaryText) {
    meta.append(textNode("span", "finance-secondary", item.secondaryText));
  }

  row.append(heading, meta);
  return row;
}

function uniqueFinanceItems(items) {
  const seen = new Set();
  return items.filter((item) => {
    const identity = typeof item?.key === "string" && item.key.trim()
      ? item.key
      : `${item?.category || ""}|${item?.name || ""}|${item?.valueText || ""}`;
    if (seen.has(identity)) return false;
    seen.add(identity);
    return true;
  });
}

export function createFinanceWidget(category) {
  const container = document.querySelector(`.finance-widget[data-finance-category="${category}"]`);
  const list = container?.querySelector(".finance-items");
  let finance = { items: [] };
  let language = "zh_CN";

  function render(nextFinance) {
    finance = nextFinance || { items: [] };
    if (!list) return;
    const allItems = Array.isArray(finance.items) ? finance.items : [];
    const filtered = category === "overview"
      ? allItems
      : allItems.filter((item) => item.category === category);
    const unique = uniqueFinanceItems(filtered);
    list.replaceChildren();
    if (!unique.length) {
      list.append(textNode("div", "finance-empty", translate("finance.noData", language)));
      return;
    }
    // The layout controller grows the card from the list's measured height.
    unique.forEach((item) => list.append(financeRow(item, language)));
  }

  function setMode() {
    // Finance widgets are view-only in every Dashboard mode.
  }

  function setLanguage(nextLanguage) {
    language = normalizeLanguage(nextLanguage);
    render(finance);
  }

  if (typeof ResizeObserver !== "undefined" && container) {
    new ResizeObserver(() => render(finance)).observe(container);
  }
  render(finance);
  return { render, setMode, setLanguage };
}
