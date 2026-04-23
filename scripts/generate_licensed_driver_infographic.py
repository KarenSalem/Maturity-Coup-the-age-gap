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
    "age_split": "licensed-drivers-age-split-16-21.svg",
    "age_rate": "licensed-drivers-age-rate-2010-2024.svg",
    "age_18_callout": "licensed-drivers-18-year-old-callout.svg",
    "age_18_mini": "licensed-drivers-18-year-old-mini.svg",
    "youth_share": "licensed-drivers-youth-shares.svg",
    "overlay": "licensed-drivers-youth-work-overlay.svg",
    "overlay_data": "licensed-drivers-youth-work-overlay.csv",
    "gender_ratio": "licensed-drivers-gender-ratio-trends.svg",
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

SMALL_MULTIPLE_COHORTS = ["16", "17", "18", "19", "20", "21"]

AGE_RATE_TREND = {
    2010: {"16": 28.7, "17": 47.1, "18": 62.2, "19": 71.1, "20": 78.9, "21": 80.9},
    2012: {"16": 28.2, "17": 45.6, "18": 59.0, "19": 68.0, "20": 71.6, "21": 73.6},
    2014: {"16": 24.5, "17": 44.9, "18": 60.1, "19": 69.0, "20": 72.9, "21": 74.4},
    2016: {"16": 26.3, "17": 46.9, "18": 62.1, "19": 71.6, "20": 75.8, "21": 77.3},
    2018: {"16": 25.8, "17": 46.6, "18": 60.9, "19": 71.3, "20": 76.0, "21": 78.2},
    2020: {"16": 25.1, "17": 44.7, "18": 58.0, "19": 67.7, "20": 75.8, "21": 78.2},
    2022: {"16": 24.9, "17": 43.0, "18": 59.8, "19": 68.7, "20": 72.2, "21": 72.5},
    2024: {"16": 26.2, "17": 44.4, "18": 60.4, "19": 68.8, "20": 75.4, "21": 79.3},
}

AGE_RATE_YEARS = sorted(AGE_RATE_TREND)

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


