#!/usr/bin/env python3
"""Generate a minimum-wage affordability package for the teen-autonomy story.

The package combines:
* DOL federal minimum wage history
* BLS CPI series for used cars and motor-vehicle insurance
* EIA annual gasoline prices
* BLS Consumer Expenditure anchors for used-vehicle purchases, vehicle insurance,
  and gasoline / motor oil spending

The result is an estimated annual ownership basket cost and the minimum-wage
hours required to cover it.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import math
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


BLS_URL = "https://data.bls.gov/pdq/SurveyOutputServlet"
EIA_URL = "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T09.04"
USED_PURCHASE_URL = "https://fred.stlouisfed.org/data/CXUUSEDCARSLB0101M"
INSURANCE_EXP_URL = "https://fred.stlouisfed.org/data/CXU500110LB0101M"
GAS_EXP_URL = "https://fred.stlouisfed.org/data/CXUGASOILLB0101M"


# Federal minimum wage history, keyed by the effective date of each change.
# The sequence follows the DOL history page and uses the rate that best matches
# the broadly applicable federal minimum wage in effect after each date.
MIN_WAGE_EVENTS = [
    (date(1938, 10, 24), 0.25),
    (date(1939, 10, 24), 0.30),
    (date(1945, 10, 24), 0.40),
    (date(1950, 1, 25), 0.75),
    (date(1956, 3, 1), 1.00),
    (date(1961, 9, 3), 1.15),
    (date(1963, 9, 3), 1.25),
    (date(1964, 9, 3), 1.15),
    (date(1965, 9, 3), 1.25),
    (date(1967, 2, 1), 1.40),
    (date(1968, 2, 1), 1.60),
    (date(1969, 2, 1), 1.30),
    (date(1970, 2, 1), 1.45),
    (date(1971, 2, 1), 1.60),
    (date(1974, 5, 1), 2.00),
    (date(1975, 1, 1), 2.10),
    (date(1976, 1, 1), 2.30),
    (date(1977, 1, 1), 2.30),
    (date(1978, 1, 1), 2.65),
    (date(1979, 1, 1), 2.90),
    (date(1980, 1, 1), 3.10),
    (date(1981, 1, 1), 3.35),
    (date(1990, 4, 1), 3.80),
    (date(1991, 4, 1), 4.25),
    (date(1996, 10, 1), 4.75),
    (date(1997, 9, 1), 5.15),
    (date(2007, 7, 24), 5.85),
    (date(2008, 7, 24), 6.55),
    (date(2009, 7, 24), 7.25),
]


SELECTED_YEARS = [1963, 1973, 1983, 1993, 2003, 2013, 2023, 2024]


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def axis_label(
    x: float,
    y: float,
    text: str,
    size: int = 12,
    *,
    anchor: str = "middle",
    fill: str = "#667085",
    weight: str = "400",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
        f'font-family="Arial, Helvetica, sans-serif" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{esc(text)}</text>'
    )


def svg_wrap(width: int, height: int, title: str, subtitle: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
  <defs>
    <linearGradient id="bgFade" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#FFFDF8"/>
      <stop offset="100%" stop-color="#F7F2E8"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#0D1321" flood-opacity="0.10"/>
    </filter>
  </defs>
  <rect x="0" y="0" width="{width}" height="{height}" rx="30" fill="url(#bgFade)"/>
  <g filter="url(#softShadow)">
    <rect x="22" y="22" width="{width - 44}" height="{height - 44}" rx="24" fill="white" opacity="0.92"/>
  </g>
  <text x="52" y="72" font-size="30" font-family="Georgia, 'Times New Roman', serif" font-weight="700" fill="#101828">{esc(title)}</text>
  <text x="52" y="102" font-size="14" font-family="Arial, Helvetica, sans-serif" fill="#475467">{esc(subtitle)}</text>
  {body}
</svg>"""


