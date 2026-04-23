#!/usr/bin/env python3
"""Generate a high-end editorial package from official BLS youth labor data.

This piece is intentionally separate from the licensed-driver story.
It focuses on teen labor force participation, summer youth participation,
and current age-specific participation rates using official BLS sources.
"""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def axis_label(x: float, y: float, text: str, size: int = 12, anchor: str = "middle", fill: str = "#667085", weight: str = "400") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="Arial, Helvetica, sans-serif" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(text)}</text>'


def svg_wrap(width: int, height: int, title: str, subtitle: str, body: str, background: str = "#FFFDF8") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
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
  <text x="52" y="72" font-size="30" font-family="Georgia, 'Times New Roman', serif" font-weight="700" fill="#101828">{esc(title)}</text>
  <text x="52" y="102" font-size="14" font-family="Arial, Helvetica, sans-serif" fill="#475467">{esc(subtitle)}</text>
  {body}
</svg>"""


def line_points(series, x0, x1, y0, y1, xmin, xmax, ymin, ymax):
    pts = []
    span_x = xmax - xmin
    span_y = ymax - ymin
    for year, value in series:
        x = x0 + (year - xmin) / span_x * (x1 - x0)
        y = y1 - (value - ymin) / span_y * (y1 - y0)
        pts.append((x, y))
    return pts


ANNUAL_TEEN = [
    (1948, 52.5), (1950, 51.8), (1955, 48.9), (1960, 47.5), (1963, 45.2), (1964, 44.5),
    (1966, 48.2), (1969, 49.4), (1970, 49.9), (1972, 51.9), (1973, 53.7), (1974, 54.8),
    (1976, 54.5), (1977, 56.0), (1978, 57.8), (1979, 57.9), (1980, 56.7), (1983, 53.5),
    (1985, 54.5), (1989, 55.9), (1990, 53.7), (1993, 51.5), (1995, 53.5), (1999, 52.0),
    (2000, 52.0), (2001, 49.6), (2003, 44.5), (2004, 43.9), (2007, 41.3), (2008, 40.2),
    (2009, 37.5), (2010, 34.9), (2011, 34.1), (2014, 34.0), (2015, 34.3),
]

JULY_YOUTH = [
    (1989, 77.5, 82.8, 72.4),
    (1990, 75.1, 80.8, 69.5),
    (1991, 73.6, 79.6, 67.6),
    (1994, 74.1, 78.8, 69.4),
    (1998, 72.8, 76.3, 69.3),
    (2000, 71.6, 75.2, 68.1),
    (2003, 67.3, 70.0, 64.5),
    (2007, 65.0, 67.9, 62.1),
    (2009, 63.0, 64.9, 61.1),
    (2010, 60.5, 62.7, 58.1),
    (2014, 60.5, 63.2, 57.8),
    (2016, 60.1, 62.4, 57.7),
    (2019, 61.8, 63.2, 60.4),
    (2020, 57.3, 58.4, 56.2),
    (2021, 60.5, 61.8, 59.1),
    (2022, 60.4, 61.7, 59.2),
    (2023, 60.2, 60.4, 60.0),
    (2024, 60.4, 61.2, 59.6),
]

AGE_GRADIENT = {
    2004: {"16-19": 43.9, "16-24": 61.1, "20-24": 75.0, "25-54": 82.8, "55+": 43.2},
    2014: {"16-19": 34.0, "16-24": 55.0, "20-24": 70.8, "25-54": 80.9, "55+": 45.9},
    2024: {"16-19": 36.9, "16-24": 55.9, "20-24": 71.5, "25-54": 83.6, "55+": 43.9},
    2034: {"16-19": 34.6, "16-24": 53.6, "20-24": 69.1, "25-54": 82.8, "55+": 41.6},
}

def draw_annual_chart() -> str:
    width, height = 1220, 840
    chart_left, chart_right = 110, 1120
    chart_top, chart_bottom = 170, 600
    years = [y for y, _ in ANNUAL_TEEN]
    y_min, y_max = 30, 60

    parts = []
    parts.append(axis_label(110, 132, "Teen labor force participation, annual averages", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(110, 154, "The school-year labor market for 16- to 19-year-olds lost its postwar baseline.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(110, 178, "Annual average series from BLS MLR. Highlighted markers: 1979 peak, 1989, 2015.", 13, anchor="start", fill="#667085"))

    for i in range(7):
        y = chart_top + i * (chart_bottom - chart_top) / 6
        val = y_max - i * (y_max - y_min) / 6
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 16, y + 4, f"{val:.0f}%", 11, anchor="end", fill="#667085"))

    for year in range(1950, 2016, 10):
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    plotted = line_points(ANNUAL_TEEN, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#244A71" stroke-width="4"/>')
    for x, y in plotted:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#244A71"/>')

    highlights = {1979: 57.9, 1989: 55.9, 2015: 34.3}
    for year, value in highlights.items():
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        y = chart_bottom - (value - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="none" stroke="#C8971D" stroke-width="3"/>')
        parts.append(axis_label(x, y - 16, f"{year} {value:.1f}%", 11, fill="#8A6400", weight="700"))

    # End cap summary card.
    card_x = 820
    parts.append(f'<rect x="{card_x}" y="650" width="310" height="130" rx="22" fill="#FFF7EE" stroke="#F1E2C5"/>')
    parts.append(axis_label(card_x + 155, 682, "Current BLS age table", 13, fill="#8A6400", weight="700"))
    parts.append(axis_label(card_x + 155, 722, "36.9%", 34, fill="#244A71", weight="700"))
    parts.append(axis_label(card_x + 155, 748, "16-19 labor force participation in 2024", 12, fill="#101828"))
    parts.append(axis_label(card_x + 155, 772, "A separate BLS monthly series shows 37.4% in Mar. 2026.", 11, fill="#667085"))

    parts.append(axis_label(110, 788, "Source: BLS Monthly Labor Review article on teen labor force participation; current 2024 age table and CPS monthly data from BLS.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "School-year work faded fast", "Teen labor force participation fell from the late-1970s peak into the mid-2010s and remains far below its old baseline.", "\n  ".join(parts))


def draw_july_chart() -> str:
    width, height = 1220, 920
    chart_left, chart_right = 110, 1120
    chart_top, chart_bottom = 170, 640
    years = [y for y, *_ in JULY_YOUTH]
    y_min, y_max = 50, 85

    men = [(y, m) for y, _, m, _ in JULY_YOUTH]
    women = [(y, w) for y, _, _, w in JULY_YOUTH]
    total = [(y, t) for y, t, _, _ in JULY_YOUTH]

    parts = []
    parts.append(axis_label(110, 132, "Summer youth labor force participation", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(110, 154, "The summer-job season still exists, but the 1980s peak has not come back.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(110, 178, "July rates for 16- to 24-year-olds, with men and women separated.", 13, anchor="start", fill="#667085"))

    for i in range(8):
        y = chart_top + i * (chart_bottom - chart_top) / 7
        val = y_max - i * (y_max - y_min) / 7
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 16, y + 4, f"{val:.0f}%", 11, anchor="end", fill="#667085"))

    for year in range(1990, 2025, 5):
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    for series, color, width_line, label in [
        (total, "#1F2937", 5, "Total"),
        (men, "#244A71", 3, "Men"),
        (women, "#C65A6A", 3, "Women"),
    ]:
        pts = line_points(series, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        dash = ' stroke-dasharray="6 4"' if label != "Total" else ""
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="{width_line}"{dash}/>')
        for x, y in pts[::4]:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}"/>')

    # Annotation cards.
    cards = [
        (110, 690, "1989 peak", "77.5%", "The summer-job market was much bigger."),
        (440, 690, "2024", "60.4%", "Youth labor force participation is still far below the peak."),
        (770, 690, "Men / women", "61.2 / 59.6", "The gender gap is now narrow."),
    ]
    for x, y, title, big, sub in cards:
        parts.append(f'<rect x="{x}" y="{y}" width="280" height="170" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
        parts.append(axis_label(x + 140, y + 34, title, 13, fill="#667085", weight="700"))
        parts.append(axis_label(x + 140, y + 78, big, 34, fill="#244A71", weight="700"))
        parts.append(axis_label(x + 140, y + 112, sub, 12, fill="#101828"))

    parts.append(axis_label(110, 888, "Source: BLS The Economics Daily, July 2024 youth labor force participation; chart data for July 1989-2024, Current Population Survey.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "The summer job shrank, but did not disappear", "The summer youth labor force remains important, though much smaller than the late-1980s peak.", "\n  ".join(parts))


def draw_age_gradient_chart() -> str:
    width, height = 1220, 860
    chart_left, chart_right = 180, 1070
    chart_top, chart_bottom = 195, 655
    years = [2004, 2014, 2024, 2034]
    groups = ["16-19", "16-24", "20-24", "25-54", "55+"]
    colors = {2004: "#6B7280", 2014: "#C8971D", 2024: "#244A71", 2034: "#9A4F5E"}
    y_min, y_max = 30, 90

    parts = []
    parts.append(axis_label(110, 132, "Current and projected participation by age", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(110, 154, "The drop is concentrated in teens, while prime-age participation stays high.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(110, 178, "BLS Employment Projections table 3.3; comparison years 2004, 2014, 2024, and 2034.", 13, anchor="start", fill="#667085"))

    for i in range(7):
        y = chart_top + i * (chart_bottom - chart_top) / 6
        val = y_max - i * (y_max - y_min) / 6
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 16, y + 4, f"{val:.0f}%", 11, anchor="end", fill="#667085"))

    row_step = (chart_bottom - chart_top) / (len(groups) - 1)
    for idx, group in enumerate(groups):
        y = chart_top + idx * row_step
        parts.append(axis_label(78, y + 4, group, 12, anchor="start", fill="#101828", weight="600"))
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#F2F4F7" stroke-width="1"/>')
        prev = None
        for year in years:
            value = AGE_GRADIENT[year][group]
            x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
            yv = chart_bottom - (value - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
            if prev:
                parts.append(f'<line x1="{prev[0]:.1f}" y1="{prev[1]:.1f}" x2="{x:.1f}" y2="{yv:.1f}" stroke="#CBD5E1" stroke-width="2"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{yv:.1f}" r="6.5" fill="{colors[year]}" stroke="#fff" stroke-width="2"/>')
            prev = (x, yv)

    legend_y = 705
    for idx, year in enumerate(years):
        x = 180 + idx * 195
        parts.append(f'<rect x="{x}" y="{legend_y}" width="14" height="14" rx="4" fill="{colors[year]}"/>')
        parts.append(axis_label(x + 22, legend_y + 12, str(year), 12, anchor="start", fill="#101828", weight="600"))

        parts.append(axis_label(110, 770, "Source: BLS Employment Projections table 3.3. The teen rate is the stress point; the 25-54 series barely moves.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "The age gradient is the real story", "Young people are where labor-force participation changes most, not prime-age workers.", "\n  ".join(parts))


def draw_a8b_age_split_chart() -> str:
    history_path = Path(__file__).resolve().parents[1] / "bls/a8b-age-split-history.csv"
    history = []
    with history_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if any(row[k] == "-" for k in ["16-17", "18-19", "20-24", "25-54"]):
                continue
            history.append(
                {
                    "Index": idx,
                    "Month": row["Month"],
                    "Year": int(row["Month"].split("-")[0]),
                    "MonthNum": int(row["Month"].split("-")[1]),
                    "16-17": float(row["16-17"]),
                    "18-19": float(row["18-19"]),
                    "20-24": float(row["20-24"]),
                    "25-54": float(row["25-54"]),
                }
            )

    width, height = 1220, 1120
    left_margin, right_margin = 60, 60
    top_margin = 150
    panel_w = (width - left_margin - right_margin - 24) / 2
    panel_h = 320
    row_gap = 18
    col_gap = 24
    groups = ["16-17", "18-19", "20-24", "25-54"]
    colors = {
        "16-17": "#4E8098",
        "18-19": "#C65A6A",
        "20-24": "#244A71",
        "25-54": "#C8971D",
    }
    y_min, y_max = 20, 88

    def series(group: str):
        return [(row["Index"], row[group]) for row in history]

    parts = []
    parts.append(axis_label(110, 132, "A-8b teen age split", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(110, 154, "The teen transition is clearest once 16-17 and 18-19 are separated.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(110, 178, "BLS A-8b seasonally adjusted participation rates, 2014 to current.", 13, anchor="start", fill="#667085"))

    for idx, group in enumerate(groups):
        row = idx // 2
        col = idx % 2
        x = left_margin + col * (panel_w + col_gap)
        y = top_margin + row * (panel_h + row_gap)
        inner_left = x + 18
        inner_right = x + panel_w - 18
        inner_top = y + 42
        inner_bottom = y + 232
        values = series(group)
        plotted = line_points(values, inner_left, inner_right, inner_top, inner_bottom, 0, len(history) - 1, y_min, y_max)
        start_val = history[0][group]
        end_val = history[-1][group]
        bg = "#FFF7F8" if group == "18-19" else "#FFFFFF"

        parts.append(f'<rect x="{x}" y="{y}" width="{panel_w:.1f}" height="{panel_h}" rx="24" fill="{bg}" stroke="#E5E7EB"/>')
        parts.append(axis_label(x + 18, y + 28, group, 19, anchor="start", fill="#101828", weight="700"))
        parts.append(axis_label(x + panel_w - 18, y + 28, f"{start_val:.1f}% → {end_val:.1f}%", 12, anchor="end", fill=colors[group], weight="700"))
        parts.append(axis_label(x + 18, y + 54, "seasonally adjusted LFPR", 11, anchor="start", fill="#667085"))

        for tick in [20, 40, 60, 80]:
            ty = inner_bottom - (tick - y_min) / (y_max - y_min) * (inner_bottom - inner_top)
            parts.append(f'<line x1="{inner_left}" y1="{ty:.1f}" x2="{inner_right}" y2="{ty:.1f}" stroke="#EEF2F7" stroke-width="1"/>')
            parts.append(axis_label(inner_left - 8, ty + 4, f"{tick}%", 10, anchor="end", fill="#667085"))

        tick_years = [2014, 2016, 2018, 2020, 2022, 2024, 2026]
        tick_positions = {}
        for year in tick_years:
            month_idx = next((row["Index"] for row in history if row["Year"] == year and row["MonthNum"] == 1), None)
            if month_idx is None:
                month_idx = next((row["Index"] for row in history if row["Year"] == year), None)
            if month_idx is not None:
                tick_positions[year] = month_idx
        for year, idx2 in tick_positions.items():
            tx = inner_left + idx2 / (len(history) - 1) * (inner_right - inner_left)
            parts.append(f'<line x1="{tx:.1f}" y1="{inner_top}" x2="{tx:.1f}" y2="{inner_bottom}" stroke="#F8FAFC" stroke-width="1"/>')
            parts.append(axis_label(tx, inner_bottom + 22, year, 10, fill="#667085"))

        poly = " ".join(f"{xv:.1f},{yv:.1f}" for xv, yv in plotted)
        width_line = 4 if group == "18-19" else 3
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{colors[group]}" stroke-width="{width_line}" stroke-linecap="round" stroke-linejoin="round"/>')

    parts.append(axis_label(110, 1042, "Source: BLS A-8b table, seasonally adjusted participation rates by age and sex.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "Teen age split, BLS A-8b", "Four age bands, 2014 to current. The gap is most readable once 16-17 and 18-19 are separated.", "\n  ".join(parts))


def build_html() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>The Summer Job Shrunk</title>
  <meta name="description" content="A journalist-grade BLS data piece on teen labor force participation, summer youth work, and current age-specific participation rates." />
    <style>
    :root {{
      --bg: #09111f;
      --bg2: #101a2e;
      --panel: #f7f2e8;
      --ink: #0f172a;
      --muted: #5b667a;
      --accent: #c65a6a;
      --blue: #244a71;
      --gold: #c8971d;
      --shadow: 0 28px 80px rgba(0,0,0,.30);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 18% 12%, rgba(198,90,106,.18), transparent 0 23%),
        radial-gradient(circle at 82% 8%, rgba(79,129,153,.16), transparent 0 20%),
        radial-gradient(circle at 50% 0%, rgba(200,151,29,.12), transparent 0 18%),
        linear-gradient(180deg, var(--bg) 0%, #0b1322 38%, var(--bg2) 100%);
      color: #fff;
      font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", Arial, sans-serif;
    }}
    .wrap {{ max-width: 1320px; margin: 0 auto; padding: 40px 24px 72px; }}
    .hero {{ display: grid; grid-template-columns: 1.45fr .95fr; gap: 28px; align-items: end; padding: 12px 0 26px; }}
    .kicker {{ text-transform: uppercase; letter-spacing: .22em; color: rgba(255,255,255,.68); font-size: 11px; margin-bottom: 14px; }}
    h1 {{ margin: 0; max-width: 10ch; font-family: Georgia, "Times New Roman", serif; font-size: clamp(54px, 7vw, 84px); line-height: .92; letter-spacing: -.055em; }}
    .deck {{ margin-top: 18px; max-width: 67ch; color: rgba(255,255,255,.84); font-size: 18px; line-height: 1.65; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 22px; color: rgba(255,255,255,.72); font-size: 13px; }}
    .meta span {{ padding: 8px 12px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); border-radius: 999px; backdrop-filter: blur(8px); }}
    .hero-card {{ border-radius: 28px; padding: 20px; background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.10); box-shadow: var(--shadow); backdrop-filter: blur(12px); }}
    .fact-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .fact {{ background: linear-gradient(180deg, rgba(255,255,255,.14), rgba(255,255,255,.06)); border: 1px solid rgba(255,255,255,.10); border-radius: 22px; padding: 16px 16px 18px; }}
    .fact .num {{ display: block; font-family: Georgia, "Times New Roman", serif; font-size: 28px; line-height: 1; margin-bottom: 8px; }}
    .fact .label {{ color: rgba(255,255,255,.78); font-size: 13px; line-height: 1.45; }}
    .section {{ margin-top: 18px; border-radius: 32px; overflow: hidden; box-shadow: var(--shadow); }}
    .panel {{ background: var(--panel); color: var(--ink); padding: 28px; }}
    .panel.soft {{ background: linear-gradient(180deg, #fff8ef, #f5efe3); }}
    .intro {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 26px; align-items: start; }}
    h2 {{ margin: 0 0 12px; font-size: clamp(26px, 3vw, 42px); line-height: 1; letter-spacing: -.04em; font-family: Georgia, "Times New Roman", serif; }}
    .copy {{ color: var(--muted); line-height: 1.7; font-size: 17px; }}
    .pullquote {{ margin: 0; padding: 22px 24px; border-left: 4px solid var(--accent); background: rgba(198,90,106,.08); border-radius: 20px; color: var(--ink); font-family: Georgia, "Times New Roman", serif; font-size: 26px; line-height: 1.28; letter-spacing: -.02em; }}
    .pullquote small {{ display: block; margin-top: 12px; color: var(--muted); font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", Arial, sans-serif; font-size: 13px; line-height: 1.5; }}
    .chart-card {{ background: #fff; border-top: 1px solid rgba(15, 23, 42, .08); }}
    .chart-head {{ padding: 22px 26px 0; }}
    .chart-head h3 {{ margin: 0; font-size: 24px; letter-spacing: -.03em; font-family: Georgia, "Times New Roman", serif; }}
    .chart-head p {{ margin: 8px 0 0; color: var(--muted); line-height: 1.6; max-width: 82ch; }}
    .chart {{ padding: 18px 18px 8px; background: linear-gradient(180deg, #fff, #faf7f1); }}
    .chart img {{ display: block; width: 100%; height: auto; border-radius: 18px; box-shadow: 0 12px 40px rgba(15, 23, 42, .08); }}
    .triptych {{ display: grid; grid-template-columns: 1fr; gap: 18px; }}
    .card-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .card {{ border-radius: 26px; overflow: hidden; background: #fff; box-shadow: 0 14px 40px rgba(15, 23, 42, .10); border: 1px solid rgba(15, 23, 42, .08); }}
    .card.feature {{ grid-column: 1 / -1; }}
    .card .top {{ padding: 18px 18px 0; }}
    .card .top h3 {{ margin: 0; font-size: 18px; font-family: Georgia, "Times New Roman", serif; letter-spacing: -.02em; }}
    .card .top p {{ margin: 8px 0 0; color: var(--muted); font-size: 14px; line-height: 1.55; }}
    .card img {{ display: block; width: 100%; height: auto; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: .18em; font-size: 11px; font-weight: 700; color: #6b7280; margin-bottom: 10px; }}
    .notes {{ display: grid; grid-template-columns: 1.05fr .95fr; gap: 18px; margin-top: 18px; }}
    .listbox {{ background: rgba(255,255,255,.78); border: 1px solid rgba(15, 23, 42, .08); border-radius: 24px; padding: 20px 22px; }}
    .listbox h4 {{ margin: 0 0 10px; font-size: 18px; font-family: Georgia, "Times New Roman", serif; }}
    .listbox ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.65; }}
    .listbox li + li {{ margin-top: 8px; }}
    .footer {{ margin-top: 20px; color: rgba(255,255,255,.74); line-height: 1.65; font-size: 13px; }}
    .source {{ margin-top: 6px; color: rgba(255,255,255,.60); font-size: 12px; }}
    @media (max-width: 1080px) {{ .hero, .intro, .notes, .card-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div>
        <div class="kicker">BLS / Current Population Survey / Employment Projections</div>
        <h1>The summer job shrunk</h1>
        <p class="deck">
          The central fact is simple: teen and youth participation in work fell hard after the 1970s and 1980s.
          The summer labor market is still there, but it is no longer the giant rite of passage it once was.
        </p>
        <div class="meta">
          <span>Annual teen LFPR peak: 57.9% in 1979</span>
          <span>July youth LFPR peak: 77.5% in 1989</span>
          <span>July 2024 youth LFPR: 60.4%</span>
          <span>Mar. 2026 teen LFPR: 37.4%</span>
        </div>
      </div>
      <div class="hero-card">
        <div class="fact-grid">
          <div class="fact"><span class="num">57.9%</span><div class="label">Teen annual labor force participation peak in 1979</div></div>
          <div class="fact"><span class="num">55.9%</span><div class="label">Teen annual labor force participation in 1989</div></div>
          <div class="fact"><span class="num">60.4%</span><div class="label">Youth labor force participation in July 2024</div></div>
          <div class="fact"><span class="num">37.4%</span><div class="label">16-19 participation in Mar. 2026, seasonally adjusted</div></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="panel soft">
        <div class="intro">
          <div>
            <div class="eyebrow">What the data says</div>
            <h2>A summer job used to be a norm. Now it reads like an exception.</h2>
            <div class="copy">
              BLS shows a long decline in teen labor force participation, a sharp gap between the late-1970s peak
              and current levels, and a flatter age gradient in which prime-age participation stays high while teen
              participation does not. That makes the labor market one of the cleanest ways to show delayed entry into
              adult life without overreaching.
            </div>
          </div>
          <blockquote class="pullquote">
            “Teen labor force participation has been on a long-term downward trend.”
            <small>That BLS framing is useful because it is plain, measurable, and conservative.</small>
          </blockquote>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-head">
          <h3>Lead visual: school-year teen labor force participation</h3>
          <p>This line shows the long decline from the postwar baseline to the mid-2010s. The highlighted points are the ones a journalist can quote without hedging.</p>
        </div>
        <div class="chart">
          <img src="bls-teens-annual-line.svg" alt="Annual teen labor force participation line chart" />
        </div>
      </div>
    </section>

    <section class="section">
      <div class="panel">
        <div class="card-grid">
          <div class="card">
            <div class="top">
              <h3>Summer youth labor force</h3>
              <p>July rates for 16- to 24-year-olds, with men and women separated.</p>
            </div>
            <img src="bls-summer-july-line.svg" alt="July youth labor force participation chart" />
          </div>
          <div class="card">
            <div class="top">
              <h3>Age gradient today</h3>
              <p>The 16-19 series is the stress point; 25-54 is almost flat by comparison.</p>
            </div>
            <img src="bls-age-gradient.svg" alt="Age gradient participation chart" />
          </div>
          <div class="card feature">
            <div class="top">
              <h3>Teen age split, A-8b</h3>
              <p>This is the tighter bridge chart: it separates 16-17, 18-19, 20-24, and 25-54 across a longer historical run so the teen transition is easier to see.</p>
            </div>
            <img src="bls-a8b-age-split.svg" alt="BLS A-8b teen age split chart" />
          </div>
          <div class="card feature">
            <div class="top">
              <h3>What to quote</h3>
              <p>Use these lines directly in the story pitch or in the eventual article.</p>
            </div>
            <div style="padding:18px;">
              <div style="border-radius:22px;background:linear-gradient(180deg,#0f172a,#1f3552);color:#fff;padding:24px 22px;min-height:100%;box-shadow:inset 0 1px 0 rgba(255,255,255,.08);">
                <div style="font-family:Georgia,'Times New Roman',serif;font-size:50px;line-height:.92;letter-spacing:-.06em;margin-bottom:10px;">-21.0</div>
                <div style="font-size:16px;line-height:1.55;color:rgba(255,255,255,.84);">The drop from 57.9% in 1979 to 36.9% in 2024 is the cleanest summary of the teen-work story.</div>
                <div style="margin-top:16px;font-size:13px;line-height:1.6;color:rgba(255,255,255,.68);">Separate measures, same direction: teen work became much less common.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="notes">
          <div class="listbox">
            <h4>Three lines a reporter can quote</h4>
            <ul>
              <li>Teen labor force participation peaked at 57.9 percent in 1979 and was 34.3 percent in 2015.</li>
              <li>July youth participation was 77.5 percent in 1989 and 60.4 percent in July 2024.</li>
              <li>In March 2026, the seasonally adjusted labor force participation rate for 16- to 19-year-olds was 37.4 percent.</li>
              <li>A-8b shows 16-17 at 24.9 percent and 18-19 at 48.4 percent in March 2026.</li>
            </ul>
          </div>
          <div class="listbox">
            <h4>How to frame the story</h4>
            <ul>
              <li>Strongest claim: the summer-job culture shrank substantially after the late 1970s and 1980s.</li>
              <li>Best caution: annual averages and monthly July rates are not the same measure, so label them clearly.</li>
              <li>Best use: pair teen labor participation with school enrollment and household formation later, not now.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="panel soft">
        <div class="eyebrow" style="color:#5d6470;">Methodology</div>
        <div class="copy" style="max-width: 90ch;">
          All figures are from the U.S. Bureau of Labor Statistics. The teen annual series comes from the Monthly Labor Review article on teen labor force participation. The July summer series comes from The Economics Daily youth participation article. The current teen rate comes from the CPS A-8b table. The age-gradient chart uses BLS Employment Projections table 3.3.
        </div>
        <div class="source">
          Sources: https://www.bls.gov/opub/mlr/2017/article/teen-labor-force-participation-before-and-after-the-great-recession.htm
          | https://www.bls.gov/opub/ted/2024/youth-labor-force-participation-rate-at-60-4-percent-in-july-2024.htm
          | https://www.bls.gov/web/empsit/cpseea08b.htm
          | https://www.bls.gov/emp/tables/civilian-labor-force-participation-rate.htm
        </div>
      </div>
    </section>

    <div class="footer">
      This is a standalone BLS package. It is intentionally separate from the licensed-driver story, so we can review each thread before we bridge them.
    </div>
  </div>
</body>
</html>
"""