def draw_age_small_multiples(by_year_total, by_year_cohort) -> str:
    years = sorted(by_year_total)
    width, height = 1240, 920
    left_margin, right_margin = 56, 56
    top_margin = 138
    panel_w = (width - left_margin - right_margin - 24) / 2
    panel_h = 206
    row_gap = 18
    col_gap = 24
    plot_y_min, plot_y_max = 0.0, 3.0
    tick_years = [1963, 1993, 2024]
    accent = {
        "16": "#4E8098",
        "17": "#334E68",
        "18": "#C65A6A",
        "19": "#C8971D",
        "20": "#244A71",
        "21": "#7A1F2B",
    }

    def share_series(cohort: str):
        return [(year, by_year_cohort[(year, cohort)] / by_year_total[year] * 100) for year in years]

    def panel(x: float, y: float, cohort: str, series):
        inner_left = x + 18
        inner_right = x + panel_w - 18
        inner_top = y + 44
        inner_bottom = y + 162
        line_color = accent[cohort]
        points = line_points(series, inner_left, inner_right, inner_top, inner_bottom, years[0], years[-1], plot_y_min, plot_y_max)
        start_val = series[0][1]
        end_val = series[-1][1]

        bg = "#FFF7F8" if cohort == "18" else "#FFFFFF"
        parts = [
            f'<rect x="{x}" y="{y}" width="{panel_w:.1f}" height="{panel_h}" rx="24" fill="{bg}" stroke="#E5E7EB"/>',
            axis_label(x + 18, y + 28, cohort, 19, anchor="start", fill="#101828", weight="700"),
            axis_label(x + panel_w - 18, y + 28, f"{start_val:.2f}% \u2192 {end_val:.2f}%", 12, anchor="end", fill=line_color, weight="700"),
            axis_label(x + 18, y + 60, "share of all licensed drivers", 11, anchor="start", fill="#667085"),
        ]

        for tick in [0.0, 1.0, 2.0, 3.0]:
            ty = inner_bottom - (tick - plot_y_min) / (plot_y_max - plot_y_min) * (inner_bottom - inner_top)
            parts.append(f'<line x1="{inner_left}" y1="{ty:.1f}" x2="{inner_right}" y2="{ty:.1f}" stroke="#EEF2F7" stroke-width="1"/>')

        for year in tick_years:
            tx = inner_left + (year - years[0]) / (years[-1] - years[0]) * (inner_right - inner_left)
            parts.append(f'<line x1="{tx:.1f}" y1="{inner_top}" x2="{tx:.1f}" y2="{inner_bottom}" stroke="#F8FAFC" stroke-width="1"/>')
            parts.append(axis_label(tx, inner_bottom + 22, str(year), 10, fill="#667085"))

        for tick in [0.0, 1.0, 2.0, 3.0]:
            ty = inner_bottom - (tick - plot_y_min) / (plot_y_max - plot_y_min) * (inner_bottom - inner_top)
            parts.append(axis_label(inner_left - 8, ty + 4, f"{tick:.0f}%", 10, anchor="end", fill="#667085"))

        poly = " ".join(f"{xv:.1f},{yv:.1f}" for xv, yv in points)
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{line_color}" stroke-width="3.5"/>')
        parts.append(f'<circle cx="{points[0][0]:.1f}" cy="{points[0][1]:.1f}" r="4.8" fill="{line_color}"/>')
        parts.append(f'<circle cx="{points[-1][0]:.1f}" cy="{points[-1][1]:.1f}" r="4.8" fill="{line_color}"/>')

        # Endpoint callouts.
        parts.append(axis_label(points[0][0] + 2, points[0][1] - 10, f"{start_val:.2f}%", 11, anchor="start", fill=line_color, weight="700"))
        parts.append(axis_label(points[-1][0] - 2, points[-1][1] - 10, f"{end_val:.2f}%", 11, anchor="end", fill=line_color, weight="700"))
        return parts

    parts = []

    for idx, cohort in enumerate(SMALL_MULTIPLE_COHORTS):
        row = idx // 2
        col = idx % 2
        x = left_margin + col * (panel_w + col_gap)
        y = top_margin + row * (panel_h + row_gap)
        parts.extend(panel(x, y, cohort, share_series(cohort)))

    parts.append(axis_label(620, 905, "Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov. Percentages are each cohort's share of all licensed drivers in that year.", 11, anchor="middle", fill="#667085"))
    return svg_wrap(
        width,
        height,
        "Age-by-age youth share",
        "Six panels, one age each: 16 through 21. The 18-year-old panel is highlighted because it is the cleanest autonomy signal.",
        "\n  ".join(parts),
    )