def parse_bls_annual_series(series_id: str, start_year: int = 1963, end_year: int = 2024) -> Dict[int, float]:
    payload = {
        "request_action": "get_data",
        "reformat": "true",
        "from_results_page": "true",
        "annualAveragesRequested": "true",
        "initial_request": "false",
        "data_tool": "latest_numbers",
        "series_id": series_id,
        "include_graphs": "true",
        "output_view": "data|",
        "from_year": str(start_year),
        "to_year": str(end_year),
    }
    req = Request(BLS_URL, data=urlencode(payload).encode("utf-8"), method="POST")
    html_doc = urlopen(req, timeout=60).read().decode("utf-8", "replace")
    soup = BeautifulSoup(html_doc, "html.parser")
    rows: Dict[int, float] = {}
    for tr in soup.find_all("tr"):
        year_th = tr.find("th", scope="row")
        if not year_th:
            continue
        year_text = year_th.get_text(strip=True)
        if not year_text.isdigit():
            continue
        year = int(year_text)
        if year < start_year or year > end_year:
            continue
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < 13:
            continue
        annual = cells[12]
        if annual in {"", ".", "NA", "N/A", "-"}:
            continue
        rows[year] = float(annual.replace(",", ""))
    return rows


def parse_fred_annual_table(url: str) -> Dict[int, float]:
    html_doc = urlopen(url, timeout=60).read().decode("utf-8", "replace")
    soup = BeautifulSoup(html_doc, "html.parser")
    rows: Dict[int, float] = {}
    for tr in soup.find_all("tr"):
        year_th = tr.find("th", scope="row")
        if not year_th:
            continue
        year_text = year_th.get_text(strip=True)
        year = None
        if year_text.isdigit():
            year = int(year_text)
        else:
            try:
                year = datetime.strptime(year_text, "%Y-%m-%d").year
            except ValueError:
                continue
        tds = tr.find_all("td")
        if not tds:
            continue
        value_text = tds[0].get_text(strip=True)
        if value_text in {"", ".", "NA", "N/A", "-"}:
            continue
        rows[year] = float(value_text.replace(",", ""))
    return rows


def fill_missing_years(series: Dict[int, float]) -> Dict[int, float]:
    years = sorted(series)
    if not years:
        return series
    filled = dict(series)
    for year in range(years[0], years[-1] + 1):
        if year in filled:
            continue
        prev_years = [y for y in years if y < year]
        next_years = [y for y in years if y > year]
        if not prev_years or not next_years:
            continue
        y0 = max(prev_years)
        y1 = min(next_years)
        filled[year] = filled[y0] + (filled[y1] - filled[y0]) * (year - y0) / (y1 - y0)
    return filled


def parse_eia_gasoline_annual(series_id: str) -> Dict[int, float]:
    with urlopen(EIA_URL, timeout=60) as response:
        raw = response.read().decode("utf-8", "replace")
    reader = csv.DictReader(io.StringIO(raw.replace("\r", "")))
    annual: Dict[int, float] = {}
    for row in reader:
        if row["MSN"] != series_id:
            continue
        yyyymm = row["YYYYMM"].strip()
        if not yyyymm.endswith("13"):
            continue
        value = row["Value"].strip()
        if value in {"", ".", "NA", "N/A", "Not Available", "Not Applicable", "--"}:
            continue
        annual[int(yyyymm[:4])] = float(value)
    return annual


def annual_min_wage(year: int) -> float:
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    events = [event for event in MIN_WAGE_EVENTS if event[0] < end]
    if not events:
        raise ValueError(f"No minimum wage history available for {year}")
    current_rate = None
    for effective_date, rate in reversed(events):
        if effective_date <= start:
            current_rate = rate
            break
    if current_rate is None:
        current_rate = events[0][1]

    cursor = start
    total = 0.0
    for effective_date, rate in events:
        if effective_date <= start:
            current_rate = rate
            continue
        if effective_date >= end:
            break
        total += current_rate * (effective_date - cursor).days
        cursor = effective_date
        current_rate = rate
    total += current_rate * (end - cursor).days
    return total / (end - start).days


