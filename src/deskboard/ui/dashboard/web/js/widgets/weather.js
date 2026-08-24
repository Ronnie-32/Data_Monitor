const SINGLE_CITY_MODE = "single-city detail";
const MULTI_CITY_MODE = "multi-city summary";
const CITY_ROW_HEIGHT_PX = 76;

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

function temperatureText(value) {
  return Number.isFinite(Number(value)) ? `${Number(value)}℃` : "暂无数据";
}

function modeText(mode) {
  return mode === MULTI_CITY_MODE ? "多城市摘要" : "单城市详情";
}

function cityCard(city) {
  const card = document.createElement("article");
  card.className = "weather-city-card";

  const heading = document.createElement("header");
  heading.className = "weather-city-heading";
  heading.append(
    textNode("h3", "weather-city-name", city.city || "未知城市"),
    textNode("span", "weather-condition", city.condition || "暂无天气"),
  );

  const reading = document.createElement("div");
  reading.className = "weather-reading";
  reading.append(textNode("strong", "weather-current", temperatureText(city.currentTemperature)));

  const range = document.createElement("div");
  range.className = "weather-range";
  range.append(
    textNode("span", "weather-high", `高 ${temperatureText(city.high)}`),
    textNode("span", "weather-low", `低 ${temperatureText(city.low)}`),
  );

  card.append(heading, reading, range, textNode("div", "weather-wind", city.wind || "风力暂无数据"));
  return card;
}

function visibleCapacity(container) {
  const height = Number(container?.clientHeight || 0);
  if (!Number.isFinite(height) || height <= 0) return 1;
  return Math.max(1, Math.floor(Math.max(0, height - 58) / CITY_ROW_HEIGHT_PX));
}

export function createWeatherWidget() {
  const container = document.querySelector(".weather-widget");
  const modeLabel = document.getElementById("weather-mode");
  const list = document.getElementById("weather-cities");
  let weather = { displayMode: SINGLE_CITY_MODE, cities: [] };

  function render(nextWeather) {
    weather = nextWeather || { displayMode: SINGLE_CITY_MODE, cities: [] };
    const mode = weather.displayMode === MULTI_CITY_MODE ? MULTI_CITY_MODE : SINGLE_CITY_MODE;
    const cities = Array.isArray(weather.cities) ? weather.cities : [];
    const visibleCities = cities.slice(0, mode === MULTI_CITY_MODE ? visibleCapacity(container) : 1);
    modeLabel.textContent = modeText(mode);
    list.replaceChildren();
    if (!visibleCities.length) {
      list.append(textNode("div", "weather-empty", "暂无数据"));
      return;
    }
    visibleCities.forEach((city) => list.append(cityCard(city)));
  }

  function setMode() {
    // Weather is view-only in every Dashboard mode.
  }

  if (typeof ResizeObserver !== "undefined" && container) {
    new ResizeObserver(() => render(weather)).observe(container);
  }
  render(weather);
  return { render, setMode };
}
