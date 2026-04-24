#!/usr/bin/env python3
"""Generate a bridge chart linking the 1978-1980 gasoline shock to teen licensure.

The top panel uses EIA Table 9.4 annual leaded regular gasoline prices.
The bottom panel uses the existing teen work overlay plus a computed 18-year-old
licensed-driver share from the FHWA DL-220 source already in the repo.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen

GAS_URL = "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T09.04"


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


def load_gasoline_history() -> list[tuple[int, float]]:
    with urlopen(GAS_URL) as response:
        raw = response.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw.replace("\r", "")))
    annual: dict[int, float] = {}
    for row in reader:
        if row["MSN"] != "RLUCUUS":
            continue
        if not row["YYYYMM"].endswith("13"):
            continue
        value = row["Value"].strip()
        if value in {"Not Available", "Not Applicable", "--", ""}:
            continue
        year = int(row["YYYYMM"][:4])
        annual[year] = float(value)
    return sorted(annual.items())


def load_teen_history(path: Path):
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "Year": int(row["Year"]),
                    "YouthJulLFPR": float(row["YouthJulLFPR"]),
                    "YouthJulLFPR_Index1963": float(row["YouthJulLFPR_Index1963"]),
                }
            )
    return rows


def load_licensed_18_share(path: Path):
    by_year = defaultdict(int)
    total_by_year = defaultdict(int)
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            drivers = row["Drivers"].strip()
            if not drivers:
                continue
            year = int(row["Year"])
            cohort = row["Cohort"]
            count = int(drivers.replace(",", ""))
            by_year[(year, cohort)] += count
            total_by_year[year] += count

    series = []
    for year in sorted(total_by_year):
        share = by_year[(year, "18")] / total_by_year[year] * 100
        series.append((year, share))
    return series


def indexed_series(series, base_year: int):
    base = None
    for year, value in series:
        if year == base_year:
            base = value
            break
    if base is None:
        raise ValueError(f"Missing base year {base_year}")
    return [(year, value / base * 100) for year, value in series]


def draw_top_panel(gas_series):
    width = 1200
    chart_left, chart_right = 110, 1110
    chart_top, chart_bottom = 176, 528
    years = [year for year, _ in gas_series if year >= 1963]
    plot_series = [(year, value) for year, value in gas_series if year >= 1963]
    y_min, y_max = 0.0, 4.0
    line = line_points(plot_series, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in line)

    x78 = chart_left + (1978 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
    x80 = chart_left + (1980 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
    callout_x, callout_y = 812, 214

    parts = []
    parts.append(axis_label(70, 136, "Table 9.4 gasoline shock window", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(70, 158, "Leaded regular gasoline jumped almost 90% from 1978 to 1980.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(70, 182, "The chart starts in 1963 so it can be read against the teen-licensing panel below.", 13, anchor="start", fill="#667085"))

    parts.append(f'<rect x="70" y="198" width="1080" height="360" rx="26" fill="#FFFFFF" stroke="#E8E0D2"/>')
    parts.append(f'<rect x="{x78:.1f}" y="{chart_top}" width="{x80 - x78:.1f}" height="{chart_bottom - chart_top}" fill="#C8971D" opacity="0.10"/>')

    for tick in [0, 1, 2, 3, 4]:
        y = chart_bottom - (tick - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 14, y + 4, f"${tick:.0f}.0", 11, anchor="end", fill="#667085"))

    for year in [1949, 1955, 1960, 1965, 1970, 1975, 1978, 1979, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]:
        if year < years[0] or year > years[-1]:
            continue
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in line)
    parts.append(f'<polyline points="{polyline}" fill="none" stroke="#244A71" stroke-width="4.5"/>')
    parts.append(f'<polygon points="{chart_left:.1f},{chart_bottom:.1f} {polyline} {chart_right:.1f},{chart_bottom:.1f}" fill="#244A71" opacity="0.08"/>')

    for year in [1978, 1980, years[-1]]:
        x, y = line[years.index(year) if year in years else -1]
        color = "#C8971D" if year in {1978, 1980} else "#244A71"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>')

    gas_map = dict(gas_series)
    first_1978 = gas_map.get(1978)
    first_1980 = gas_map.get(1980)
    last_year, last_val = plot_series[-1]
    pct_change = (first_1980 / first_1978 - 1) * 100 if first_1978 and first_1980 else None

    parts.append(f'<rect x="{callout_x}" y="{callout_y}" width="280" height="132" rx="20" fill="#FFFDF4" stroke="#E9D8A6"/>')
    parts.append(axis_label(callout_x + 20, callout_y + 34, "1978 to 1980", 13, anchor="start", fill="#667085", weight="700"))
    parts.append(axis_label(callout_x + 20, callout_y + 64, f"${first_1978:.3f} -> ${first_1980:.3f}", 24, anchor="start", fill="#101828", weight="700"))
    if pct_change is not None:
        parts.append(axis_label(callout_x + 20, callout_y + 96, f"+{pct_change:.1f}% in two years", 18, anchor="start", fill="#C65A6A", weight="700"))
    parts.append(axis_label(callout_x + 20, callout_y + 118, f"{last_year} annual average: ${last_val:.3f}", 12, anchor="start", fill="#667085"))

    parts.append(axis_label(1110, line[-1][1] - 8, f"${last_val:.2f}", 12, anchor="end", fill="#244A71", weight="700"))
    parts.append(axis_label(110, 572, "Source: EIA Monthly Energy Review Table 9.4, leaded regular gasoline annual averages from 1963 to 1990.", 11, anchor="start", fill="#667085"))
    parts.append(axis_label(110, 590, f"The panel starts in 1963 to line up with teen licensure; the 1978-1980 jump is still the timing marker for the licensing story.", 11, anchor="start", fill="#667085"))
    return "\n  ".join(parts)


def draw_bottom_panel(teen_rows, lic18_series):
    width = 1200
    chart_left, chart_right = 110, 1110
    chart_top, chart_bottom = 176, 528
    years = [row["Year"] for row in teen_rows]
    youth = [(row["Year"], row["YouthJulLFPR_Index1963"]) for row in teen_rows]
    lic18_index = indexed_series(lic18_series, 1963)

    y_min, y_max = 60.0, 125.0
    youth_pts = line_points(youth, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    lic_pts = line_points(lic18_index, chart_left, chart_right, chart_top, chart_bottom, years[0], years[-1], y_min, y_max)
    youth_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in youth_pts)
    lic_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in lic_pts)

    x78 = chart_left + (1978 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
    x80 = chart_left + (1980 - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)

    lic_by_year = dict(lic18_series)
    lic_1978 = lic_by_year[1978]
    lic_1980 = lic_by_year[1980]
    youth_by_year = dict((row["Year"], row["YouthJulLFPR"]) for row in teen_rows)
    youth_1978 = youth_by_year[1978]
    youth_1980 = youth_by_year[1980]

    parts = []
    parts.append(axis_label(70, 136, "Summer work and 18-year-old licensure", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(70, 158, "The summer-job line stays high while 18-year-old licensure turns down after the gasoline shock.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(70, 182, "Youth work uses the existing BLS July youth LFPR series; licensure uses the FHWA DL-220 counts converted into an 18-year-old share.", 13, anchor="start", fill="#667085"))

    parts.append(f'<rect x="70" y="198" width="1080" height="360" rx="26" fill="#FFFFFF" stroke="#E8E0D2"/>')
    parts.append(f'<rect x="110" y="218" width="280" height="54" rx="16" fill="#F8FAFC" stroke="#E5E7EB"/>')
    parts.append(f'<circle cx="132" cy="235" r="6" fill="#244A71"/>')
    parts.append(axis_label(150, 239, "Blue line: July youth LFPR, ages 16-24", 12, anchor="start", fill="#101828", weight="700"))
    parts.append(f'<circle cx="132" cy="255" r="6" fill="#C65A6A"/>')
    parts.append(axis_label(150, 259, "Red line: 18-year-old share of licensed drivers", 12, anchor="start", fill="#101828", weight="700"))
    parts.append(f'<rect x="{x78:.1f}" y="{chart_top}" width="{x80 - x78:.1f}" height="{chart_bottom - chart_top}" fill="#C65A6A" opacity="0.08"/>')

    for tick in [60, 70, 80, 90, 100, 110, 120]:
        y = chart_bottom - (tick - y_min) / (y_max - y_min) * (chart_bottom - chart_top)
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 14, y + 4, f"{tick}", 11, anchor="end", fill="#667085"))

    for year in [1963, 1965, 1970, 1975, 1978, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
        if year < years[0] or year > years[-1]:
            continue
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    parts.append(f'<polygon points="{chart_left:.1f},{chart_bottom:.1f} {lic_poly} {chart_right:.1f},{chart_bottom:.1f}" fill="#C65A6A" opacity="0.08"/>')
    parts.append(f'<polyline points="{youth_poly}" fill="none" stroke="#244A71" stroke-width="4"/>')
    parts.append(f'<polyline points="{lic_poly}" fill="none" stroke="#C65A6A" stroke-width="4.5"/>')

    for year in [1963, 1978, 1980, years[-1]]:
        color = "#244A71" if year != 1980 else "#C8971D"
        ypts = youth_pts if year != years[-1] else youth_pts
        if year in years:
            x, y = youth_pts[years.index(year)]
            if year == 1980:
                color = "#C8971D"
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>')
        if year in lic_by_year:
            x, y = lic_pts[years.index(year)]
            color = "#C65A6A" if year != 1980 else "#C8971D"
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>')

    callout_x, callout_y = 814, 214
    parts.append(f'<rect x="{callout_x}" y="{callout_y}" width="286" height="132" rx="20" fill="#FFF7F8" stroke="#E9D8A6"/>')
    parts.append(axis_label(callout_x + 20, callout_y + 34, "1978 to 1980", 13, anchor="start", fill="#667085", weight="700"))
    parts.append(axis_label(callout_x + 20, callout_y + 62, f"18-year-old share: {lic_1978:.2f}% -> {lic_1980:.2f}%", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(callout_x + 20, callout_y + 90, f"July youth LFPR: {youth_1978:.1f}% -> {youth_1980:.1f}%", 18, anchor="start", fill="#244A71", weight="700"))
    parts.append(axis_label(callout_x + 20, callout_y + 116, "Licensure moves; summer work barely budges.", 12, anchor="start", fill="#667085"))

    parts.append(axis_label(110, 572, "Source: BLS youth labor series plus FHWA DL-220 driver counts; 18-year-old share is computed from the raw licensed-driver counts.", 11, anchor="start", fill="#667085"))
    parts.append(axis_label(110, 590, "This is the bridge to the existing summer-work / teen-licensing chart: the oil shock belongs in the same sentence as the first turn down in teen autonomy.", 11, anchor="start", fill="#667085"))
    return "\n  ".join(parts)


def build_csv(out_path: Path, gas_series, teen_rows, lic18_series):
    teen_by_year = {row["Year"]: row for row in teen_rows}
    lic_by_year = dict(lic18_series)
    gas_map = dict(gas_series)
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Year",
                "LeadedRegularGasoline",
                "GasolineIndex1978",
                "YouthJulLFPR",
                "YouthJulLFPR_Index1963",
                "Licensed18Share",
                "Licensed18Share_Index1963",
            ]
        )
        gas_base = gas_map[1978]
        lic_base = lic18_series[0][1]
        for year in sorted(teen_by_year):
            row = teen_by_year[year]
            lic_value = lic_by_year[year]
            gas_value = gas_map.get(year)
            writer.writerow(
                [
                    year,
                    f"{gas_value:.3f}" if gas_value is not None else "",
                    f"{gas_value / gas_base * 100:.1f}" if gas_value is not None else "",
                    f"{row['YouthJulLFPR']:.1f}",
                    f"{row['YouthJulLFPR_Index1963']:.1f}",
                    f"{lic_value:.2f}",
                    f"{lic_value / lic_base * 100:.1f}",
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a gasoline and teen-licensure bridge chart.")
    parser.add_argument("--outdir", type=Path, default=Path("licensed-drivers"), help="Output directory.")
    args = parser.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    gas_series = load_gasoline_history()
    teen_rows = load_teen_history(Path(__file__).resolve().parents[1] / "licensed-drivers/licensed-drivers-youth-work-overlay.csv")
    lic18_series = load_licensed_18_share(Path(__file__).resolve().parents[1] / "licensed-drivers/licensed-drivers.csv")

    svg = svg_wrap(
        1200,
        1280,
        "Gasoline shock and teen licensing",
        "EIA Table 9.4 gives the oil-crisis trigger; the teen-work and licensure series show what happened next.",
        draw_top_panel(gas_series) + '\n  <g transform="translate(0,620)">\n  ' + draw_bottom_panel(teen_rows, lic18_series) + '\n  </g>',
    )

    (outdir / "licensed-drivers-gasoline-teen-context.svg").write_text(svg, encoding="utf-8")
    build_csv(outdir / "licensed-drivers-gasoline-teen-context.csv", gas_series, teen_rows, lic18_series)
    print(f"Wrote bridge chart to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