def backcast(anchor_value: float, series: Dict[int, float], year: int, anchor_year: int) -> float:
    return anchor_value * series[year] / series[anchor_year]


def line_points(series, x0, x1, y0, y1, xmin, xmax, ymin, ymax):
    pts = []
    span_x = xmax - xmin
    span_y = ymax - ymin
    for year, value in series:
        x = x0 + (year - xmin) / span_x * (x1 - x0)
        y = y1 - (value - ymin) / span_y * (y1 - y0)
        pts.append((x, y))
    return pts


def build_dataset():
    used_cpi = fill_missing_years(parse_bls_annual_series("CUUR0000SETA02"))
    ins_cpi = parse_bls_annual_series("CUUR0000SETE")
    gas_leaded = parse_eia_gasoline_annual("RLUCUUS")
    gas_all = parse_eia_gasoline_annual("MGUCUUS")

    used_purchase = parse_fred_annual_table(USED_PURCHASE_URL)
    insurance_exp = parse_fred_annual_table(INSURANCE_EXP_URL)
    gas_exp = parse_fred_annual_table(GAS_EXP_URL)

    used_anchor_year = 2024
    ins_anchor_year = 2024
    gas_anchor_year = 2023

    used_anchor = used_purchase[used_anchor_year]
    insurance_anchor = insurance_exp[ins_anchor_year]
    gas_anchor = gas_exp[gas_anchor_year]

    gas_splice_year = 1990
    gas_splice_scale = gas_leaded[gas_splice_year] / gas_all[gas_splice_year]
    gas_price: Dict[int, float] = {}
    for year in range(1963, 2025):
        if year <= gas_splice_year:
            gas_price[year] = gas_leaded[year]
        else:
            gas_price[year] = gas_all[year] * gas_splice_scale

    rows = []
    for year in range(1963, 2025):
        used_cost = backcast(used_anchor, used_cpi, year, used_anchor_year)
        ins_cost = backcast(insurance_anchor, ins_cpi, year, ins_anchor_year)
        gas_cost = backcast(gas_anchor, gas_price, year, gas_anchor_year)
        wage = annual_min_wage(year)
        total = used_cost + ins_cost + gas_cost
        hours = total / wage
        rows.append(
            {
                "Year": year,
                "MinWage": wage,
                "UsedVehiclePurchases": used_cost,
                "VehicleInsurance": ins_cost,
                "GasolineAndMotorOil": gas_cost,
                "TotalOwnershipCost": total,
                "HoursAtMinWage": hours,
                "WeeksAt40Hours": hours / 40.0,
                "SummerJobsAt480Hours": hours / 480.0,
            }
        )
    return rows


