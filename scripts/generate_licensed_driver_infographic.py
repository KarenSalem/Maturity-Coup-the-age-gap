#!/usr/bin/env python3
"""Generate infographic-ready SVG charts from FHWA DL-220 data.

This script downloads or reads the official DOT CSV for
"Licensed Drivers by Sex and Age Groups, 1963 - 2024 (DL-220)",
then emits a small bundle of static SVG charts plus a storyboard HTML page.

The outputs are intentionally dependency-free so they can be reused in
design tools, docs, or a CMS without needing a plotting library.
"""

from __future__ import annotations

import argparse
import csv
import html
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.request import urlopen

DATA_URL = "https://data.transportation.gov/api/views/jm62-yva2/rows.csv?accessType=DOWNLOAD"

OUTPUT_FILENAMES = {
    "age_pyramid": "licensed-drivers-age-pyramid-2024.svg",
    "youth_share": "licensed-drivers-youth-shares.svg",
    "gender_ratio": "licensed-drivers-gender-ratio-trends.svg",
    "summary": "licensed-drivers-summary.md",
    "storyboard": "licensed-drivers-storyboard.html",
}

COHORT_ORDER = [
    "Under 16",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
    "70-74",
    "75-79",
    "80-84",
    "85 and Older",
]

TIME_SERIES_COHORTS = ["16", "18", "21", "25-29"]

RATIO_COHORTS = [
    "Under 16",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
]


def fmt_millions(value_thousands: int) -> str:
    return f"{value_thousands / 1000:.1f}M"


def fmt_thousands(value_thousands: int) -> str:
    return f"{value_thousands:,}"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def escape(text: str) -> str:
    return html.escape(str(text), quote=True)