def draw_age_rate_chart() -> str:
    width, height = 1240, 920
    chart_left, chart_right = 190, 1110
    chart_top, chart_bottom = 190, 680
    years = AGE_RATE_YEARS
    ages = ["16", "17", "18", "19", "20", "21"]
    y_min, y_max = 20.0, 85.0
    colors = {
        "16": "#4E8098",
        "17": "#5A7184",
        "18": "#C65A6A",
        "19": "#C8971D",
        "20": "#244A71",
        "21": "#7A1F2B",
    }

    parts = []
    parts.append(axis_label(56, 146, "Licensed share by age, 2010 to 2024", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(56, 170, "FHWA Table DL-20 shows how likely each age was to be licensed across eight snapshots.", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(56, 192, "The 18-year-old line is the clearest hinge: 62.2% in 2010, 59.0% in 2012, 60.1% in 2014, 62.1% in 2016, and 60.4% in 2024.", 13, anchor="start", fill="#667085"))

    for i in range(6):
        y = chart_top + i * (chart_bottom - chart_top) / 5
        val = y_max - i * (y_max - y_min) / 5
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 16, y + 4, f"{val:.0f}%", 11, anchor="end", fill="#667085"))

    for year in years:
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    for age in ages:
        series = [(year, AGE_RATE_TREND[year][age]) for year in years]
        plotted = line_points(series, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
        line_color = colors[age]
        width_line = 5 if age == "18" else 3.5
        opacity = "0.98" if age == "18" else "0.92"
        dash = ' stroke-dasharray="6 4"' if age in {"16", "17"} else ""
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{line_color}" stroke-width="{width_line}" opacity="{opacity}"{dash}/>')
        for x, y in plotted:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" fill="{line_color}" stroke="#fff" stroke-width="2"/>')

        x_end, y_end = plotted[-1]
        end_val = series[-1][1]
        parts.append(axis_label(x_end + 10, y_end - 10, f"{age}: {end_val:.1f}%", 11, anchor="start", fill=line_color, weight="700"))

    # Highlight 18-year-olds.
    x18 = chart_left + (2024 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
    y18 = chart_bottom - (AGE_RATE_TREND[2024]["18"] - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
    parts.append(f'<circle cx="{x18:.1f}" cy="{y18:.1f}" r="13" fill="none" stroke="#C65A6A" stroke-width="3"/>')
    parts.append(axis_label(x18 + 18, y18 - 12, "18-year-olds in 2024", 11, anchor="start", fill="#8A1F2F", weight="700"))

    parts.append(f'<rect x="710" y="742" width="420" height="54" rx="18" fill="#F8FAFC" stroke="#E5E7EB"/>')
    parts.append(axis_label(920, 776, "At 18, the rate stayed near 60% across eight snapshots.", 13, anchor="middle", fill="#101828", weight="700"))
    parts.append(axis_label(620, 882, "Source: FHWA Table DL-20, Licensed Drivers: Distribution by Sex and Age Group Relative to Population (2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024).", 11, anchor="middle", fill="#667085"))
    return svg_wrap(width, height, "How close each age is to licensure", "A denominator-based view of licensed drivers by age across 2010, 2012, 2014, 2016, 2018, 2020, 2022, and 2024.", "\n  ".join(parts))


def draw_age_18_callout() -> str:
    width, height = 1240, 760
    chart_left, chart_right = 160, 1080
    chart_top, chart_bottom = 240, 560
    years = AGE_RATE_YEARS
    values = [AGE_RATE_TREND[y]["18"] for y in years]
    y_min, y_max = 56.0, 62.5

    parts = []
    parts.append(axis_label(56, 148, "18-year-olds", 52, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(56, 184, "The cleanest autonomy marker in the driver table.", 18, anchor="start", fill="#475467"))
    parts.append(axis_label(56, 210, "Licensed share of 18-year-olds: 62.2% in 2010, 59.0% in 2012, 60.1% in 2014, 62.1% in 2016, 60.9% in 2018, 58.0% in 2020, 59.8% in 2022, 60.4% in 2024.", 13, anchor="start", fill="#667085"))

    # Main number block.
    parts.append(f'<rect x="56" y="252" width="240" height="176" rx="28" fill="#111827"/>')
    parts.append(axis_label(176, 316, "60.4%", 56, anchor="middle", fill="#FFFFFF", weight="700"))
    parts.append(axis_label(176, 360, "licensed in 2024", 18, anchor="middle", fill="#D1D5DB"))
    parts.append(axis_label(176, 392, "FHWA DL-20 age-rate table", 12, anchor="middle", fill="#9CA3AF"))

    # Sparkline plot.
    for i in range(6):
        y = chart_top + i * (chart_bottom - chart_top) / 5
        val = y_max - i * (y_max - y_min) / 5
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 16, y + 4, f"{val:.1f}%", 11, anchor="end", fill="#667085"))
    for year in years:
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 22, str(year), 10, fill="#667085"))

    series = list(zip(years, values))
    plotted = line_points(series, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#C65A6A" stroke-width="5"/>')
    for x, y in plotted:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#C65A6A" stroke="#fff" stroke-width="2"/>')
    parts.append(f'<circle cx="{plotted[-1][0]:.1f}" cy="{plotted[-1][1]:.1f}" r="14" fill="none" stroke="#C65A6A" stroke-width="3"/>')
    parts.append(axis_label(plotted[-1][0] + 18, plotted[-1][1] - 12, "2024", 11, anchor="start", fill="#8A1F2F", weight="700"))

    # Year chips.
    left_x = 390
    right_x = 710
    chip_w = 300
    chip_h = 42
    chip_cols = [(left_x, 0), (right_x, 4)]
    for chip_x, start_idx in chip_cols:
        for offset in range(4):
            idx = start_idx + offset
            year = years[idx]
            value = values[idx]
            y = 268 + offset * 58
            parts.append(f'<rect x="{chip_x}" y="{y}" width="{chip_w}" height="{chip_h}" rx="16" fill="#FFF7F8" stroke="#F3D7DB"/>')
            parts.append(axis_label(chip_x + 18, y + 26, str(year), 12, anchor="start", fill="#667085", weight="700"))
            parts.append(axis_label(chip_x + 110, y + 26, f"{value:.1f}%", 14, anchor="start", fill="#C65A6A", weight="700"))

    parts.append(f'<rect x="390" y="520" width="620" height="88" rx="22" fill="#F8FAFC" stroke="#E5E7EB"/>')
    parts.append(axis_label(700, 548, "This age stays right around 60%, even across a longer pre-pandemic baseline.", 14, anchor="middle", fill="#101828", weight="700"))
    parts.append(axis_label(700, 570, "That makes 18 the best single-age proxy for the story.", 12, anchor="middle", fill="#667085"))
    parts.append(axis_label(620, 732, "Source: FHWA Table DL-20, Licensed Drivers: Distribution by Sex and Age Group Relative to Population.", 11, anchor="middle", fill="#667085"))
    return svg_wrap(width, height, "The 18-year-old callout", "A compact view of the strongest quote-ready number in the licensed-driver data.", "\n  ".join(parts))


def draw_age_18_mini() -> str:
    width, height = 920, 360
    chart_left, chart_right = 340, 848
    chart_top, chart_bottom = 128, 252
    years = AGE_RATE_YEARS
    values = [AGE_RATE_TREND[y]["18"] for y in years]
    y_min, y_max = 56.0, 64.0

    parts = []
    parts.append(axis_label(44, 74, "18-year-olds", 28, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(44, 106, "The cleanest single-age anchor in the DL-20 rate table.", 14, anchor="start", fill="#475467"))
    parts.append(axis_label(44, 138, "60.4% licensed in 2024", 34, anchor="start", fill="#C65A6A", weight="700"))

    for i in range(5):
        y = chart_top + i * (chart_bottom - chart_top) / 4
        val = y_max - i * (y_max - y_min) / 4
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 10, y + 4, f"{val:.0f}%", 10, anchor="end", fill="#667085"))

    for year in years:
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F3F4F6" stroke-width="1"/>')

    series = list(zip(years, values))
    plotted = line_points(series, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#C65A6A" stroke-width="4.5"/>')
    for x, y in plotted:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" fill="#C65A6A" stroke="#fff" stroke-width="2"/>')

    parts.append(axis_label(chart_left, 272, "2010", 10, anchor="start", fill="#667085"))
    parts.append(axis_label(chart_right, 272, "2024", 10, anchor="end", fill="#667085"))
    parts.append(axis_label(chart_right - 6, plotted[-1][1] - 10, "2024", 10, anchor="start", fill="#8A1F2F", weight="700"))
    parts.append(axis_label(620, 330, "Source: FHWA DL-20 age-rate tables, 2010 to 2024.", 11, anchor="middle", fill="#667085"))

    return svg_wrap(width, height, "18-year-old rate, compact view", "A minimal backup card that isolates the single age at the center of the story.", "\n  ".join(parts))


def draw_youth_share_chart(by_year_total, by_year_cohort, by_year_sex) -> str:
    years = sorted(by_year_total)
    bundle_16_18 = []
    share_18 = []
    for year in years:
        total = by_year_total[year]
        youth = sum(by_year_cohort[(year, c)] for c in ["16", "17", "18"])
        bundle_16_18.append((year, youth / total * 100))
        share_18.append((year, by_year_cohort[(year, "18")] / total * 100))

    width, height = 1240, 1100
    chart_left, chart_right = 120, 1130
    chart_top = 180
    chart_h = 440
    year_min, year_max = years[0], years[-1]

    palette = {
        "16-18": "#0F172A",
        "18": "#C65A6A",
        "context": "#4E8098",
    }

    parts = []
    y_min, y_max = 0.0, 8.0
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
    parts.append(f'<rect x="{chart_left}" y="{chart_top + 140}" width="{chart_right-chart_left}" height="120" rx="20" fill="#FFF6EF" opacity="0.95"/>')

    for cohort, pts, stroke, width_line, opacity, dash in [
        ("16-18", bundle_16_18, palette["16-18"], 5, "0.96", ""),
        ("18", share_18, palette["18"], 3.25, "0.94", ' stroke-dasharray="7 5"'),
    ]:
        plotted = line_points(pts, chart_left, chart_right, chart_top, chart_top + chart_h, year_min, year_max, y_min, y_max)
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{stroke}" stroke-width="{width_line}" opacity="{opacity}"{dash}/>')
        if plotted:
            x0, y0p = plotted[0]
            x1, y1p = plotted[-1]
            parts.append(f'<circle cx="{x0:.1f}" cy="{y0p:.1f}" r="5" fill="{stroke}"/>')
            parts.append(f'<circle cx="{x1:.1f}" cy="{y1p:.1f}" r="5" fill="{stroke}"/>')

    parts.append(axis_label(160, 162, "16-18 combined share", 13, fill=palette["16-18"], weight="700"))
    parts.append(axis_label(160, 182, "Ages 16, 17, and 18 as a share of all licensed drivers", 13, fill="#667085"))

    # Endpoint callouts
    parts.append(f'<rect x="150" y="690" width="280" height="250" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(290, 732, "1963", 14, fill="#667085", weight="700"))
    parts.append(axis_label(290, 774, "5.40%", 34, fill=palette["16-18"], weight="700"))
    parts.append(axis_label(290, 806, "Ages 16-18 share of all licensed drivers", 13, fill="#101828"))
    parts.append(axis_label(290, 838, "Teen licensing was a much bigger part of the driving economy.", 12, fill="#667085"))
    parts.append(f'<rect x="470" y="690" width="280" height="250" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(610, 732, "2024", 14, fill="#667085", weight="700"))
    parts.append(axis_label(610, 774, "2.46%", 34, fill=palette["16-18"], weight="700"))
    parts.append(axis_label(610, 806, "Ages 16-18 share of all licensed drivers", 13, fill="#101828"))
    parts.append(axis_label(610, 838, "The teen slice is still much smaller than it was before adulthood got delayed.", 12, fill="#667085"))
    parts.append(f'<rect x="790" y="690" width="330" height="250" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(955, 732, "The hardest number to ignore", 14, fill="#667085", weight="700"))
    parts.append(axis_label(955, 774, "1.12%", 34, fill=palette["18"], weight="700"))
    parts.append(axis_label(955, 806, "18-year-olds as a share of all licensed drivers in 2024", 13, fill="#101828"))
    parts.append(axis_label(955, 838, "That is the single cleanest teen-autonomy statistic in the table.", 12, fill="#667085"))

    parts.append(axis_label(620, 1032, "Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov. Percentages are each cohort's share of all licensed drivers in that year.", 11, fill="#667085"))
    return svg_wrap(width, height, "The road stopped being teen-heavy", "A focused look at how the youth slice of the driver pool has thinned over time.", "\n  ".join(parts))


def load_july_youth_history(outdir: Path) -> Dict[int, float]:
    history_path = Path(__file__).resolve().parents[1] / "bls/july-youth-lfpr-history.csv"
    series: Dict[int, float] = {}
    with history_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            series[int(row["Year"])] = float(row["Total"])

    # Append the current BLS TED update so the bridge chart can reach 2024.
    current_path = Path(__file__).resolve().parents[1] / "bls/july-youth-lfpr.csv"
    if current_path.exists():
        with current_path.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                series[int(row["Year"])] = float(row["Total"])
    return series


def draw_youth_work_overlay_chart(by_year_total, by_year_cohort, youth_history) -> str:
    years = [year for year in sorted(by_year_total) if year in youth_history]
    years = [year for year in years if year >= 1963]

    def youth_share(year: int) -> float:
        return sum(by_year_cohort[(year, c)] for c in ["16", "17", "18"]) / by_year_total[year] * 100

    youth_series = [(year, youth_history[year]) for year in years]
    license_series = [(year, youth_share(year)) for year in years]

    base_year = years[0]
    youth_base = youth_history[base_year]
    license_base = youth_share(base_year)

    youth_index = [(year, val / youth_base * 100) for year, val in youth_series]
    license_index = [(year, val / license_base * 100) for year, val in license_series]

    width, height = 1320, 1020
    chart_left, chart_right = 120, 1140
    chart_top, chart_bottom = 180, 670
    y_min, y_max = 40, 125

    parts = []
    parts.append(axis_label(120, 132, "Indexed youth work and teen licensing", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(120, 154, "Both series are indexed to 1963 = 100 so we can compare the direction of change cleanly.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(120, 178, "July youth LFPR for ages 16-24 vs. ages 16-18 as a share of all licensed drivers.", 13, anchor="start", fill="#667085"))

    for i in range(6):
        y = chart_top + i * (chart_bottom - chart_top) / 5
        val = y_max - i * (y_max - y_min) / 5
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 18, y + 4, f"{val:.0f}", 11, anchor="end", fill="#667085"))

    for year in range(base_year, years[-1] + 1, 5):
        x = chart_left + (year - base_year) / (years[-1] - base_year) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    for label, series, color, width_line, dash in [
        ("Youth work", youth_index, "#244A71", 4, ""),
        ("Teen licensure", license_index, "#C65A6A", 4, ' stroke-dasharray="8 5"'),
    ]:
        plotted = line_points(series, chart_left, chart_right, chart_top, chart_bottom, base_year, years[-1], y_min, y_max)
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="{width_line}" stroke-linecap="round" stroke-linejoin="round"{dash}/>')
        for x, y in plotted[:: max(1, len(plotted) // 8)]:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}"/>')

    # Reference line at 100.
    ref_y = chart_bottom - (100 - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
    parts.append(f'<line x1="{chart_left}" y1="{ref_y:.1f}" x2="{chart_right}" y2="{ref_y:.1f}" stroke="#94A3B8" stroke-width="2.5" stroke-dasharray="8 6"/>')
    parts.append(axis_label(chart_right, ref_y - 10, "1963 = 100", 11, anchor="end", fill="#64748B", weight="700"))

    # Endpoint cards.
    def pct_change(base: float, end: float) -> float:
        return (end / base - 1.0) * 100

    youth_end = youth_series[-1][1]
    license_end = license_series[-1][1]
    youth_2024 = youth_series[-1][1]
    license_2024 = license_series[-1][1]

    cards = [
        (120, 730, "Youth work", f"{youth_base:.1f}% -> {youth_2024:.1f}%", f"{youth_index[0][1]:.0f} -> {youth_index[-1][1]:.0f} indexed", f"{pct_change(youth_base, youth_2024):+.1f}% since 1963"),
        (460, 730, "Teen licensure", f"{license_base:.2f}% -> {license_2024:.2f}%", f"{license_index[0][1]:.0f} -> {license_index[-1][1]:.0f} indexed", f"{pct_change(license_base, license_2024):+.1f}% since 1963"),
        (800, 730, "Shared years", f"{base_year} to {years[-1]}", "BLS youth series + FHWA DL-220", "Indexed to the same starting point"),
    ]
    for x, y, title, big, sub, note in cards:
        parts.append(f'<rect x="{x}" y="{y}" width="280" height="220" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
        parts.append(axis_label(x + 140, y + 34, title, 13, fill="#667085", weight="700"))
        parts.append(axis_label(x + 140, y + 84, big, 30, fill="#101828", weight="700"))
        parts.append(axis_label(x + 140, y + 118, sub, 12, fill="#244A71" if title == "Youth work" else "#C65A6A" if title == "Teen licensure" else "#101828"))
        parts.append(axis_label(x + 140, y + 154, note, 12, fill="#667085"))

    parts.append(axis_label(120, 960, "Source: BLS July youth labor-force participation series, with 2024 appended from the current TED update; FHWA DL-220 licensed-driver counts via data.transportation.gov.", 11, anchor="start", fill="#667085"))
    parts.append(axis_label(120, 982, "The licensure line uses ages 16-18 as a share of all licensed drivers. The chart is indexed because the base rates are very different.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "Summer work and teen licensing moved together", "Indexed to 1963 = 100 so the direction of travel is easy to compare across two different measures.", "\n  ".join(parts))


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

    def share_bundle(year: int, cohorts: Sequence[str]) -> float:
        return sum(by_year_cohort[(year, cohort)] for cohort in cohorts) / by_year_total[year] * 100

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
        "1963_16_18_share": share_bundle(1963, ["16", "17", "18"]),
        "2024_16_18_share": share_bundle(2024, ["16", "17", "18"]),
        "1963_youth_share": sum(by_year_cohort[(1963, c)] for c in ["16", "17", "18", "19", "20", "21", "22", "23", "24"]) / by_year_total[1963] * 100,
        "2024_youth_share": sum(by_year_cohort[(2024, c)] for c in ["16", "17", "18", "19", "20", "21", "22", "23", "24"]) / by_year_total[2024] * 100,
    }

    summary = f"""# Licensed drivers data summary

Source: FHWA Highway Statistics Table DL-220 via data.transportation.gov.

Key readout:

- Licensed-driver counts are in thousands, so `2024 total` means about `{metrics["2024_total_m"]:.1f} million` drivers.
- Female share of all licensed drivers rose from `{metrics["1963_female_share"]:.1f}%` in 1963 to `{metrics["2024_female_share"]:.1f}%` in 2024.
- The 16-18 slice of the licensed-driver pool fell from `{metrics["1963_16_18_share"]:.1f}%` in 1963 to `{metrics["2024_16_18_share"]:.1f}%` in 2024.
- The 16-24 slice of the licensed-driver pool fell from `{metrics["1963_youth_share"]:.1f}%` in 1963 to `{metrics["2024_youth_share"]:.1f}%` in 2024.
- Age 16 fell from `{metrics["1963_16_share"]:.2f}%` of all licensed drivers to `{metrics["2024_16_share"]:.2f}%`.
- Age 18 fell from `{metrics["1963_18_share"]:.2f}%` to `{metrics["2024_18_share"]:.2f}%`.

Useful narrative guardrail:

- This dataset strongly supports a story about delayed licensing and the shrinking youth share of the driver pool.
- It does not, by itself, prove causation for broader autonomy claims, so if we want to say "least autonomous generation," it is safer to frame this as a proxy story and pair it with outside indicators.

Chart suggestions:

1. A mirrored 2024 age pyramid to show male vs female gaps by cohort.
2. A youth-share trend chart to show how the 16-18 bundle shrinks as a slice of all drivers.
3. A ratio chart to show how male-to-female gaps collapsed between 1963, 1993, and 2024.
"""
    (outdir / OUTPUT_FILENAMES["summary"]).write_text(summary, encoding="utf-8")


def write_overlay_data(outdir: Path, by_year_total, by_year_cohort, youth_history):
    years = [year for year in sorted(by_year_total) if year in youth_history and year >= 1963]
    base_year = years[0]

    def youth_share(year: int) -> float:
        return sum(by_year_cohort[(year, c)] for c in ["16", "17", "18"]) / by_year_total[year] * 100

    youth_base = youth_history[base_year]
    license_base = youth_share(base_year)

    lines = ["Year,YouthJulLFPR,Licensed16_18Share,YouthJulLFPR_Index1963,Licensed16_18Share_Index1963"]
    for year in years:
        youth = youth_history[year]
        license_share = youth_share(year)
        lines.append(
            f"{year},{youth:.1f},{license_share:.2f},{youth / youth_base * 100:.1f},{license_share / license_base * 100:.1f}"
        )

    (outdir / OUTPUT_FILENAMES["overlay_data"]).write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        <div class="pill"><strong>2.46%</strong><span>Ages 16-18 share of the driver pool in 2024</span></div>
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
            <p>Bundle ages 16, 17, and 18 into one series to show the pre-19 slice more cleanly. Keep age 18 in the accent color as the comparison point.</p>
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
    parser.add_argument("--outdir", type=Path, default=Path("licensed-drivers"), help="Directory to write outputs to.")
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
    youth_history = load_july_youth_history(outdir)

    age_svg = draw_age_pyramid(rows, by_year_cohort)
    age_split_svg = draw_age_small_multiples(by_year_total, by_year_cohort)
    age_rate_svg = draw_age_rate_chart()
    age_18_svg = draw_age_18_callout()
    age_18_mini_svg = draw_age_18_mini()
    youth_svg = draw_youth_share_chart(by_year_total, by_year_cohort, by_year_sex)
    overlay_svg = draw_youth_work_overlay_chart(by_year_total, by_year_cohort, youth_history)
    ratio_svg = draw_ratio_chart(rows)

    (outdir / OUTPUT_FILENAMES["age_pyramid"]).write_text(age_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["age_split"]).write_text(age_split_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["age_rate"]).write_text(age_rate_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["age_18_callout"]).write_text(age_18_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["age_18_mini"]).write_text(age_18_mini_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["youth_share"]).write_text(youth_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["overlay"]).write_text(overlay_svg, encoding="utf-8")
    (outdir / OUTPUT_FILENAMES["gender_ratio"]).write_text(ratio_svg, encoding="utf-8")
    write_overlay_data(outdir, by_year_total, by_year_cohort, youth_history)

    print(f"Wrote infographic bundle to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