def draw_chart(rows):
    width, height = 1300, 1020
    chart_left, chart_right = 118, 1178
    chart_top, chart_bottom = 170, 640
    y_min = 0
    y_max = max(row["HoursAtMinWage"] for row in rows) * 1.12

    year_points = [(row["Year"], row["HoursAtMinWage"]) for row in rows]
    pts = line_points(year_points, chart_left, chart_right, chart_top, chart_bottom, rows[0]["Year"], rows[-1]["Year"], y_min, y_max)

    selected = {row["Year"]: row for row in rows if row["Year"] in SELECTED_YEARS}
    first = selected[1963]
    last = selected[2024]

    parts = []
    parts.append(axis_label(118, 132, "Minimum-wage hours needed for a teen driving basket", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(118, 154, "Annual used-vehicle purchases, vehicle insurance, and gasoline spending, backcast to 1963 with official price series.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(118, 178, "The basket is indexed from annual household spending anchors, so the result reads like the cost of ownership, not a sticker-price-only proxy.", 13, anchor="start", fill="#667085"))

    parts.append(f'<rect x="84" y="198" width="1136" height="492" rx="28" fill="#FFFFFF" stroke="#E5E7EB"/>')

    # Horizontal reference line for a 12-week summer job at 40 hours/week.
    summer_hours = 480
    summer_y = chart_bottom - (summer_hours - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
    parts.append(f'<line x1="{chart_left}" y1="{summer_y:.1f}" x2="{chart_right}" y2="{summer_y:.1f}" stroke="#C8971D" stroke-width="2" stroke-dasharray="7 6"/>')
    parts.append(axis_label(chart_right, summer_y - 8, "12 weeks at 40 hours/week = 480 hours", 11, anchor="end", fill="#C8971D", weight="700"))

    # Grid + y labels
    ticks = [0, 200, 400, 600, 800, 1000, 1200]
    for tick in ticks:
        if tick > y_max:
            continue
        y = chart_bottom - (tick - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#EEF2F7" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 16, y + 4, f"{tick}", 11, anchor="end", fill="#667085"))

    for year in range(1963, 2025, 5):
        x = chart_left + (year - rows[0]["Year"]) / (rows[-1]["Year"] - rows[0]["Year"]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F3F4F6" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    parts.append(f'<polygon points="{chart_left:.1f},{chart_bottom:.1f} {poly} {chart_right:.1f},{chart_bottom:.1f}" fill="#244A71" opacity="0.08"/>')
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#244A71" stroke-width="4.5"/>')

    for year in SELECTED_YEARS:
        row = selected[year]
        x = chart_left + (year - rows[0]["Year"]) / (rows[-1]["Year"] - rows[0]["Year"]) * (chart_right - chart_left)
        y = chart_bottom - (row["HoursAtMinWage"] - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        color = "#C8971D" if year in {1963, 2024} else "#C65A6A"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>')
        if year in {1963, 2024}:
            label_y = y - 18 if year == 1963 else y + 26
            align = "start" if year == 1963 else "end"
            label_x = x + 12 if year == 1963 else x - 12
            parts.append(f'<rect x="{label_x - (2 if year == 1963 else 190)}" y="{label_y - 24}" width="190" height="58" rx="16" fill="#FFFDF8" stroke="#E9E3D5"/>')
            parts.append(axis_label(label_x, label_y, f"{year}: {row['HoursAtMinWage']:.0f} hours", 16, anchor=align, fill="#101828", weight="700"))
            parts.append(axis_label(label_x, label_y + 22, f"about {row['SummerJobsAt480Hours']:.1f} summers", 12, anchor=align, fill="#667085"))

    parts.append(axis_label(118, 688, "Source notes: DOL minimum wage history; BLS CPI annual averages for used cars and motor vehicle insurance; EIA annual gasoline prices spliced from leaded regular through 1990 and all-grades gasoline thereafter; BLS Consumer Expenditure annual spending anchors for vehicle purchases, vehicle insurance, and gasoline / motor oil.", 11, anchor="start", fill="#667085"))
    parts.append(axis_label(118, 706, "The result is an estimated annual cost of ownership divided by the federal minimum wage, expressed as work hours.", 11, anchor="start", fill="#667085"))

    # Summary cards
    card_y = 748
    cards = [
        ("1963", first, "#244A71"),
        ("2024", last, "#C65A6A"),
    ]
    for idx, (title, row, color) in enumerate(cards):
        x = 118 + idx * 390
        parts.append(f'<rect x="{x}" y="{card_y}" width="360" height="190" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
        parts.append(f'<rect x="{x}" y="{card_y}" width="360" height="10" rx="10" fill="{color}"/>')
        parts.append(axis_label(x + 24, card_y + 42, f"{title} ownership basket", 14, anchor="start", fill="#667085", weight="700"))
        parts.append(axis_label(x + 24, card_y + 88, f"${row['TotalOwnershipCost']:.0f}", 38, anchor="start", fill="#101828", weight="700"))
        parts.append(axis_label(x + 24, card_y + 122, f"{row['HoursAtMinWage']:.0f} hours at the federal minimum wage", 13, anchor="start", fill="#667085"))
        parts.append(axis_label(x + 24, card_y + 148, f"{row['WeeksAt40Hours']:.1f} weeks at 40 hours/week", 13, anchor="start", fill="#667085"))
        parts.append(axis_label(x + 24, card_y + 174, f"{row['SummerJobsAt480Hours']:.1f} summers at 12 weeks", 13, anchor="start", fill="#667085"))

    parts.append(axis_label(118, 986, "Hours line = annual used-vehicle purchases + vehicle insurance + gasoline/motor oil spending, each backcast to the selected year from the nearest available annual spending anchor.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "How many minimum-wage hours a car basket required", "A long-run affordability line from 1963 to 2024.", "\n  ".join(parts))


def build_html(rows, svg_name: str) -> str:
    selected = [row for row in rows if row["Year"] in SELECTED_YEARS]
    table_rows = []
    for row in selected:
        table_rows.append(
            "<tr>"
            f"<th>{row['Year']}</th>"
            f"<td>${row['UsedVehiclePurchases']:.0f}</td>"
            f"<td>${row['VehicleInsurance']:.0f}</td>"
            f"<td>${row['GasolineAndMotorOil']:.0f}</td>"
            f"<td>${row['TotalOwnershipCost']:.0f}</td>"
            f"<td>{row['HoursAtMinWage']:.0f}</td>"
            f"<td>{row['WeeksAt40Hours']:.1f}</td>"
            f"<td>{row['SummerJobsAt480Hours']:.1f}</td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Minimum-Wage Car Ownership Basket</title>
  <style>
    :root {{
      --bg: #0A1220;
      --panel: #F7F3EB;
      --ink: #101828;
      --muted: #667085;
      --shadow: 0 28px 80px rgba(0,0,0,.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 14% 10%, rgba(198,90,106,.16), transparent 24%),
        radial-gradient(circle at 88% 8%, rgba(36,74,113,.18), transparent 22%),
        linear-gradient(180deg, var(--bg) 0%, #0F172A 48%, #132238 100%);
      color: #fff;
      font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", Arial, sans-serif;
    }}
    .wrap {{ max-width: 1380px; margin: 0 auto; padding: 42px 24px 70px; }}
    .hero {{ display: grid; grid-template-columns: 1.18fr .82fr; gap: 28px; align-items: end; padding-bottom: 24px; }}
    .kicker {{ text-transform: uppercase; letter-spacing: .22em; color: rgba(255,255,255,.66); font-size: 11px; margin-bottom: 14px; }}
    h1 {{ margin: 0; max-width: 10ch; font-family: Georgia, "Times New Roman", serif; font-size: clamp(54px, 7vw, 88px); line-height: .92; letter-spacing: -.055em; }}
    .deck {{ margin-top: 18px; max-width: 70ch; color: rgba(255,255,255,.84); font-size: 18px; line-height: 1.65; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 22px; color: rgba(255,255,255,.72); font-size: 13px; }}
    .meta span {{ padding: 8px 12px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); border-radius: 999px; backdrop-filter: blur(8px); }}
    .hero-card {{ border-radius: 28px; padding: 20px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.10); box-shadow: var(--shadow); backdrop-filter: blur(12px); }}
    .pill-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .pill {{ background: linear-gradient(180deg, rgba(255,255,255,.14), rgba(255,255,255,.06)); border: 1px solid rgba(255,255,255,.10); border-radius: 22px; padding: 16px 16px 18px; }}
    .pill .num {{ display: block; font-family: Georgia, "Times New Roman", serif; font-size: 30px; line-height: 1; margin-bottom: 8px; }}
    .pill .label {{ color: rgba(255,255,255,.78); font-size: 13px; line-height: 1.45; }}
    .section {{ margin-top: 18px; border-radius: 32px; overflow: hidden; box-shadow: var(--shadow); }}
    .panel {{ background: var(--panel); color: var(--ink); padding: 28px; }}
    .intro {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 22px; align-items: start; }}
    h2 {{ margin: 0 0 12px; font-size: clamp(26px, 3vw, 40px); line-height: 1; letter-spacing: -.04em; font-family: Georgia, "Times New Roman", serif; }}
    .copy {{ color: var(--muted); line-height: 1.7; font-size: 17px; }}
    .chart-card {{ background: #fff; border-top: 1px solid rgba(15, 23, 42, .08); }}
    .chart-head {{ padding: 22px 26px 0; }}
    .chart-head h3 {{ margin: 0; font-size: 24px; letter-spacing: -.03em; font-family: Georgia, "Times New Roman", serif; }}
    .chart-head p {{ margin: 8px 0 0; color: var(--muted); line-height: 1.6; max-width: 84ch; }}
    .chart {{ padding: 18px; background: linear-gradient(180deg, #fff, #faf7f1); }}
    .chart img {{ display: block; width: 100%; height: auto; border-radius: 18px; box-shadow: 0 12px 40px rgba(15, 23, 42, .08); }}
    .table-wrap {{ padding: 18px 18px 0; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 920px; }}
    th, td {{ text-align: right; padding: 10px 12px; border-bottom: 1px solid rgba(15, 23, 42, .08); font-size: 14px; }}
    th:first-child, td:first-child {{ text-align: left; }}
    thead th {{ position: sticky; top: 0; background: #fff; font-weight: 700; color: #344054; }}
    .footer {{ margin-top: 20px; color: rgba(255,255,255,.74); line-height: 1.65; font-size: 13px; }}
    @media (max-width: 1080px) {{ .hero, .intro {{ grid-template-columns: 1fr; }} .pill-grid {{ grid-template-columns: 1fr 1fr; }} }}
    @media (max-width: 640px) {{ .pill-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div>
        <div class="kicker">DOL / BLS / EIA affordability basket</div>
        <h1>A summer job used to cover the car</h1>
        <p class="deck">
          This package turns the federal minimum wage into hours of work required for a representative
          annual driving basket: used-vehicle purchases, vehicle insurance, and gasoline / motor oil.
          The long-run series is backcast from annual spending anchors using the relevant official price
          indexes, so the line is about ownership cost, not just sticker price.
        </p>
        <div class="meta">
          <span>Selected years: 1963, 1973, 1983, 1993, 2003, 2013, 2023, 2024</span>
          <span>Work benchmark: 12 weeks at 40 hours/week = 480 hours</span>
          <span>Series anchored to BLS / EIA annual data</span>
        </div>
      </div>
      <div class="hero-card">
        <div class="pill-grid">
          <div class="pill"><span class="num">{rows[0]['HoursAtMinWage']:.0f}</span><div class="label">Hours required in 1963</div></div>
          <div class="pill"><span class="num">{rows[-1]['HoursAtMinWage']:.0f}</span><div class="label">Hours required in 2024</div></div>
          <div class="pill"><span class="num">{rows[0]['SummerJobsAt480Hours']:.1f}</span><div class="label">Summer-job equivalents in 1963</div></div>
          <div class="pill"><span class="num">{rows[-1]['SummerJobsAt480Hours']:.1f}</span><div class="label">Summer-job equivalents in 2024</div></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="panel">
        <div class="intro">
          <div>
            <div class="eyebrow" style="text-transform:uppercase;letter-spacing:.18em;color:#6B7280;font-size:11px;font-weight:700;margin-bottom:10px;">What the line says</div>
            <h2>The minimum wage stopped keeping a summer car basket within reach.</h2>
            <div class="copy">
              The estimate adds up annual used-vehicle purchases, vehicle insurance, and gasoline / motor oil
              spending for a representative young driver. Each component is backcast from its current annual
              spending anchor using the appropriate official price series, then divided by the federal minimum
              wage in effect that year. That turns the argument into hours, weeks, and summers.
            </div>
          </div>
          <div class="copy">
            In the chart, the gold dashed line marks one 12-week summer at 40 hours a week. When the blue line
            rises above it, a single summer job can no longer fund the basket.
          </div>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-head">
          <h3>Main visual: hours of minimum-wage work required</h3>
          <p>The selected-year dots are the story points: 1963, 1973, 1983, 1993, 2003, 2013, 2023, and 2024.</p>
        </div>
        <div class="chart">
          <img src="{svg_name}" alt="Minimum-wage hours required for the annual driving basket" />
        </div>
      </div>

      <div class="chart-card" style="margin-top:18px;">
        <div class="chart-head">
          <h3>Selected years</h3>
          <p>Dollar values are annual spending estimates; hours divide that total by the federal minimum wage.</p>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>Used vehicle purchases</th>
                <th>Vehicle insurance</th>
                <th>Gasoline / motor oil</th>
                <th>Total basket</th>
                <th>Hours at min wage</th>
                <th>Weeks at 40h</th>
                <th>Summer jobs</th>
              </tr>
            </thead>
            <tbody>
              {''.join(table_rows)}
            </tbody>
          </table>
        </div>
      </div>

      <div class="chart-card" style="margin-top:18px;">
        <div class="chart-head">
          <h3>Method note</h3>
          <p>
            Used-vehicle purchases are anchored to the BLS Consumer Expenditure annual average for used
            vehicle purchases. Vehicle insurance is anchored to the BLS annual average vehicle-insurance
            expenditure. Gasoline / motor oil is anchored to the BLS annual average expenditure series
            and backcast with EIA leaded regular gasoline prices. The minimum wage uses the DOL history
            of federal minimum wage changes.
          </p>
        </div>
      </div>
    </section>

    <div class="footer">
      This is an estimated annual ownership basket, not a single dealership sticker price. The point is the
      work required to maintain a basic driving setup, not a perfect household survey reconstruction.
    </div>
  </div>
</body>
</html>"""


def write_outputs(outdir: Path, rows):
    outdir.mkdir(parents=True, exist_ok=True)
    svg_name = "minimum-wage-car-affordability.svg"
    html_name = "minimum-wage-car-affordability.html"
    csv_name = "minimum-wage-car-affordability.csv"

    (outdir / svg_name).write_text(draw_chart(rows), encoding="utf-8")
    (outdir / html_name).write_text(build_html(rows, svg_name), encoding="utf-8")

    with (outdir / csv_name).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Year",
                "MinWage",
                "UsedVehiclePurchases",
                "VehicleInsurance",
                "GasolineAndMotorOil",
                "TotalOwnershipCost",
                "HoursAtMinWage",
                "WeeksAt40Hours",
                "SummerJobsAt480Hours",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["Year"],
                    f"{row['MinWage']:.3f}",
                    f"{row['UsedVehiclePurchases']:.2f}",
                    f"{row['VehicleInsurance']:.2f}",
                    f"{row['GasolineAndMotorOil']:.2f}",
                    f"{row['TotalOwnershipCost']:.2f}",
                    f"{row['HoursAtMinWage']:.2f}",
                    f"{row['WeeksAt40Hours']:.2f}",
                    f"{row['SummerJobsAt480Hours']:.2f}",
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a minimum-wage affordability package.")
    parser.add_argument("--outdir", type=Path, default=Path("licensed-drivers"), help="Output directory.")
    args = parser.parse_args()

    rows = build_dataset()
    write_outputs(args.outdir, rows)
    print(f"Wrote affordability package to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
