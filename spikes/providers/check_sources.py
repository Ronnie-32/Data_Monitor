"""Bounded source gate for DeskBoard V1 network categories.

This research spike uses fixed sources, disables urllib proxy discovery, and
can record raw responses for deterministic offline parser replay. It is not a
production Provider and does not implement runtime fallback.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "providers"
MAX_RESPONSE_BYTES = 256_000
TIMEOUT_SECONDS = 10
USER_AGENT = "DeskBoard-Task1-SourceGate/0.2"

WEATHER_CITIES = {
    "beijing": ("北京", "101010100"),
    "shanghai": ("上海", "101020100"),
}
WEATHER_URL = "http://d1.weather.com.cn/weather_index/{city_id}.html"
WEATHER_FORECAST_URL = "http://www.weather.com.cn/weather/{city_id}.shtml"
SGE_DAILY_URL = "https://www.sge.com.cn/sjzx/quotation_daily_new"
CHINAMONEY_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew"
INDEX_URL = (
    "https://qt.gtimg.cn/q="
    "s_sh000001,s_sz399001,s_sz399006,sh000300,us.DJI,us.INX,us.IXIC"
)

FIXTURE_NAMES = {
    "weather_beijing": "weather_com_cn_beijing.html",
    "weather_shanghai": "weather_com_cn_shanghai.html",
    "weather_forecast_beijing": "weather_com_cn_beijing_forecast.html",
    "weather_forecast_shanghai": "weather_com_cn_shanghai_forecast.html",
    "gold": "sge_au9999_daily.html",
    "fx": "chinamoney_ccpr_his_new.json",
    "indices": "tencent_indices_gbk.txt",
}


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("response is neither UTF-8 nor GB18030")


def fetch(url: str) -> bytes:
    """Fetch one fixed endpoint with environment/system proxies disabled."""
    opener = build_opener(ProxyHandler({}))
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    if "weather.com.cn" in url:
        city_id = url.rsplit("/", 1)[-1].split(".", 1)[0]
        request.add_header(
            "Referer", f"http://www.weather.com.cn/weather1d/{city_id}.shtml"
        )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        message = str(exc).replace("\n", " ")[:160]
        raise RuntimeError(f"request failed: {type(exc).__name__}: {message}") from exc
    if len(content) > MAX_RESPONSE_BYTES:
        raise RuntimeError(f"response exceeds {MAX_RESPONSE_BYTES} byte limit")
    return content


def _number(value: Any, *, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if result != result or result in (float("inf"), float("-inf")):
        raise ValueError(f"{field} is not finite")
    return result


def _weather_object(text: str, variable: str) -> dict[str, Any]:
    match = re.search(rf"var\s+{variable}\s*=\s*(\{{.*?\}})\s*;", text, re.S)
    if not match:
        raise ValueError(f"weather response missing {variable}")
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"weather {variable} JSON is invalid") from exc
    if not isinstance(value, dict):
        raise ValueError(f"weather {variable} is not an object")
    return value


def _forecast_temperatures(raw: bytes) -> tuple[float, float]:
    text = raw.decode("utf-8", errors="replace")
    list_start = text.find('<ul class="t clearfix">')
    first_day_end = text.find("</li>", list_start)
    if list_start < 0 or first_day_end < 0:
        raise ValueError("weather forecast page lacks today's row")
    today = text[list_start:first_day_end]
    match = re.search(
        r'<p class="tem">\s*<span>([-+]?\d+(?:\.\d+)?)</span>\s*/\s*'
        r'<i>([-+]?\d+(?:\.\d+)?)℃</i>',
        today,
        re.S,
    )
    if not match:
        raise ValueError("weather forecast page lacks today's high/low")
    return _number(match.group(1), field="high"), _number(match.group(2), field="low")


def parse_weather(raw: bytes, forecast_raw: bytes, *, city_key: str) -> dict[str, Any]:
    city_name, city_id = WEATHER_CITIES[city_key]
    text = _decode(raw)
    current = _weather_object(text, "dataSK")
    high, low = _forecast_temperatures(forecast_raw)
    current_temperature = _number(current.get("temp"), field="current temperature")
    condition = str(current.get("weather") or "").strip()
    wind = " ".join(
        str(current.get(key, "")).strip() for key in ("WD", "WS") if current.get(key)
    )
    if not condition or not wind:
        raise ValueError("weather response lacks condition or wind")
    return {
        "city": city_name,
        "city_id": city_id,
        "condition": condition,
        "current_temperature": current_temperature,
        "high": max(high, current_temperature),
        "low": min(low, current_temperature),
        "forecast_high": high,
        "forecast_low": low,
        "temperature_envelope": "observed current expands forecast bounds",
        "wind": wind,
        "temperature_unit": "°C",
    }


def _cell_text(cell: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", cell)
    return " ".join(html.unescape(without_tags).split())


def parse_gold(raw: bytes) -> dict[str, Any]:
    """Parse the Shanghai Gold Exchange daily Au99.99 row."""
    text = _decode(raw)
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, re.I | re.S):
        cells = [_cell_text(cell) for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.I | re.S)]
        try:
            contract_i = next(
                index for index, value in enumerate(cells) if value.replace(" ", "") == "Au99.99"
            )
        except StopIteration:
            continue
        if contract_i < 1 or len(cells) <= contract_i + 6:
            continue
        return {
            "key": "gold_au9999",
            "date": cells[contract_i - 1],
            "name": "Au99.99",
            "value": _number(cells[contract_i + 4].replace(",", ""), field="Au99.99 close"),
            "change": _number(cells[contract_i + 5].replace(",", ""), field="Au99.99 change"),
            "change_percent": _number(cells[contract_i + 6].rstrip("%").replace(",", ""), field="Au99.99 change percent"),
            "unit": "CNY/g",
            "price_field": "daily close",
        }
    raise ValueError("SGE response lacks a usable Au99.99 daily row")


def parse_fx(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(_decode(raw))
        data = payload["data"]
        labels = data["searchlist"]
        records = payload["records"]
        latest = records[0]
        values = latest["values"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("FX response shape is invalid") from exc
    if not isinstance(labels, list) or not isinstance(values, list) or len(labels) != len(values):
        raise ValueError("FX labels and values are inconsistent")
    upstream = dict(zip((str(label) for label in labels), values, strict=True))
    wanted = {
        "USD": ("USD/CNY", 1.0),
        "EUR": ("EUR/CNY", 1.0),
        "JPY": ("100JPY/CNY", 0.01),
        "HKD": ("HKD/CNY", 1.0),
    }
    items: dict[str, Any] = {}
    for currency, (quotation, multiplier) in wanted.items():
        if quotation not in upstream:
            raise ValueError(f"FX record missing {quotation}")
        raw_value = _number(upstream[quotation], field=quotation)
        items[currency] = {
            "value": raw_value * multiplier,
            "unit": f"CNY/1 {currency}",
            "upstream_quotation": quotation,
            "upstream_value": raw_value,
        }
    return {
        "date": str(latest.get("date", "")),
        "basis": "CNY per 1 foreign-currency unit",
        "items": items,
    }


INDEX_FIELDS = {
    "v_s_sh000001": ("上证指数", "china", 3, 4, 5),
    "v_s_sz399001": ("深证成指", "china", 3, 4, 5),
    "v_s_sz399006": ("创业板指", "china", 3, 4, 5),
    "v_sh000300": ("沪深300", "china", 3, 31, 32),
    "v_us.DJI": ("道琼斯", "us", 3, 31, 32),
    "v_us.INX": ("标普500", "us", 3, 31, 32),
    "v_us.IXIC": ("纳斯达克综合", "us", 3, 31, 32),
}


def parse_indices(raw: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {"china": [], "us": []}
    for match in re.finditer(r'(v_[\w.]+)="([^"]*)";', _decode(raw)):
        variable = match.group(1)
        if variable not in INDEX_FIELDS:
            continue
        name, market, value_i, change_i, percent_i = INDEX_FIELDS[variable]
        fields = match.group(2).split("~")
        try:
            item = {
                "key": variable.removeprefix("v_"),
                "name": name,
                "value": _number(fields[value_i], field=f"{name} value"),
                "change": _number(fields[change_i], field=f"{name} change"),
                "change_percent": _number(fields[percent_i], field=f"{name} change percent"),
                "unit": "index points",
            }
        except (IndexError, ValueError) as exc:
            if market == "us":
                continue
            raise ValueError(f"{name} quote fields are invalid") from exc
        result[market].append(item)
    if len(result["china"]) != 4:
        raise ValueError("not all four required A-share indices were found")
    return result


def _sample(result: dict[str, Any]) -> str:
    if "items" in result:
        return ", ".join(
            f"{key}={item['value']:.5f} {item['unit']}"
            for key, item in result["items"].items()
        )
    if "china" in result:
        return ", ".join(
            f"{item['name']}={item['value']:.2f} ({item['change_percent']:+.2f}%)"
            for item in result["china"] + result["us"]
        )
    keys = ("city", "condition", "current_temperature", "high", "low", "wind", "name", "value", "unit")
    return ", ".join(f"{key}={result[key]}" for key in keys if key in result)


def _fetch_gold(as_of: date) -> bytes:
    """Use a bounded same-source date lookback for weekends and holidays."""
    last_error = "no response"
    for offset in range(10):
        target = as_of - timedelta(days=offset)
        url = f"{SGE_DAILY_URL}?{urlencode({'start_date': target.isoformat(), 'end_date': target.isoformat()})}"
        try:
            raw = fetch(url)
            parse_gold(raw)
            return raw
        except (RuntimeError, ValueError) as exc:
            last_error = str(exc)
    raise RuntimeError(f"no usable SGE Au99.99 row in bounded 10-day lookback: {last_error}")


def _fx_url(as_of: date) -> str:
    params = {
        "startDate": (as_of - timedelta(days=14)).isoformat(),
        "endDate": as_of.isoformat(),
        "currency": "USD/CNY,EUR/CNY,100JPY/CNY,HKD/CNY",
        "pageNum": "1",
        "pageSize": "20",
    }
    return f"{CHINAMONEY_URL}?{urlencode(params)}"


def _acquire(as_of: date) -> dict[str, bytes]:
    raws = {
        f"weather_{key}": fetch(WEATHER_URL.format(city_id=city_id))
        for key, (_, city_id) in WEATHER_CITIES.items()
    }
    raws.update(
        {
            f"weather_forecast_{key}": fetch(
                WEATHER_FORECAST_URL.format(city_id=city_id)
            )
            for key, (_, city_id) in WEATHER_CITIES.items()
        }
    )
    raws["gold"] = _fetch_gold(as_of)
    raws["fx"] = fetch(_fx_url(as_of))
    raws["indices"] = fetch(INDEX_URL)
    return raws


def _run(raws: dict[str, bytes]) -> int:
    failures: list[str] = []
    for city_key in WEATHER_CITIES:
        try:
            result = parse_weather(
                raws[f"weather_{city_key}"],
                raws[f"weather_forecast_{city_key}"],
                city_key=city_key,
            )
            print(f"PASS weather/{city_key}: {_sample(result)}")
        except (KeyError, ValueError) as exc:
            failures.append(f"weather/{city_key}: {exc}")
            print(f"FAIL weather/{city_key}: {exc}")
    for group, parser in (("gold", parse_gold), ("fx", parse_fx), ("indices", parse_indices)):
        try:
            result = parser(raws[group])
            print(f"PASS {group}: {_sample(result)}")
        except (KeyError, ValueError) as exc:
            failures.append(f"{group}: {exc}")
            print(f"FAIL {group}: {exc}")
    try:
        us = parse_indices(raws["indices"])["us"]
        if len(us) == 3:
            print("PASS us_indices candidate: " + ", ".join(item["name"] for item in us))
        else:
            print("DEFER us_indices: required three quotes were not all usable")
    except (KeyError, ValueError) as exc:
        print(f"DEFER us_indices: {exc}")
    if failures:
        print("SUMMARY: FAIL (mandatory source gate did not pass)")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SUMMARY: PASS mandatory categories; US candidate is reported separately")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="parse saved fixtures only")
    parser.add_argument("--record", action="store_true", help="save successful raw responses")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(), metavar="YYYY-MM-DD")
    args = parser.parse_args(argv)
    if args.offline and args.record:
        parser.error("--offline and --record are mutually exclusive")

    if args.offline:
        try:
            raws = {key: (FIXTURE_DIR / name).read_bytes() for key, name in FIXTURE_NAMES.items()}
        except OSError as exc:
            print(f"ERROR fixture: {exc}", file=sys.stderr)
            return 2
    else:
        try:
            raws = _acquire(args.as_of)
        except RuntimeError as exc:
            print(f"SUMMARY: FAIL acquisition: {exc}")
            return 1
        if args.record:
            FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
            for key, raw in raws.items():
                path = FIXTURE_DIR / FIXTURE_NAMES[key]
                path.write_bytes(raw)
                print(f"RECORDED {key}: {len(raw)} bytes -> {path}")
    return _run(raws)


if __name__ == "__main__":
    raise SystemExit(main())
