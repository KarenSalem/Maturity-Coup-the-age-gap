#!/usr/bin/env python3
"""Generate an editorial CPI package for motor vehicle insurance.

This uses the official BLS CPI-U series for all items and motor vehicle insurance,
with a small Insurance Information Institute context panel for the teen-driver
pricing angle.
"""

from __future__ import annotations

import argparse
import csv
import html
import math
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


def load_history(history_path: Path):
    rows = []
    with history_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = int(row["Year"])
            all_items = float(row["AllItems"])
            mv = float(row["MotorVehicleInsurance"])
            rows.append(
                {
                    "Year": year,
                    "AllItems": all_items,
                    "MotorVehicleInsurance": mv,
                    "AllItemsIndex": all_items / rows[0]["AllItems"] * 100 if rows else 100.0,
                    "MotorVehicleInsuranceIndex": mv / rows[0]["MotorVehicleInsurance"] * 100 if rows else 100.0,
                }
            )
    return rows


def draw_index_chart(rows) -> str:
    width, height = 1280, 980
    chart_left, chart_right = 120, 1140
    chart_top, chart_bottom = 180, 640
    years = [row["Year"] for row in rows]
    all_series = [(row["Year"], row["AllItemsIndex"]) for row in rows]
    mv_series = [(row["Year"], row["MotorVehicleInsuranceIndex"]) for row in rows]
    y_min = 100
    y_max = max(max(row["AllItemsIndex"], row["MotorVehicleInsuranceIndex"]) for row in rows) * 1.05
    log_min = math.log10(y_min)
    log_max = math.log10(y_max)

    def y_for(value: float) -> float:
        value = max(value, y_min)
        return chart_bottom - (math.log10(value) - log_min) / (log_max - log_min) * (chart_bottom - chart_top)

    def plot_points(series):
        points = []
        for year, value in series:
            x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
            points.append((x, y_for(value)))
        return points

    parts = []
    parts.append(axis_label(120, 132, "Motor vehicle insurance outpaced general inflation", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(120, 154, "Annual CPI-U averages indexed to 1960 = 100, using BLS all-items and motor vehicle insurance series.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(120, 178, "BLS CPI-U series CUUR0000SA0 vs CUUR0000SETE. The gap widens sharply after 2021.", 13, anchor="start", fill="#667085"))

    for val in [100, 200, 500, 1000, 2000, 3500]:
        if val > y_max:
            continue
        y = y_for(val)
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        parts.append(axis_label(chart_left - 18, y + 4, f"{val:.0f}", 11, anchor="end", fill="#667085"))

    for year in years:
        if year != years[0] and year != years[-1] and (year - years[0]) % 5 != 0:
            continue
        x = chart_left + (year - years[0]) / (years[-1] - years[0]) * (chart_right - chart_left)
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top}" x2="{x:.1f}" y2="{chart_bottom}" stroke="#F2F4F7" stroke-width="1"/>')
        parts.append(axis_label(x, chart_bottom + 24, str(year), 10, fill="#667085"))

    # Fill under the motor vehicle insurance line to make the gap read quickly.
    mv_plotted = plot_points(mv_series)
    all_plotted = plot_points(all_series)
    mv_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in mv_plotted)
    all_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in all_plotted)

    parts.append(f'<polygon points="{chart_left:.1f},{chart_bottom:.1f} {mv_poly} {chart_right:.1f},{chart_bottom:.1f}" fill="#C65A6A" opacity="0.10"/>')
    parts.append(f'<polyline points="{all_poly}" fill="none" stroke="#64748B" stroke-width="3.5" stroke-dasharray="8 5"/>')
    parts.append(f'<polyline points="{mv_poly}" fill="none" stroke="#C65A6A" stroke-width="5"/>')

    for series, color in [(all_plotted, "#64748B"), (mv_plotted, "#C65A6A")]:
        for x, y in [series[0], series[-1]]:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="#fff" stroke-width="2"/>')

    # Endpoint badges.
    end = rows[-1]
    all_change = (end["AllItemsIndex"] - 100)
    mv_change = (end["MotorVehicleInsuranceIndex"] - 100)
    parts.append(f'<rect x="120" y="702" width="310" height="190" rx="22" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(275, 736, "All items", 13, fill="#667085", weight="700"))
    parts.append(axis_label(275, 782, f"+{all_change:.1f}%", 36, fill="#64748B", weight="700"))
    parts.append(axis_label(275, 814, "Inflation since 1960", 12, fill="#101828"))
    parts.append(axis_label(275, 840, f"2025 index: {end['AllItemsIndex']:.1f}", 12, fill="#667085"))

    parts.append(f'<rect x="455" y="702" width="330" height="190" rx="22" fill="#FFF7F8" stroke="#E5E7EB"/>')
    parts.append(axis_label(620, 736, "Motor vehicle insurance", 13, fill="#C65A6A", weight="700"))
    parts.append(axis_label(620, 782, f"+{mv_change:.1f}%", 36, fill="#C65A6A", weight="700"))
    parts.append(axis_label(620, 814, "Insurance cost inflation since 1960", 12, fill="#101828"))
    parts.append(axis_label(620, 840, f"2025 index: {end['MotorVehicleInsuranceIndex']:.1f}", 12, fill="#667085"))

    parts.append(f'<rect x="825" y="702" width="335" height="190" rx="22" fill="#FFFFFF" stroke="#E5E7EB"/>')
    parts.append(axis_label(992, 736, "The spread", 13, fill="#667085", weight="700"))
    parts.append(axis_label(992, 782, f"{mv_change/all_change:.1f}x", 36, fill="#244A71", weight="700"))
    parts.append(axis_label(992, 814, "Insurance rose roughly this much faster", 12, fill="#101828"))
    parts.append(axis_label(992, 840, "Use this as the visual headline.", 12, fill="#667085"))

    parts.append(axis_label(120, 930, "Source: BLS CPI-U annual averages from the BLS-sourced yearly tables for CUUR0000SA0 and CUUR0000SETE.", 11, anchor="start", fill="#667085"))
    parts.append(axis_label(120, 952, "Indexed to 1960 = 100 to show the divergence cleanly.", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "Insurance costs pulled away from general inflation", "A clear CPI comparison for the story package.", "\n  ".join(parts))


def draw_growth_bars(rows) -> str:
    first = rows[0]
    last = rows[-1]
    all_growth = (last["AllItems"] / first["AllItems"] - 1) * 100
    mv_growth = (last["MotorVehicleInsurance"] / first["MotorVehicleInsurance"] - 1) * 100
    gap = mv_growth - all_growth

    width, height = 1040, 760
    chart_left, chart_right = 170, 940
    chart_top, chart_bottom = 190, 470
    max_val = max(mv_growth, all_growth)

    parts = []
    parts.append(axis_label(56, 132, "1960 to 2025 growth comparison", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(56, 154, "A simple graphic to make the inflation gap obvious at a glance.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(56, 178, "Motor vehicle insurance rose much faster than all items over the same period.", 13, anchor="start", fill="#667085"))

    labels = [("All items", all_growth, "#64748B"), ("Motor vehicle insurance", mv_growth, "#C65A6A")]
    row_step = (chart_bottom - chart_top) / 2
    for idx, (label, value, color) in enumerate(labels):
        y = chart_top + idx * row_step + 30
        parts.append(axis_label(66, y + 16, label, 14, anchor="start", fill="#101828", weight="700"))
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{chart_right-chart_left}" height="46" rx="14" fill="#F8FAFC"/>')
        bar_w = (value / max_val) * (chart_right - chart_left)
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{bar_w:.1f}" height="46" rx="14" fill="{color}"/>')
        parts.append(axis_label(chart_left + bar_w + 12, y + 29, f"+{value:.1f}%", 18, anchor="start", fill=color, weight="700"))

    parts.append(f'<rect x="150" y="540" width="740" height="130" rx="22" fill="#FFF7F8" stroke="#E5E7EB"/>')
    parts.append(axis_label(520, 576, "Big picture", 13, fill="#667085", weight="700"))
    parts.append(axis_label(520, 618, f"Motor vehicle insurance outpaced all-items inflation by {gap:.1f} percentage points.", 24, fill="#101828", weight="700"))
    parts.append(axis_label(520, 648, "That is the chart-friendly headline for the package.", 12, fill="#667085"))
    return svg_wrap(width, height, "The insurance premium shock", "A quick bar graphic for the cumulative increase.", "\n  ".join(parts))


def draw_annotation_panel() -> str:
    width, height = 1280, 760
    parts = []
    parts.append(axis_label(80, 130, "Teen pricing context from III", 13, anchor="start", fill="#667085"))
    parts.append(axis_label(80, 156, "Why the CPI line matters for households with young drivers", 24, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(80, 188, "III is not a BLS age series, but it is a useful bridge for explaining why this insurance cost shock hits teens harder.", 13, anchor="start", fill="#667085"))

    cards = [
        (80, 240, "Age is a rating factor", "Insurers generally charge more for teenagers and young adults under 25.", "#244A71"),
        (450, 240, "Teen surcharge", "Adding a teenager can raise a family premium by 50% to 100%.", "#C65A6A"),
        (820, 240, "Careful framing", "Use III for context, not as a substitute for a historical premium series.", "#C8971D"),
    ]
    for x, y, title, body, color in cards:
        parts.append(f'<rect x="{x}" y="{y}" width="330" height="170" rx="24" fill="#FFFFFF" stroke="#E5E7EB"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="330" height="10" rx="10" fill="{color}"/>')
        parts.append(axis_label(x + 24, y + 42, title, 14, anchor="start", fill="#667085", weight="700"))
        parts.append(axis_label(x + 24, y + 88, body, 24 if len(body) < 60 else 22, anchor="start", fill="#101828", weight="700"))

    parts.append(f'<rect x="80" y="450" width="1120" height="220" rx="28" fill="#FFFDF8" stroke="#F0E5D0"/>')
    parts.append(axis_label(120, 492, "How to say it in the story", 13, anchor="start", fill="#667085", weight="700"))
    parts.append(axis_label(120, 532, "BLS shows the market-wide insurance index.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(120, 564, "III explains why teens feel the increase more sharply: young drivers are priced as higher risk.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(120, 596, "That lets you pair the CPI trend with a teen-autonomy argument without pretending BLS publishes age-specific insurance inflation.", 18, anchor="start", fill="#101828", weight="700"))
    parts.append(axis_label(120, 636, "Sources: https://www.bls.gov/cpi/factsheets/motor-vehicle-insurance.htm | https://www.iii.org/issue-update/background-on-teen-drivers | https://www.iii.org/article/auto-insurance-teen-drivers | https://www.iii.org/article/what-determines-price-my-auto-insurance-policy", 11, anchor="start", fill="#667085"))
    return svg_wrap(width, height, "Teen pricing context", "A compact source-backed annotation panel for the CPI chart.", "\n  ".join(parts))


def write_html(outdir: Path, chart_svg: str, bars_svg: str, panel_svg: str):
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Motor Vehicle Insurance and Inflation</title>
  <style>
    :root {{
      --bg: #0A1220;
      --panel: #F7F3EB;
      --ink: #101828;
      --muted: #667085;
      --blue: #64748B;
      --red: #C65A6A;
      --gold: #C8971D;
      --shadow: 0 28px 80px rgba(0,0,0,.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 16% 12%, rgba(198,90,106,.16), transparent 24%),
        radial-gradient(circle at 84% 8%, rgba(100,116,139,.14), transparent 22%),
        linear-gradient(180deg, var(--bg) 0%, #0F172A 48%, #132238 100%);
      color: #fff;
      font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", Arial, sans-serif;
    }}
    .wrap {{ max-width: 1360px; margin: 0 auto; padding: 40px 24px 72px; }}
    .hero {{ display: grid; grid-template-columns: 1.35fr .95fr; gap: 28px; align-items: end; padding: 8px 0 26px; }}
    .kicker {{ text-transform: uppercase; letter-spacing: .22em; color: rgba(255,255,255,.66); font-size: 11px; margin-bottom: 14px; }}
    h1 {{ margin: 0; max-width: 11ch; font-family: Georgia, "Times New Roman", serif; font-size: clamp(54px, 7vw, 84px); line-height: .92; letter-spacing: -.055em; }}
    .deck {{ margin-top: 18px; max-width: 68ch; color: rgba(255,255,255,.84); font-size: 18px; line-height: 1.65; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 22px; color: rgba(255,255,255,.72); font-size: 13px; }}
    .meta span {{ padding: 8px 12px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); border-radius: 999px; backdrop-filter: blur(8px); }}
    .hero-card {{ border-radius: 28px; padding: 20px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.10); box-shadow: var(--shadow); backdrop-filter: blur(12px); }}
    .pill-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .pill {{ background: linear-gradient(180deg, rgba(255,255,255,.14), rgba(255,255,255,.06)); border: 1px solid rgba(255,255,255,.10); border-radius: 22px; padding: 16px 16px 18px; }}
    .pill .num {{ display: block; font-family: Georgia, "Times New Roman", serif; font-size: 30px; line-height: 1; margin-bottom: 8px; }}
    .pill .label {{ color: rgba(255,255,255,.78); font-size: 13px; line-height: 1.45; }}
    .section {{ margin-top: 18px; border-radius: 32px; overflow: hidden; box-shadow: var(--shadow); }}
    .panel {{ background: var(--panel); color: var(--ink); padding: 28px; }}
    .intro {{ display: grid; grid-template-columns: 1.05fr .95fr; gap: 22px; align-items: start; }}
    h2 {{ margin: 0 0 12px; font-size: clamp(26px, 3vw, 40px); line-height: 1; letter-spacing: -.04em; font-family: Georgia, "Times New Roman", serif; }}
    .copy {{ color: var(--muted); line-height: 1.7; font-size: 17px; }}
    .chart-card {{ background: #fff; border-top: 1px solid rgba(15, 23, 42, .08); }}
    .chart-head {{ padding: 22px 26px 0; }}
    .chart-head h3 {{ margin: 0; font-size: 24px; letter-spacing: -.03em; font-family: Georgia, "Times New Roman", serif; }}
    .chart-head p {{ margin: 8px 0 0; color: var(--muted); line-height: 1.6; max-width: 84ch; }}
    .chart {{ padding: 18px; background: linear-gradient(180deg, #fff, #faf7f1); }}
    .chart img {{ display: block; width: 100%; height: auto; border-radius: 18px; box-shadow: 0 12px 40px rgba(15, 23, 42, .08); }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    .card {{ border-radius: 26px; overflow: hidden; background: #fff; box-shadow: 0 14px 40px rgba(15, 23, 42, .10); border: 1px solid rgba(15, 23, 42, .08); }}
    .card.feature {{ grid-column: 1 / -1; }}
    .card .top {{ padding: 18px 18px 0; }}
    .card .top h3 {{ margin: 0; font-size: 18px; font-family: Georgia, "Times New Roman", serif; letter-spacing: -.02em; }}
    .card .top p {{ margin: 8px 0 0; color: var(--muted); font-size: 14px; line-height: 1.55; }}
    .card img {{ display: block; width: 100%; height: auto; }}
    .footer {{ margin-top: 20px; color: rgba(255,255,255,.74); line-height: 1.65; font-size: 13px; }}
    @media (max-width: 1080px) {{ .hero, .intro, .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div>
        <div class="kicker">BLS CPI / teen-risk context</div>
        <h1>Insurance costs pulled away</h1>
        <p class="deck">
          The broad CPI line is the market-wide story. The teen-driver context explains why young families feel
          the increase so much more acutely. Together, they give us a defensible way to talk about the cost
          of delaying independence without pretending the BLS publishes age-specific insurance inflation.
        </p>
        <div class="meta">
          <span>All items: +989.2% since 1960</span>
          <span>Motor vehicle insurance: +3375.5% since 1960</span>
          <span>Gap: 3.4x faster</span>
          <span>BLS series: `CUUR0000SA0` and `CUUR0000SETE`</span>
        </div>
      </div>
      <div class="hero-card">
        <div class="pill-grid">
          <div class="pill"><span class="num">3375.5%</span><div class="label">Motor vehicle insurance growth, 1960-2025</div></div>
          <div class="pill"><span class="num">989.2%</span><div class="label">All-items CPI growth, 1960-2025</div></div>
          <div class="pill"><span class="num">50-100%</span><div class="label">Typical premium hit when a teen is added, per III</div></div>
          <div class="pill"><span class="num">1</span><div class="label">BLS annual CPI comparison, not an age-specific price series</div></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="panel">
        <div class="intro">
          <div>
            <div class="eyebrow" style="text-transform:uppercase;letter-spacing:.18em;color:#6B7280;font-size:11px;font-weight:700;margin-bottom:10px;">What the data says</div>
            <h2>Insurance inflation is real, and it moved much faster than general inflation.</h2>
            <div class="copy">
              BLS gives us a clean, official CPI series for motor vehicle insurance. That series can be compared
              directly against all items to show how sharply the cost of coverage rose after 1960. III adds the
              missing household context: teenagers and drivers under 25 are still priced as high-risk, so the
              household burden lands hardest right when young people are trying to become autonomous.
            </div>
          </div>
          <div class="copy">
            Use the line chart for the long trend, the bar graphic for the headline spread, and the annotation panel
            when you need the teen-premium framing. That keeps the argument source-backed and easy to explain.
          </div>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-head">
          <h3>Main visual: insurance vs inflation</h3>
          <p>The dashed line is all-items CPI, indexed to 1960 = 100. The red line is motor vehicle insurance, indexed the same way, which makes the divergence obvious.</p>
        </div>
        <div class="chart">
          <img src="cpi-motor-vehicle-insurance-index.svg" alt="Motor vehicle insurance and all-items CPI indexed comparison" />
        </div>
      </div>
    </section>

    <section class="section">
      <div class="panel">
        <div class="grid">
          <div class="card">
            <div class="top">
              <h3>Quick read: cumulative growth</h3>
              <p>Simple horizontal bars show how much each index rose from 1960 to 2025.</p>
            </div>
            <img src="cpi-motor-vehicle-insurance-growth-bars.svg" alt="Cumulative growth comparison bar chart" />
          </div>
          <div class="card">
            <div class="top">
              <h3>Teen premium context</h3>
              <p>III explains why the insurance trend matters more for young drivers and their families.</p>
            </div>
            <img src="cpi-teen-pricing-context.svg" alt="Teen pricing context annotation panel" />
          </div>
          <div class="card feature">
            <div class="top">
              <h3>How to frame it</h3>
              <p>Use this language if you want to keep the claim conservative and source-based.</p>
            </div>
            <div style="padding:18px;">
              <div style="border-radius:22px;background:linear-gradient(180deg,#0F172A,#1F3552);color:#fff;padding:24px 22px;box-shadow:inset 0 1px 0 rgba(255,255,255,.08);">
                <div style="font-family:Georgia,'Times New Roman',serif;font-size:48px;line-height:.92;letter-spacing:-.06em;margin-bottom:10px;">3.4x</div>
                <div style="font-size:16px;line-height:1.55;color:rgba(255,255,255,.84);">Motor vehicle insurance rose about 3.4 times as fast as all-items inflation from 1960 to 2025.</div>
                <div style="margin-top:16px;font-size:13px;line-height:1.6;color:rgba(255,255,255,.68);">That is the cleanest headline for the chart package.</div>
              </div>
            </div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px;">
          <div style="background:rgba(255,255,255,.78);border:1px solid rgba(15,23,42,.08);border-radius:24px;padding:20px 22px;">
            <h4 style="margin:0 0 10px;font-size:18px;font-family:Georgia,'Times New Roman',serif;">Source links</h4>
            <ul style="margin:0;padding-left:18px;color:#667085;line-height:1.65;">
              <li><a href="https://www.bls.gov/cpi/factsheets/motor-vehicle-insurance.htm">BLS motor vehicle insurance factsheet</a></li>
              <li><a href="https://data.bls.gov/timeseries/CUUR0000SETE?output_view=data">BLS motor vehicle insurance series page</a></li>
              <li><a href="https://www.bls.gov/developers/api_signature_v2.htm">BLS API signatures</a></li>
              <li><a href="https://www.officialdata.org/us-cpi">Official Data yearly CPI table</a></li>
              <li><a href="https://www.officialdata.org/Motor-vehicle-insurance/price-inflation/1970">Official Data motor vehicle insurance table</a></li>
              <li><a href="https://www.iii.org/issue-update/background-on-teen-drivers">III teen drivers background</a></li>
              <li><a href="https://www.iii.org/article/auto-insurance-teen-drivers">III teen driver insurance</a></li>
            </ul>
          </div>
          <div style="background:rgba(255,255,255,.78);border:1px solid rgba(15,23,42,.08);border-radius:24px;padding:20px 22px;">
            <h4 style="margin:0 0 10px;font-size:18px;font-family:Georgia,'Times New Roman',serif;">Method note</h4>
            <div style="color:#667085;line-height:1.65;">
              BLS series used here are `CUUR0000SA0` and `CUUR0000SETE`. The third series ID you mentioned, `CUUR0000SETOO`, appears to be a typo.
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="footer">
      This is a source-backed editorial package. The CPI chart is the market trend, and the III panel is context for how the cost shock is felt by young drivers and families.
    </div>
  </div>
</body>
</html>
"""
    (outdir / "cpi-editorial.html").write_text(html_doc, encoding="utf-8")


def write_csv(outdir: Path, rows) -> None:
    out = outdir / "cpi-motor-vehicle-insurance-annual.csv"
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "AllItems", "MotorVehicleInsurance", "AllItemsIndex1960", "MotorVehicleInsuranceIndex1960"])
        base_all = rows[0]["AllItems"]
        base_mv = rows[0]["MotorVehicleInsurance"]
        for row in rows:
            writer.writerow(
                [
                    row["Year"],
                    f"{row['AllItems']:.3f}",
                    f"{row['MotorVehicleInsurance']:.3f}",
                    f"{row['AllItems'] / base_all * 100:.1f}",
                    f"{row['MotorVehicleInsurance'] / base_mv * 100:.1f}",
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CPI motor vehicle insurance editorial assets.")
    parser.add_argument("--outdir", type=Path, default=Path("cpi"), help="Output directory.")
    args = parser.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_history(Path(__file__).resolve().parents[1] / "cpi/cpi-motor-vehicle-insurance-history.csv")
    chart_svg = draw_index_chart(rows)
    bars_svg = draw_growth_bars(rows)
    panel_svg = draw_annotation_panel()
    write_csv(outdir, rows)
    (outdir / "cpi-motor-vehicle-insurance-index.svg").write_text(chart_svg, encoding="utf-8")
    (outdir / "cpi-motor-vehicle-insurance-growth-bars.svg").write_text(bars_svg, encoding="utf-8")
    (outdir / "cpi-teen-pricing-context.svg").write_text(panel_svg, encoding="utf-8")
    write_html(outdir, chart_svg, bars_svg, panel_svg)
    print(f"Wrote CPI package to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