def write_quote_pack(outdir: Path):
    text = """# BLS quote pack

## Headline options

- The summer job shrunk
- Why teen work stopped being a rite of passage
- The labor market got older

## Deck options

- BLS data shows teen labor force participation falling from the late-1970s peak into a much lower modern baseline.
- The summer-job season still exists, but it no longer looks like the default path into adulthood.

## Quote-ready lines

- Teen labor force participation peaked at 57.9 percent in 1979.
- July youth labor force participation peaked at 77.5 percent in July 1989 and was 60.4 percent in July 2024.
- In March 2026, the seasonally adjusted labor force participation rate for 16- to 19-year-olds was 37.4 percent.
- In BLS A-8b, 16-17-year-olds were at 24.9 percent and 18-19-year-olds were at 48.4 percent in March 2026.
- The 16- to 19-year-old participation rate was 43.9 percent in 2004, 34.0 percent in 2014, and 36.9 percent in 2024 in BLS projections tables.

## Safe framing

- Strong claim: teen work and summer youth work both moved down sharply from the 1970s and 1980s.
- Safer claim: the data shows delayed entry into the labor market, not a single cause.
- Avoid overclaiming: annual averages and monthly July rates are different measures and should be labeled separately.
"""
    (outdir / "bls-quote-pack.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate BLS youth labor editorial assets.")
    parser.add_argument("--outdir", type=Path, default=Path("bls_out"), help="Output directory.")
    args = parser.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "bls-teens-annual-line.svg").write_text(draw_annual_chart(), encoding="utf-8")
    (outdir / "bls-summer-july-line.svg").write_text(draw_july_chart(), encoding="utf-8")
    (outdir / "bls-age-gradient.svg").write_text(draw_age_gradient_chart(), encoding="utf-8")
    (outdir / "bls-a8b-age-split.svg").write_text(draw_a8b_age_split_chart(), encoding="utf-8")
    (outdir / "bls-editorial.html").write_text(build_html(), encoding="utf-8")
    write_quote_pack(outdir)

    print(f"Wrote BLS youth labor package to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
