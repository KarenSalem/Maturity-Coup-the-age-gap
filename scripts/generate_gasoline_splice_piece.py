#!/usr/bin/env python3
"""Generate a standalone spliced gasoline price chart.

The source is the repo-local gasoline context CSV, which already contains the
1963-2024 splice used in the React package. The result is a single, standalone
SVG focused on the gasoline history only.
"""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path


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
    <rect x="22" y="22" width="{width - 44}" height="{height - 44}" rx="24" fill="white" opacity="0.88"/>
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


def load_rows(path: Path):
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = int(row["Year"])
            value = row["LeadedRegularGasoline"].strip()
            if not value:
                continue
            rows.append((year, float(value)))
    return rows


def draw_chart(rows) -> str:
    width, height = 1240, 820
    chart_left, chart_right = 112, 1130
    chart_top, chart_bottom = 174, 624
    years = [year for year, _ in rows]
    y_min, y_max = 0.0, 4.5
    plotted = line_points(rows, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in plotted)

    x78 = chart_left + (1978 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
    x80 = chart_left + (1980 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
    last_year, last_val = rows[-1]

    parts = []
    parts.append(axis_label(72, 136, "Standalone gasoline splice", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(72, 158, "Leaded regular gasoline through 1990, then regular gasoline after the switch.", 22, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(72, 182, "This is the 1963-2024 series extracted from the gasoline context file the React chart now uses.", 13, anchor="start", fill="#667085"))

    parts.append(f'<rect x="72" y="202" width="1094" height="392" rx="26" fill="#FFFFFF" stroke="#E8E0D2"/>')
    parts.append(f'<rect x="{x78:.1f}" y="{chart_top}" width="{x80 - x78:.1f}" height="{chart_bottom - chart_top}" fill="#C8971D" opacity="0.10"/>')

    for tick in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]:
        y = chart_bottom - (tick - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 14, y + 4, f"${tick:.1f}", 11, anchor="end", fill="#667085"))

    for year in [1963, 1965, 1970, 1975, 1978, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
        if year < years[0] or year > years[-1]:
            continue
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    parts.append(f'<polygon points="{chart_left:.1f},{chart_bottom:.1f} {polyline} {chart_right:.1f},{chart_bottom:.1f}" fill="#244A71" opacity="0.08"/>')
    parts.append(f'<polyline points="{polyline}" fill="none" stroke="#244A71" stroke-width="4.5"/>')

    for year in [1963, 1978, 1980, 2024]:
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        value = dict(rows)[year]
        y = chart_bottom - (value - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        color = "#C8971D" if year in {1978, 1980} else "#244A71"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>')

    parts.append(f'<rect x="864" y="226" width="250" height="132" rx="20" fill="#FFFDF4" stroke="#E9D8A6"/>')
    parts.append(axis_label(884, 260, "Fuel shock window", 13, anchor="start", fill="#667085", weight="700"))
    parts.append(axis_label(884, 292, "1978 to 1980: $0.627 -> $1.191", 22, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(884, 324, "A nearly 90% jump in two years.", 16, anchor="start", fill="#C65A6A", weight="700"))
    parts.append(axis_label(884, 348, f"2024 annual average: ${last_val:.3f}", 12, anchor="start", fill="#667085"))

    parts.append(axis_label(112, 668, "Source: EIA Table 9.4 annual averages, spliced from leaded regular gasoline to regular gasoline after 1990.", 11, anchor="start", fill="#667085"))
    parts.append(axis_label(112, 688, "The file is a bridge chart on its own, not just a hidden helper for the composite page.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "Gasoline price history, 1963-2024", "A standalone version of the spliced fuel series used in the main chart.", "\n  ".join(parts))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a standalone spliced gasoline chart.")
    parser.add_argument("--out", type=Path, default=Path("licensed-drivers/licensed-drivers-gasoline-splice.svg"))
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("licensed-drivers/licensed-drivers-gasoline-teen-context.csv"),
    )
    args = parser.parse_args()

    rows = load_rows(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(draw_chart(rows), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
