import { normalizeLanguage, translate } from "../i18n.js";

const SINGLE_CITY_MODE = "single-city detail";
const MULTI_CITY_MODE = "multi-city summary";

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

function temperatureText(value, language) {
  return Number.isFinite(Number(value))
    ? `${Number(value)}℃`
    : translate("weather.noData", language);
}

function cityCard(city, language) {
  const card = document.createElement("article");
  card.className = "weather-city-card";

  const heading = document.createElement("header");
  heading.className = "weather-city-heading";
  heading.append(
    textNode("h3", "weather-city-name", city.city || translate("weather.unknownCity", language)),
    textNode("span", "weather-condition", city.condition || translate("weather.noWeather", language)),
  );

  const reading = document.createElement("div");
  reading.className = "weather-reading";
  reading.append(textNode("strong", "weather-current", temperatureText(city.currentTemperature, language)));

  const range = document.createElement("div");
  range.className = "weather-range";
  range.append(
    textNode("span", "weather-high", `${translate("weather.high", language)} ${temperatureText(city.high, language)}`),
    textNode("span", "weather-low", `${translate("weather.low", language)} ${temperatureText(city.low, language)}`),
  );

  card.append(
    heading,
    reading,
    range,
    textNode("div", "weather-wind", city.wind || translate("weather.windEmpty", language)),
  );
  return card;
}

export function createWeatherWidget() {
  const container = document.querySelector(".weather-widget");
  const list = document.getElementById("weather-cities");
  let weather = { displayMode: SINGLE_CITY_MODE, cities: [] };
  let language = "zh_CN";

  function render(nextWeather) {
    weather = nextWeather || { displayMode: SINGLE_CITY_MODE, cities: [] };
    const cities = Array.isArray(weather.cities) ? weather.cities : [];
    const displayCities = weather.displayMode === MULTI_CITY_MODE
      ? cities
      : cities.length ? [cities[0]] : [];
    list.replaceChildren();
    if (!displayCities.length) {
      list.append(textNode("div", "weather-empty", translate("weather.noData", language)));
      return;
    }
    // Keep every city selected by the display mode in the DOM. The layout
    // controller grows the information card when the rows need more height.
    displayCities.forEach((city) => list.append(cityCard(city, language)));
  }

  function setMode() {
    // Weather is view-only in every Dashboard mode.
  }

  function setLanguage(nextLanguage) {
    language = normalizeLanguage(nextLanguage);
    render(weather);
  }

  if (typeof ResizeObserver !== "undefined" && container) {
    new ResizeObserver(() => render(weather)).observe(container);
  }
  render(weather);
  return { render, setMode, setLanguage };
}