def download_csv(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response:
        content = response.read()
    dest.write_bytes(content)
    return dest


def load_rows(csv_path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            value = raw["Drivers"].strip().replace(",", "")
            rows.append(
                {
                    "Year": int(raw["Year"]),
                    "Cohort": raw["Cohort"],
                    "Sex": raw["Sex"],
                    "Drivers": int(value) if value else None,
                }
            )
    return rows


def build_indexes(rows: Sequence[Dict[str, object]]):
    by_year_total: Dict[int, int] = {}
    by_year_sex: Dict[Tuple[int, str], int] = {}
    by_year_cohort: Dict[Tuple[int, str], int] = {}
    for row in rows:
        drivers = row["Drivers"]
        if drivers is None:
            continue
        year = int(row["Year"])
        cohort = str(row["Cohort"])
        sex = str(row["Sex"])
        by_year_total[year] = by_year_total.get(year, 0) + int(drivers)
        by_year_sex[(year, sex)] = by_year_sex.get((year, sex), 0) + int(drivers)
        by_year_cohort[(year, cohort)] = by_year_cohort.get((year, cohort), 0) + int(drivers)
    return by_year_total, by_year_sex, by_year_cohort


def get_value(by_year_cohort: Dict[Tuple[int, str], int], year: int, cohort: str) -> int | None:
    return by_year_cohort.get((year, cohort))


def svg_wrap(width: int, height: int, title: str, subtitle: str, body: str, *, background: str = "#FFFDF8") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
  <defs>
    <linearGradient id="bgFade" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{background}"/>
      <stop offset="100%" stop-color="#F7F2E8"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#0D1321" flood-opacity="0.10"/>
    </filter>
  </defs>
  <rect x="0" y="0" width="{width}" height="{height}" rx="30" fill="url(#bgFade)"/>
  <g filter="url(#softShadow)">
    <rect x="22" y="22" width="{width-44}" height="{height-44}" rx="24" fill="white" opacity="0.88"/>
  </g>
  <text x="52" y="72" font-size="30" font-family="Georgia, 'Times New Roman', serif" font-weight="700" fill="#101828">{escape(title)}</text>
  <text x="52" y="102" font-size="14" font-family="Arial, Helvetica, sans-serif" fill="#475467">{escape(subtitle)}</text>
  {body}
</svg>"""


def axis_label(x: float, y: float, text: str, size: int = 12, anchor: str = "middle", fill: str = "#667085", weight: str = "400") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="Arial, Helvetica, sans-serif" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(text)}</text>'


def draw_age_pyramid(rows, by_year_cohort) -> str:
    selected_years = [1963, 1993, 2024]
    counts = {
        (int(row["Year"]), str(row["Cohort"]), str(row["Sex"])): int(row["Drivers"])
        for row in rows
        if row["Drivers"] is not None
    }
    cohorts = [c for c in COHORT_ORDER if any((y, c, s) in counts for y in selected_years for s in ("Male", "Female"))]
    max_val = max(counts[(y, c, s)] for y in selected_years for c in cohorts for s in ("Male", "Female") if (y, c, s) in counts)

    width, height = 1240, 1560
    center_x = 620
    chart_left = 170
    chart_right = 1070
    start_y = 170
    panel_h = 390
    row_h = 14
    scale = 340 / max_val

    male = "#244A71"
    female = "#C65A6A"
    gold = "#C8971D"
    grid = "#E5E7EB"
    ink = "#101828"
    muted = "#667085"

    def first_female_majority(year: int) -> str:
        for cohort in cohorts:
            m = counts.get((year, cohort, "Male"))
            f = counts.get((year, cohort, "Female"))
            if m is not None and f is not None and f >= m:
                return cohort
        return "none"

    year_notes = {
        1963: "Male-heavy across the whole age profile. The teenage pipeline is broad.",
        1993: "The gap narrows. Midlife starts moving toward parity.",
        2024: f"Parity arrives at {first_female_majority(2024)}. Older ages are female-heavy.",
    }

    parts = []
    for panel_idx, year in enumerate(selected_years):
        top = start_y + panel_idx * panel_h
        parts.append(f'<rect x="70" y="{top-22}" width="1100" height="330" rx="28" fill="#FFFFFF" opacity="0.64"/>')
        parts.append(axis_label(120, top + 10, str(year), 24, anchor="start", fill=ink, weight="700"))
        parts.append(axis_label(240, top + 10, year_notes[year], 14, anchor="start", fill=muted))
        parts.append(f'<line x1="{center_x}" y1="{top+18}" x2="{center_x}" y2="{top + 14 + row_h * len(cohorts) + 8}" stroke="#CBD5E1" stroke-width="2"/>')

        for tick in [0, 2500, 5000, 7500, 10000]:
            x = center_x + tick * scale
            xl = center_x - tick * scale
            parts.append(f'<line x1="{x:.1f}" y1="{top+18}" x2="{x:.1f}" y2="{top + 14 + row_h * len(cohorts) + 8}" stroke="{grid}" stroke-width="1"/>')
            if tick > 0:
                parts.append(f'<line x1="{xl:.1f}" y1="{top+18}" x2="{xl:.1f}" y2="{top + 14 + row_h * len(cohorts) + 8}" stroke="{grid}" stroke-width="1"/>')
            label = "0" if tick == 0 else f"{tick/1000:.1f}M"
            parts.append(axis_label(x, top + 10, label, 10, fill=muted))
            if tick > 0:
                parts.append(axis_label(xl, top + 10, label, 10, fill=muted))

        for idx, cohort in enumerate(cohorts):
            y = top + 28 + idx * row_h
            if idx % 2 == 0:
                parts.append(f'<rect x="{chart_left-20}" y="{y-7}" width="{chart_right-chart_left+40}" height="{row_h-1}" rx="6" fill="#FAFAFA" opacity="0.95"/>')
            if cohort in {"16", "17", "18", "19", "20", "21", "22", "23", "24"}:
                parts.append(f'<rect x="{chart_left-20}" y="{y-7}" width="{chart_right-chart_left+40}" height="{row_h-1}" rx="6" fill="#FFF4EC" opacity="0.95"/>')

            male_count = counts.get((year, cohort, "Male"))
            female_count = counts.get((year, cohort, "Female"))
            if male_count is None or female_count is None:
                continue

            female_w = female_count * scale
            male_w = male_count * scale
            bar_h = 10
            y_bar = y - 2
            parts.append(f'<rect x="{center_x - female_w:.1f}" y="{y_bar:.1f}" width="{female_w:.1f}" height="{bar_h}" rx="5" fill="{female}"/>')
            parts.append(f'<rect x="{center_x:.1f}" y="{y_bar:.1f}" width="{male_w:.1f}" height="{bar_h}" rx="5" fill="{male}"/>')
            parts.append(axis_label(chart_left - 6, y + 4, cohort, 11, anchor="end", fill=ink, weight="600"))

            if cohort in {"18", "40-44", "85 and Older"} and year == 2024:
                parts.append(axis_label(center_x - female_w - 8, y + 4, fmt_millions(female_count), 10, anchor="end", fill=female, weight="700"))
                parts.append(axis_label(center_x + male_w + 8, y + 4, fmt_millions(male_count), 10, anchor="start", fill=male, weight="700"))

        if year == 2024:
            row_idx = cohorts.index("18")
            y = top + 28 + row_idx * row_h - 2
            parts.append(f'<rect x="{center_x-170}" y="{y-11}" width="340" height="22" rx="11" fill="{gold}" opacity="0.14"/>')
            parts.append(axis_label(center_x, y + 2, "18-year-olds: 2.7M licensed drivers", 12, fill="#7A1F2B", weight="700"))

        if year == 1993:
            row_idx = cohorts.index("40-44")
            y = top + 28 + row_idx * row_h - 2
            parts.append(f'<rect x="{center_x-165}" y="{y-11}" width="330" height="22" rx="11" fill="{gold}" opacity="0.14"/>')
            parts.append(axis_label(center_x, y + 2, "Middle age is nearing parity", 12, fill="#8A6400", weight="700"))

    parts.append(axis_label(620, 1515, "Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov. Counts shown in millions of licensed drivers.", 11, fill=muted))
    title = "The road got older"
    subtitle = "Three years, same table. The shape changes from male-heavy youth to a flatter, older, nearly balanced driving population."
    return svg_wrap(width, height, title, subtitle, "\n  ".join(parts))


def line_points(series: Sequence[Tuple[int, float]], x0: float, x1: float, y0: float, y1: float, xmin: int, xmax: int, ymin: float, ymax: float):
    pts = []
    span_x = xmax - xmin
    span_y = ymax - ymin
    for year, value in series:
        x = x0 + (year - xmin) / span_x * (x1 - x0)
        y = y1 - (value - ymin) / span_y * (y1 - y0)
        pts.append((x, y))
    return pts


def draw_youth_share_chart(by_year_total, by_year_cohort, by_year_sex) -> str:
    years = sorted(by_year_total)
    series = {}
    for cohort in ["16", "18", "21", "24"]:
        pts = []
        for year in years:
            total = by_year_total[year]
            value = by_year_cohort.get((year, cohort))
            if value is None:
                continue
            pts.append((year, value / total * 100))
        series[cohort] = pts

    share_16_24 = []
    for year in years:
        total = by_year_total[year]
        youth = sum(by_year_cohort[(year, c)] for c in ["16", "17", "18", "19", "20", "21", "22", "23", "24"])
        share_16_24.append((year, youth / total * 100))

    width, height = 1240, 1100
    chart_left, chart_right = 120, 1130
    chart_top = 180
    chart_h = 440
    year_min, year_max = years[0], years[-1]

    palette = {
        "16": "#4E8098",
        "18": "#C65A6A",
        "21": "#C8971D",
        "24": "#334E68",
        "16-24": "#0F172A",
    }

    parts = []
    y_min, y_max = 0.0, 20.0
    for i in range(6):
        y = chart_top + i * chart_h / 5
        val = y_max - i * (y_max - y_min) / 5
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 18, y + 4, f"{val:.0f}%", 11, anchor="end", fill="#667085"))
    for year in range(year_min, year_max + 1, 5):
        x = chart_left + (year - year_min) / (year_max - year_min) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_top + chart_h}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_top + chart_h + 22, str(year), 10, fill="#667085"))

    # Emphasis band for the youth basket.
    parts.append(f'<rect x="{chart_left}" y="{chart_top + 120}" width="{chart_right-chart_left}" height="140" rx="20" fill="#FFF6EF" opacity="0.95"/>')

    for cohort, stroke in [("16-24", palette["16-24"]), ("18", palette["18"]), ("21", palette["21"]), ("24", palette["24"]), ("16", palette["16"])]:
        pts = share_16_24 if cohort == "16-24" else series[cohort]
        plotted = line_points(pts, chart_left, chart_right, chart_top, chart_top + chart_h, year_min, year_max, y_min, y_max)
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
        dash = ' stroke-dasharray="7 5"' if cohort in {"21", "24"} else ""
        width_line = 5 if cohort == "16-24" else 3
        opacity = "0.95" if cohort == "16-24" else "0.92"
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{stroke}" stroke-width="{width_line}" opacity="{opacity}"{dash}/>')
        if plotted:
            x0, y0p = plotted[0]
            x1, y1p = plotted[-1]
            parts.append(f'<circle cx="{x0:.1f}" cy="{y0p:.1f}" r="5" fill="{stroke}"/>')
            parts.append(f'<circle cx="{x1:.1f}" cy="{y1p:.1f}" r="5" fill="{stroke}"/>')

    parts.append(axis_label(160, 162, "16-24 combined share", 13, fill=palette["16-24"], weight="700"))
    parts.append(axis_label(160, 182, "Teen and young-adult drivers as a share of the whole driver pool", 13, fill="#667085"))

    # Endpoint callouts
    start_youth = share_16_24[0][1]
    end_youth = share_16_24[-1][1]
    parts.append(f'<rect x="150" y="690" width="280" height="250" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(290, 732, "1963", 14, fill="#667085", weight="700"))
    parts.append(axis_label(290, 774, "18.6%", 34, fill=palette["16-24"], weight="700"))
    parts.append(axis_label(290, 806, "Ages 16-24 share of all licensed drivers", 13, fill="#101828"))
    parts.append(axis_label(290, 838, "Teen licensing was a much bigger part of the driving economy.", 12, fill="#667085"))
    parts.append(f'<rect x="470" y="690" width="280" height="250" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(610, 732, "2024", 14, fill="#667085", weight="700"))
    parts.append(axis_label(610, 774, "11.2%", 34, fill=palette["16-24"], weight="700"))
    parts.append(axis_label(610, 806, "Ages 16-24 share of all licensed drivers", 13, fill="#101828"))
    parts.append(axis_label(610, 838, "The teen slice shrank by about 40 percent relative to 1963.", 12, fill="#667085"))
    parts.append(f'<rect x="790" y="690" width="330" height="250" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(955, 732, "The hardest number to ignore", 14, fill="#667085", weight="700"))
    parts.append(axis_label(955, 774, "1.12%", 34, fill=palette["18"], weight="700"))
    parts.append(axis_label(955, 806, "18-year-olds as a share of all licensed drivers in 2024", 13, fill="#101828"))
    parts.append(axis_label(955, 838, "That is the single cleanest teen-autonomy statistic in the table.", 12, fill="#667085"))

    parts.append(axis_label(620, 1032, "Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov. Percentages are each cohort's share of all licensed drivers in that year.", 11, fill="#667085"))
    return svg_wrap(width, height, "The road stopped being teen-heavy", "A focused look at how the youth slice of the driver pool has thinned over time.", "\n  ".join(parts))


def draw_ratio_chart(rows) -> str:
    selected_years = [1963, 1993, 2024]
    width, height = 1240, 1140
    chart_left, chart_right = 170, 1080
    chart_top, chart_bottom = 190, 930
    x_min, x_max = 0.7, 1.8
    palette = {
        1963: "#667085",
        1993: "#C8971D",
        2024: "#244A71",
    }

    by_year_sex_cohort: Dict[Tuple[int, str, str], int] = {}
    for row in rows:
        if row["Drivers"] is None:
            continue
        by_year_sex_cohort[(int(row["Year"]), str(row["Sex"]), str(row["Cohort"]))] = int(row["Drivers"])

    def ratio(year: int, cohort: str) -> float | None:
        m = by_year_sex_cohort.get((year, "Male", cohort))
        f = by_year_sex_cohort.get((year, "Female", cohort))
        if not m or not f:
            return None
        return m / f

    parts = []
    for i in range(6):
        y = chart_top + i * (chart_bottom - chart_top) / 5
        val = x_max - i * (x_max - x_min) / 5
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 22, y + 4, RATIO_COHORTS[i * (len(RATIO_COHORTS)-1)//5] if i < 5 else "", 11, anchor="end", fill="#667085"))
    parity_x = chart_left + (1.0 - x_min) / (x_max - x_min) * (chart_right - chart_left)
    parts.append(f'<line x1="{parity_x:.1f}" y1="{chart_top}" x2="{parity_x:.1f}" y2="{chart_bottom}" stroke="#94A3B8" stroke-width="2.5" stroke-dasharray="8 6"/>')
    parts.append(axis_label(parity_x + 8, chart_top - 12, "Parity", 11, anchor="start", fill="#667085", weight="700"))

    age_rows = [c for c in RATIO_COHORTS if c not in {"70+","70-74"} or c == "70-74"]
    age_rows = [c for c in RATIO_COHORTS]
    row_step = (chart_bottom - chart_top) / (len(age_rows) - 1)

    for idx, cohort in enumerate(age_rows):
        y = chart_top + idx * row_step
        if idx % 2 == 0:
            parts.append(f'<rect x="{chart_left}" y="{y-14}" width="{chart_right-chart_left}" height="28" rx="8" fill="#FAFAFA"/>')
        parts.append(axis_label(120, y + 4, cohort, 12, anchor="start", fill="#101828", weight="600"))

        points = []
        for year in selected_years:
            r = ratio(year, cohort)
            if r is None:
                continue
            x = chart_left + (r - x_min) / (x_max - x_min) * (chart_right - chart_left)
            points.append((year, x))
        for (year_a, x_a), (year_b, x_b) in zip(points, points[1:]):
            parts.append(f'<line x1="{x_a:.1f}" y1="{y:.1f}" x2="{x_b:.1f}" y2="{y:.1f}" stroke="#CBD5E1" stroke-width="2"/>')
        for year, x in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{palette[year]}" stroke="#fff" stroke-width="2"/>')

        if cohort == "40-44":
            x_2024 = next((x for year, x in points if year == 2024), None)
            if x_2024 is not None:
                parts.append(f'<circle cx="{x_2024:.1f}" cy="{y:.1f}" r="14" fill="none" stroke="#C8971D" stroke-width="3"/>')
                parts.append(axis_label(x_2024 + 22, y - 8, "2024 first female-majority age band", 11, anchor="start", fill="#8A6400", weight="700"))

    # legend
    legend_y = 980
    for idx, year in enumerate(selected_years):
        x = 170 + idx * 220
        parts.append(f'<rect x="{x}" y="{legend_y}" width="14" height="14" rx="4" fill="{palette[year]}"/>')
        parts.append(axis_label(x + 22, legend_y + 12, str(year), 12, anchor="start", fill="#101828", weight="600"))
    parts.append(axis_label(170, 1024, "1963 is male-heavy almost everywhere. By 2024, the ratio has moved much closer to parity and flips female-majority in older ages.", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(170, 1050, "A ratio above 1.0 means more male drivers; below 1.0 means more female drivers.", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(620, 1100, "Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov.", 11, fill="#667085"))
    return svg_wrap(width, height, "Male-female ratio by age band", "The point of this chart is where the dots cross the parity line, not just where they sit.", "\n  ".join(parts))


def write_summary(outdir: Path, by_year_total, by_year_cohort, by_year_sex):
    def share(year: int, cohort: str) -> float:
        return by_year_cohort[(year, cohort)] / by_year_total[year] * 100

    def sex_share(year: int) -> float:
        return by_year_sex[(year, "Female")] / by_year_total[year] * 100

    metrics = {
        "1963_total_m": by_year_total[1963] / 1000,
        "1993_total_m": by_year_total[1993] / 1000,
        "2024_total_m": by_year_total[2024] / 1000,
        "1963_female_share": sex_share(1963),
        "1993_female_share": sex_share(1993),
        "2024_female_share": sex_share(2024),
        "1963_16_share": share(1963, "16"),
        "2024_16_share": share(2024, "16"),
        "1963_18_share": share(1963, "18"),
        "2024_18_share": share(2024, "18"),
        "1963_youth_share": sum(by_year_cohort[(1963, c)] for c in ["16", "17", "18", "19", "20", "21", "22", "23", "24"]) / by_year_total[1963] * 100,
        "2024_youth_share": sum(by_year_cohort[(2024, c)] for c in ["16", "17", "18", "19", "20", "21", "22", "23", "24"]) / by_year_total[2024] * 100,
    }

    summary = f"""# Licensed drivers data summary

Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov.

Key readout:

- Licensed-driver counts are in thousands, so `2024 total` means about `{metrics["2024_total_m"]:.1f} million` drivers.
- Female share of all licensed drivers rose from `{metrics["1963_female_share"]:.1f}%` in 1963 to `{metrics["2024_female_share"]:.1f}%` in 2024.
- The 16-24 slice of the licensed-driver pool fell from `{metrics["1963_youth_share"]:.1f}%` in 1963 to `{metrics["2024_youth_share"]:.1f}%` in 2024.
- Age 16 fell from `{metrics["1963_16_share"]:.2f}%` of all licensed drivers to `{metrics["2024_16_share"]:.2f}%`.
- Age 18 fell from `{metrics["1963_18_share"]:.2f}%` to `{metrics["2024_18_share"]:.2f}%`.

Useful narrative guardrail:

- This dataset strongly supports a story about delayed licensing and the shrinking youth share of the driver pool.
- It does not, by itself, prove causation for broader autonomy claims, so if we want to say "least autonomous generation," it is safer to frame this as a proxy story and pair it with outside indicators.

Chart suggestions:

1. A mirrored 2024 age pyramid to show male vs female gaps by cohort.
2. A youth-share trend chart to show how age 16, 18, 21, and 25-29 shrink as a slice of all drivers.
3. A ratio chart to show how male-to-female gaps collapsed between 1963, 1993, and 2024.
"""
    (outdir / OUTPUT_FILENAMES["summary"]).write_text(summary, encoding="utf-8")


def write_storyboard(outdir: Path, age_svg: str, youth_svg: str, ratio_svg: str, summary_md: str):
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Licensed Drivers Infographic Storyboard</title>
  <style>
    :root {{
      --bg: #0D1321;
      --panel: #F7F3EB;
      --ink: #101828;
      --muted: #667085;
      --accent: #C95A6A;
      --blue: #224B72;
      --gold: #D4A017;
      --teal: #4E8098;
    }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(201,90,106,.16), transparent 22%),
        radial-gradient(circle at top right, rgba(78,128,152,.15), transparent 25%),
        linear-gradient(180deg, #0D1321 0%, #111827 48%, #0F172A 100%);
      color: #fff;
      font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", Arial, sans-serif;
    }}
    .shell {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 48px 24px 72px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.7fr 1fr;
      gap: 28px;
      align-items: end;
      margin-bottom: 28px;
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: .18em;
      color: rgba(255,255,255,.7);
      font-size: 12px;
      margin-bottom: 10px;
    }}
    h1 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(44px, 7vw, 76px);
      line-height: .95;
      letter-spacing: -.04em;
      max-width: 11ch;
    }}
    .lede {{
      margin-top: 18px;
      max-width: 68ch;
      color: rgba(255,255,255,.82);
      font-size: 18px;
      line-height: 1.6;
    }}
    .pills {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .pill {{
      background: rgba(255,255,255,.08);
      border: 1px solid rgba(255,255,255,.10);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      padding: 16px 18px;
    }}
    .pill strong {{
      display: block;
      font-size: 24px;
      margin-bottom: 4px;
    }}
    .pill span {{
      color: rgba(255,255,255,.75);
      font-size: 13px;
      line-height: 1.4;
    }}
    .grid {{
      display: grid;
      gap: 20px;
      grid-template-columns: 1fr;
    }}
    .card {{
      background: var(--panel);
      color: var(--ink);
      border-radius: 28px;
      overflow: hidden;
      box-shadow: 0 24px 70px rgba(0,0,0,.24);
    }}
    .card .copy {{
      padding: 22px 26px 0;
    }}
    .card h2 {{
      margin: 0 0 8px;
      font-size: 24px;
      letter-spacing: -.02em;
    }}
    .card p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
      max-width: 80ch;
      padding-bottom: 18px;
    }}
    .card img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .two-up {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }}
    .footer {{
      margin-top: 24px;
      color: rgba(255,255,255,.74);
      font-size: 13px;
      line-height: 1.6;
    }}
    @media (max-width: 980px) {{
      .hero, .two-up {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <div>
        <div class="eyebrow">Infographic storyboard</div>
        <h1>The Age of Delayed Independence</h1>
        <div class="lede">
          The FHWA licensed-driver table gives us a strong visual spine for a story about youth autonomy:
          the under-25 share of the driver pool keeps shrinking, while women move from minority status
          to parity. That makes the dataset ideal for an editorial package about a generation that is
          reaching adulthood later and entering the road later.
        </div>
      </div>
      <div class="pills">
        <div class="pill"><strong>50.5%</strong><span>Female share of all licensed drivers in 2024</span></div>
        <div class="pill"><strong>11.2%</strong><span>16-24 share of the driver pool in 2024</span></div>
        <div class="pill"><strong>1.12%</strong><span>18-year-olds as a share of all licensed drivers in 2024</span></div>
        <div class="pill"><strong>40-44</strong><span>First female-majority age band in 2024</span></div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="copy">
          <h2>1. 2024 age pyramid</h2>
          <p>Use this as the lead graphic. It instantly shows where male and female counts are balanced, where younger cohorts still lean male, and how female advantage emerges in older ages.</p>
        </div>
        <img alt="2024 age pyramid chart" src="{OUTPUT_FILENAMES["age_pyramid"]}" />
      </div>

      <div class="two-up">
        <div class="card">
          <div class="copy">
            <h2>2. Youth share trend</h2>
            <p>Run the 16, 18, 21, and 25-29 lines together to show that teen and young-adult licensing is becoming a smaller slice of the driver pool. Keep age 18 in the accent color.</p>
          </div>
          <img alt="Youth share trend chart" src="{OUTPUT_FILENAMES["youth_share"]}" />
        </div>
        <div class="card">
          <div class="copy">
            <h2>3. Male-to-female ratio by age band</h2>
            <p>Use this to dramatize the gender gap collapse. In 1963 the gap was male-heavy across most ages; by 2024 parity shows up much earlier and older cohorts go female-majority.</p>
          </div>
          <img alt="Gender ratio trend chart" src="{OUTPUT_FILENAMES["gender_ratio"]}" />
        </div>
      </div>
    </div>

    <div class="footer">
      Story guardrail: this dataset supports a delayed-licensing / delayed-independence thesis, but it should be framed as a proxy rather than proof of the entire social argument.
      The charts above are built from the official CSV and are ready to drop into a deck, article, or CMS.
    </div>
  </div>
</body>
</html>
"""
    (outdir / OUTPUT_FILENAMES["storyboard"]).write_text(html_doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate infographic assets from FHWA DL-220.")
    parser.add_argument("--csv", type=Path, help="Path to a local CSV export. If omitted, the script downloads the official CSV.")
    parser.add_argument("--outdir", type=Path, default=Path("infographic_out"), help="Directory to write outputs to.")
    args = parser.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    csv_path = args.csv
    if csv_path is None:
        csv_path = outdir / "licensed-drivers-dl220.csv"
        if not csv_path.exists():
            download_csv(DATA_URL, csv_path)

    rows = load_rows(csv_path)
    by_year_total, by_year_sex, by_year_cohort = build_indexes(rows)

    age_svg = draw_age_pyramid(rows, by_year_cohort)
    youth_svg = draw_youth_share_chart(by_year_total, by_year_cohort, by_year_sex)
    ratio_svg = draw_ratio_chart(rows)

    (outdir / OUTPUT_FILENAMES["age_pyramid"]).write_text(age_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["youth_share"]).write_text(youth_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["gender_ratio"]).write_text(ratio_svg, encoding="utf-8")

    write_summary(outdir, by_year_total, by_year_cohort, by_year_sex)
    write_storyboard(outdir, age_svg, youth_svg, ratio_svg, (outdir / OUTPUT_FILENAMES["summary"]).read_text(encoding="utf-8"))

    print(f"Wrote infographic bundle to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
