import React, { useMemo, useState } from "react";
import {
  getCpiInsuranceSeries,
  getGasolineShockSeries,
  getTeenAnnualSeries,
  getYouthShareSeries,
} from "../data/licensedDrivers";

const BASE_YEAR = 1963;
const DISPLAY_START_YEAR = 1963;
const HIGHLIGHT_START_YEAR = 1980;
const END_YEAR = 2024;
const SVG_WIDTH = 1540;
const SVG_HEIGHT = 980;
const PLOT_LEFT = 100;
const PLOT_RIGHT = 1080;
const PLOT_TOP = 180;
const PLOT_BOTTOM = 820;
const YEAR_GRID = [1963, 1970, 1980, 1990, 2000, 2010, 2020, 2024];
const TOOLTIP_WIDTH = 246;
const LICENSURE_AXIS_X = 1190;
const TEEN_AXIS_X = 1400;
const LEGEND_Y = 134;

const numberFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

function formatNumber(value) {
  return numberFormatter.format(value);
}

function formatSignedPercent(value) {
  const prefix = value >= 0 ? "+" : "−";
  return `${prefix}${formatNumber(Math.abs(value))}%`;
}

function percentChange(start, end) {
  return ((end - start) / start) * 100;
}

function indexSeries(rows, key, baseYear = BASE_YEAR) {
  const baseRow = rows.find((row) => row.year === baseYear) ?? rows[0];
  const baseValue = baseRow?.[key];
  if (!Number.isFinite(baseValue) || baseValue === 0) {
    throw new Error(`Missing base year data for ${key}`);
  }
  return rows
    .filter((row) => Number.isFinite(row.year) && Number.isFinite(row[key]))
    .map((row) => ({ year: row.year, value: (row[key] / baseValue) * 100 }));
}

function buildLinePath(points, xForYear, yForValue) {
  return points
    .map((point, i) => `${i === 0 ? "M" : "L"} ${xForYear(point.year).toFixed(1)} ${yForValue(point.value).toFixed(1)}`)
    .join(" ");
}

function niceStep(rawStep) {
  if (!Number.isFinite(rawStep) || rawStep <= 0) return 1;
  const exp = Math.floor(Math.log10(rawStep));
  const frac = rawStep / 10 ** exp;
  const nice = frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 2.5 ? 2.5 : frac <= 5 ? 5 : 10;
  return nice * 10 ** exp;
}

function buildLinearScale(values, plotTop, plotBottom, { min = 0, max = null, tickCount = 5, paddingRatio = 0.08 } = {}) {
  const finite = values.filter(Number.isFinite);
  const maxValue = max ?? Math.max(...finite, min);
  const span = Math.max(maxValue - min, 1);
  const paddedMax = max ?? maxValue + span * paddingRatio;
  const step = niceStep((paddedMax - min) / Math.max(1, tickCount - 1));
  const domainMin = min;
  const domainMax = max ?? Math.ceil(paddedMax / step) * step;
  const ticks = [];
  for (let t = domainMin; t <= domainMax + step / 2; t += step) {
    ticks.push(Number(t.toFixed(6)));
  }
  return {
    domainMin,
    domainMax,
    ticks,
    yForValue: (value) => {
      const bounded = Math.max(value, domainMin);
      return plotBottom - ((bounded - domainMin) / (domainMax - domainMin)) * (plotBottom - plotTop);
    },
  };
}

function buildLogScale(values, plotTop, plotBottom) {
  const finite = values.filter(Number.isFinite);
  const dataMax = Math.max(...finite);
  const domainMin = 80;
  const domainMax = dataMax * 1.12;
  const logMin = Math.log10(domainMin);
  const logMax = Math.log10(domainMax);
  return {
    domainMin,
    domainMax,
    ticks: [80, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 4000].filter(
      (t) => t >= domainMin && t <= domainMax,
    ),
    yForValue: (value) => {
      const bounded = Math.max(value, domainMin);
      return plotBottom - ((Math.log10(bounded) - logMin) / (logMax - logMin)) * (plotBottom - plotTop);
    },
  };
}

export default function OverlayExperimentChart() {
  const [hoverYear, setHoverYear] = useState(2024);
  const [hoveredSeriesId, setHoveredSeriesId] = useState(null);

  const driving = useMemo(
    () => [
      {
        id: "insurance",
        label: "Motor vehicle insurance",
        color: "#C65A6A",
        points: indexSeries(
          getCpiInsuranceSeries().map((row) => ({ year: row.year, insurance: row.insurance })),
          "insurance",
          BASE_YEAR,
        ).filter((row) => row.year >= DISPLAY_START_YEAR && row.year <= END_YEAR),
      },
      {
        id: "gasoline",
        label: "Gasoline price",
        color: "#244A71",
        points: indexSeries(
          getGasolineShockSeries().map((row) => ({ year: row.year, gasoline: row.gasoline })),
          "gasoline",
          BASE_YEAR,
        ).filter((row) => row.year >= DISPLAY_START_YEAR && row.year <= END_YEAR),
      },
    ],
    [],
  );

  const teenLabor = useMemo(
    () => getTeenAnnualSeries().filter((row) => row.year >= DISPLAY_START_YEAR && row.year <= END_YEAR),
    [],
  );
  const licensure = useMemo(
    () => getYouthShareSeries().filter((row) => row.year >= DISPLAY_START_YEAR && row.year <= END_YEAR),
    [],
  );

  const allYears = useMemo(
    () =>
      [
        ...new Set([
          ...driving.flatMap((s) => s.points.map((p) => p.year)),
          ...teenLabor.map((r) => r.year),
          ...licensure.map((r) => r.year),
        ]),
      ].sort((a, b) => a - b),
    [driving, teenLabor, licensure],
  );

  const xForYear = useMemo(() => {
    const span = allYears[allYears.length - 1] - allYears[0];
    return (year) => PLOT_LEFT + ((year - allYears[0]) / span) * (PLOT_RIGHT - PLOT_LEFT);
  }, [allYears]);

  const drivingScale = useMemo(
    () => buildLogScale(driving.flatMap((s) => s.points.map((p) => p.value)), PLOT_TOP, PLOT_BOTTOM),
    [driving],
  );
  const teenScale = useMemo(
    () => buildLinearScale(teenLabor.map((r) => r.lfpr), PLOT_TOP, PLOT_BOTTOM, { min: 30, tickCount: 5, paddingRatio: 0.04 }),
    [teenLabor],
  );
  const licensureScale = useMemo(
    () => buildLinearScale(licensure.map((r) => r.share), PLOT_TOP, PLOT_BOTTOM, { min: 0, max: 6, tickCount: 4, paddingRatio: 0 }),
    [licensure],
  );

  const clipPathId = "overlay-experiment-clip";
  const plotHeight = PLOT_BOTTOM - PLOT_TOP;
  const yearGridYears = YEAR_GRID.filter((y) => y >= allYears[0] && y <= allYears[allYears.length - 1]);
  const selectedYear = hoverYear ?? allYears[allYears.length - 1];
  const showTooltip = hoverYear !== null;
  const selectedX = xForYear(selectedYear);
  const isTeenHovered = hoveredSeriesId === "teen";

  // Smart tooltip: show on whichever side has more room
  const midX = (PLOT_LEFT + PLOT_RIGHT) / 2;
  const tooltipOnLeft = selectedX > midX;
  const tooltipX = tooltipOnLeft
    ? Math.max(PLOT_LEFT + 4, selectedX - TOOLTIP_WIDTH - 16)
    : Math.min(selectedX + 16, PLOT_RIGHT - TOOLTIP_WIDTH - 4);
  const tooltipLabelX = tooltipX + 14;

  const selectedDriving = useMemo(
    () => driving.map((s) => ({ ...s, point: s.points.find((p) => p.year === selectedYear) })),
    [driving, selectedYear],
  );
  const selectedTeen = useMemo(
    () => teenLabor.find((r) => r.year === selectedYear),
    [teenLabor, selectedYear],
  );
  const selectedLicensure = useMemo(
    () => licensure.find((r) => r.year === selectedYear),
    [licensure, selectedYear],
  );

  const tooltipRows = useMemo(
    () =>
      [
        selectedLicensure
          ? { label: "16–18 share", value: `${formatNumber(selectedLicensure.share)}%`, color: "#8A6400" }
          : null,
        selectedTeen
          ? { label: "Teen LFPR", value: `${formatNumber(selectedTeen.lfpr)}%`, color: "#1F7A8C" }
          : null,
        {
          label: "Insurance idx",
          value: formatNumber(selectedDriving[0]?.point?.value ?? 0),
          color: "#C65A6A",
        },
        {
          label: "Gasoline idx",
          value: formatNumber(selectedDriving[1]?.point?.value ?? 0),
          color: "#244A71",
        },
      ].filter(Boolean),
    [selectedLicensure, selectedTeen, selectedDriving],
  );
  const tooltipHeight = 40 + tooltipRows.length * 22 + 8;

  const highlights = useMemo(() => {
    const startYear = HIGHLIGHT_START_YEAR;
    const endYear = END_YEAR;
    const startLicensure = licensure.find((r) => r.year === startYear);
    const endLicensure = licensure.find((r) => r.year === endYear);
    const startTeen = teenLabor.find((r) => r.year === startYear);
    const endTeen = teenLabor.find((r) => r.year === endYear);
    const insSeries = driving.find((s) => s.id === "insurance")?.points;
    const gasSeries = driving.find((s) => s.id === "gasoline")?.points;
    const startIns = insSeries?.find((p) => p.year === startYear);
    const endIns = insSeries?.find((p) => p.year === endYear);
    const startGas = gasSeries?.find((p) => p.year === startYear);
    const endGas = gasSeries?.find((p) => p.year === endYear);
    if (!startLicensure || !endLicensure || !startTeen || !endTeen || !startIns || !endIns || !startGas || !endGas) {
      return [];
    }
    return [
      {
        id: "licensure",
        label: "Teen licensure rate",
        color: "#8A6400",
        value: formatSignedPercent(percentChange(startLicensure.share, endLicensure.share)),
        detail: `${formatNumber(startLicensure.share)}% in ${startYear} → ${formatNumber(endLicensure.share)}% in ${endYear}`,
        note: "16-to-18-year-olds as share of all U.S. licensed drivers. Source: FHWA DL-220.",
      },
      {
        id: "teen-lfpr",
        label: "Teen LFPR",
        color: "#1F7A8C",
        value: formatSignedPercent(percentChange(startTeen.lfpr, endTeen.lfpr)),
        detail: `${formatNumber(startTeen.lfpr)}% in ${startYear} → ${formatNumber(endTeen.lfpr)}% in ${endYear}`,
        note: "Share of teens (16–19) working or seeking work. Source: BLS Current Population Survey.",
      },
      {
        id: "gasoline",
        label: "Gasoline price index",
        color: "#244A71",
        value: formatSignedPercent(percentChange(startGas.value, endGas.value)),
        detail: `Index ${formatNumber(startGas.value)} in ${startYear} → ${formatNumber(endGas.value)} in ${endYear} (1963 = 100)`,
        note: "Annual avg. regular gas price. In real (inflation-adj.) terms, cheaper in 2024 than 1980. Source: U.S. EIA.",
      },
      {
        id: "insurance",
        label: "Insurance price index",
        color: "#C65A6A",
        value: formatSignedPercent(percentChange(startIns.value, endIns.value)),
        detail: `Index ${formatNumber(startIns.value)} in ${startYear} → ${formatNumber(endIns.value)} in ${endYear} (1963 = 100)`,
        note: "CPI Motor Vehicle Insurance (CUUR0000SETA02). In real terms, 2.7× more than 1980. Source: BLS.",
      },
    ];
  }, [driving, teenLabor, licensure]);

  const handlePointerMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * SVG_WIDTH;
    const clamped = Math.max(PLOT_LEFT, Math.min(PLOT_RIGHT, x));
    const span = allYears[allYears.length - 1] - allYears[0];
    const rawYear = allYears[0] + ((clamped - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT)) * span;
    const nearest = allYears.reduce(
      (best, c) => (Math.abs(c - rawYear) < Math.abs(best - rawYear) ? c : best),
      allYears[0],
    );
    setHoverYear(nearest);
  };

  // Pre-compute path strings
  const drivingPaths = useMemo(
    () => driving.map((s) => ({ ...s, d: buildLinePath(s.points, xForYear, drivingScale.yForValue) })),
    [driving, xForYear, drivingScale],
  );
  const teenPathD = useMemo(
    () => buildLinePath(teenLabor.map((r) => ({ year: r.year, value: r.lfpr })), xForYear, teenScale.yForValue),
    [teenLabor, xForYear, teenScale],
  );

  // 1974 peak annotation position (6.28% — highest share on record)
  const peak1974X = xForYear(1974);
  const peak1974 = licensure.find((r) => r.year === 1974);
  const peak1974Y = peak1974 ? licensureScale.yForValue(peak1974.share) : null;

  return (
    <section className="chart-card chart-card-separated">
      <div className="panel-chart-header">
        <div>
          <p className="panel-chart-kicker">Federal data &nbsp;&middot;&nbsp; 1963&ndash;2024</p>
          <h3>Driving costs, teen licensure, and youth labor participation — 61 years of federal data</h3>
          <p>
            Motor vehicle insurance and gasoline price indices (left axis, 1963&nbsp;=&nbsp;100) plotted alongside
            16&ndash;18-year-old licensed driver share (gold bars, inner right axis) and annual teen labor force
            participation (teal line, outer right axis). Hover any year to read across all series simultaneously.
          </p>
        </div>
        <div className="chart-badge">Interactive</div>
      </div>

      <div className="panel-chart-frame">
        <svg
          className="panel-chart-svg"
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          role="img"
          aria-label="Chart showing U.S. motor vehicle insurance and gasoline cost indices, teen 16-18 licensed driver share bars, and annual teen labor force participation, 1963 to 2024."
          style={{ cursor: "crosshair" }}
          onPointerMove={handlePointerMove}
          onPointerLeave={() => {
            setHoverYear(null);
            setHoveredSeriesId(null);
          }}
        >
          <defs>
            <clipPath id={clipPathId}>
              <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={plotHeight} />
            </clipPath>
          </defs>

          {/* Background */}
          <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} rx="24" fill="#FFFDF8" />

          {/* SVG header text */}
          <text x={PLOT_LEFT} y="52" className="svg-kicker">
            Youth &amp; Mobility &nbsp;&middot;&nbsp; FHWA / BLS / EIA &nbsp;&middot;&nbsp; 1963&ndash;2024
          </text>
          <text x={PLOT_LEFT} y="82" className="svg-title">
            Teen drivers&apos; share of U.S. roads peaked in 1974 and has fallen 61% since
          </text>
          <text x={PLOT_LEFT} y="108" className="svg-subtitle">
            Insurance &amp; gasoline indices (left axis, 1963=100) &nbsp;&middot;&nbsp; 16&ndash;18 licensed driver share % (gold bars) &nbsp;&middot;&nbsp; Annual teen LFPR % (teal, right axis)
          </text>

          {/* Legend */}
          <g aria-label="Chart legend">
            <line
              x1={PLOT_LEFT}
              x2={PLOT_LEFT + 24}
              y1={LEGEND_Y}
              y2={LEGEND_Y}
              stroke={hoveredSeriesId === "insurance" ? "#A43F54" : "#C65A6A"}
              strokeWidth={hoveredSeriesId === "insurance" ? "5.5" : "4"}
              strokeLinecap="round"
            />
            <circle cx={PLOT_LEFT + 12} cy={LEGEND_Y} r="3.5" fill="#C65A6A" stroke="#FFFDF8" strokeWidth="1.5" />
            <text
              x={PLOT_LEFT + 32}
              y={LEGEND_Y + 4}
              className="axis-label axis-label-start"
              fill={hoveredSeriesId === "insurance" ? "#A43F54" : "#C65A6A"}
              fontWeight={hoveredSeriesId === "insurance" ? "800" : "700"}
            >
              Insurance index
            </text>

            <line
              x1={PLOT_LEFT + 162}
              x2={PLOT_LEFT + 186}
              y1={LEGEND_Y}
              y2={LEGEND_Y}
              stroke={hoveredSeriesId === "gasoline" ? "#16324D" : "#244A71"}
              strokeWidth={hoveredSeriesId === "gasoline" ? "5" : "3.5"}
              strokeLinecap="round"
            />
            <circle cx={PLOT_LEFT + 174} cy={LEGEND_Y} r="3.5" fill="#244A71" stroke="#FFFDF8" strokeWidth="1.5" />
            <text
              x={PLOT_LEFT + 194}
              y={LEGEND_Y + 4}
              className="axis-label axis-label-start"
              fill={hoveredSeriesId === "gasoline" ? "#16324D" : "#244A71"}
              fontWeight={hoveredSeriesId === "gasoline" ? "800" : "700"}
            >
              Gasoline index
            </text>

            <line
              x1={PLOT_LEFT + 330}
              x2={PLOT_LEFT + 354}
              y1={LEGEND_Y}
              y2={LEGEND_Y}
              stroke={hoveredSeriesId === "teen" ? "#16616E" : "#1F7A8C"}
              strokeWidth={hoveredSeriesId === "teen" ? "5.2" : "3.8"}
              strokeLinecap="round"
            />
            <circle cx={PLOT_LEFT + 342} cy={LEGEND_Y} r="3.5" fill="#1F7A8C" stroke="#FFFDF8" strokeWidth="1.5" />
            <text
              x={PLOT_LEFT + 362}
              y={LEGEND_Y + 4}
              className="axis-label axis-label-start"
              fill={hoveredSeriesId === "teen" ? "#16616E" : "#1F7A8C"}
              fontWeight={hoveredSeriesId === "teen" ? "800" : "700"}
            >
              Teen LFPR (ages 16&ndash;19)
            </text>

            <rect x={PLOT_LEFT + 524} y={LEGEND_Y - 6} width="12" height="12" rx="2.5" fill="#E0B24C" />
            <text x={PLOT_LEFT + 542} y={LEGEND_Y + 4} className="axis-label axis-label-start" fill="#8A6400" fontWeight="700">
              16&ndash;18 licensed share
            </text>
          </g>

          {/* Plot backdrop */}
          <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={plotHeight} className="plot-backdrop" />

          {/* Left axis (log scale, driving costs) */}
          {drivingScale.ticks.map((tick) => {
            const y = drivingScale.yForValue(tick);
            return (
              <g key={`drive-${tick}`}>
                <line x1={PLOT_LEFT} x2={PLOT_LEFT + 8} y1={y} y2={y} className="axis-tick" />
                <text x={PLOT_LEFT - 10} y={y + 4} className="axis-label axis-label-right">
                  {tick >= 1000 ? `${(tick / 1000).toFixed(tick % 1000 === 0 ? 0 : 1)}k` : formatNumber(tick)}
                </text>
              </g>
            );
          })}
          <text
            x={PLOT_LEFT - 10}
            y={PLOT_TOP - 16}
            className="axis-label axis-label-right"
            fill="#667085"
            fontWeight="700"
          >
            Index
          </text>
          <text
            x={PLOT_LEFT - 10}
            y={PLOT_TOP - 4}
            className="axis-label axis-label-right"
            fill="#667085"
          >
            1963=100
          </text>

          {/* Teen LFPR grid lines + right-side tick marks */}
          {teenScale.ticks.map((tick) => {
            const y = teenScale.yForValue(tick);
            return (
              <g key={`teen-${tick}`}>
                <line x1={PLOT_LEFT} x2={PLOT_RIGHT} y1={y} y2={y} className="grid-line" />
                <line x1={TEEN_AXIS_X} x2={TEEN_AXIS_X + 8} y1={y} y2={y} className="axis-tick" />
                <text x={TEEN_AXIS_X + 12} y={y + 4} className="axis-label axis-label-start" fill="#1F7A8C">
                  {formatNumber(tick)}%
                </text>
              </g>
            );
          })}

          {/* Year grid + x-axis labels */}
          {yearGridYears.map((year) => {
            const x = xForYear(year);
            return (
              <g key={year}>
                <line x1={x} x2={x} y1={PLOT_TOP} y2={PLOT_BOTTOM} className="vertical-grid-line" />
                <text x={x} y={PLOT_BOTTOM + 24} className="axis-label axis-label-center">
                  {year}
                </text>
              </g>
            );
          })}

          {/* Licensure (bar scale) right axis */}
          {licensureScale.ticks.map((tick) => {
            const y = licensureScale.yForValue(tick);
            return (
              <g key={`lic-${tick}`}>
                <line x1={LICENSURE_AXIS_X} x2={LICENSURE_AXIS_X + 8} y1={y} y2={y} className="axis-tick" />
                <text x={LICENSURE_AXIS_X + 12} y={y + 4} className="axis-label axis-label-start" fill="#8A6400">
                  {formatNumber(tick)}%
                </text>
              </g>
            );
          })}

          {/* Right axis lines */}
          <line
            x1={LICENSURE_AXIS_X}
            x2={LICENSURE_AXIS_X}
            y1={PLOT_TOP}
            y2={PLOT_BOTTOM}
            stroke="#D4A017"
            strokeWidth="1.5"
            strokeDasharray="6 4"
          />
          <line
            x1={TEEN_AXIS_X}
            x2={TEEN_AXIS_X}
            y1={PLOT_TOP}
            y2={PLOT_BOTTOM}
            stroke="rgba(31,122,140,0.2)"
            strokeWidth="1"
          />

          {/* Right axis header labels */}
          <text
            x={LICENSURE_AXIS_X}
            y={PLOT_TOP - 18}
            className="axis-label axis-label-center"
            fill="#8A6400"
            fontWeight="700"
          >
            16&ndash;18 driver share
          </text>
          <text
            x={TEEN_AXIS_X}
            y={PLOT_TOP - 18}
            className="axis-label axis-label-center"
            fill="#1F7A8C"
            fontWeight="700"
          >
            Annual teen LFPR
          </text>

          {/* Chart content inside clip path */}
          <g clipPath={`url(#${clipPathId})`}>
            {/* Licensure bars */}
            {licensure.map((row) => {
              const x = xForYear(row.year);
              const barTop = licensureScale.yForValue(row.share);
              const barBase = licensureScale.yForValue(0);
              const barH = Math.max(0, barBase - barTop);
              const isSelected = row.year === selectedYear;
              const barW = isSelected ? 10 : 7;
              return (
                <rect
                  key={`lic-${row.year}`}
                  x={x - barW / 2}
                  y={barTop}
                  width={barW}
                  height={barH}
                  rx="2"
                  fill={isSelected ? "#C89200" : "#E0B24C"}
                  opacity={isSelected ? 0.92 : 0.52}
                  stroke={isSelected ? "#8A6400" : "none"}
                  strokeWidth={isSelected ? "1.5" : "0"}
                  pointerEvents="none"
                />
              );
            })}

            {/* Driving cost lines */}
            {drivingPaths.map((series) => (
              <g key={series.id}>
                <path
                  d={series.d}
                  fill="none"
                  stroke={series.color}
                  strokeWidth={series.id === "insurance" ? 4 : 3.2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  pointerEvents="none"
                  opacity={hoveredSeriesId && hoveredSeriesId !== series.id ? 0.22 : 1}
                />
                {/* Wide invisible hit area */}
                <path
                  d={series.d}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="24"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  onPointerEnter={() => setHoveredSeriesId(series.id)}
                  onPointerLeave={() => setHoveredSeriesId(null)}
                />
              </g>
            ))}

            {/* Teen LFPR line */}
            <path
              d={teenPathD}
              fill="none"
              stroke={isTeenHovered ? "#16616E" : "#1F7A8C"}
              strokeWidth={isTeenHovered ? 5 : 3.6}
              strokeLinecap="round"
              strokeLinejoin="round"
              pointerEvents="none"
              opacity={hoveredSeriesId && hoveredSeriesId !== "teen" ? 0.22 : 1}
            />
            <path
              d={teenPathD}
              fill="none"
              stroke="transparent"
              strokeWidth="24"
              strokeLinecap="round"
              strokeLinejoin="round"
              onPointerEnter={() => setHoveredSeriesId("teen")}
              onPointerLeave={() => setHoveredSeriesId(null)}
            />

            {/* Hover crosshair */}
            {showTooltip && (
              <line
                x1={selectedX}
                x2={selectedX}
                y1={PLOT_TOP}
                y2={PLOT_BOTTOM}
                stroke="rgba(23,32,51,0.2)"
                strokeWidth="1.5"
                strokeDasharray="5 5"
                pointerEvents="none"
              />
            )}

            {/* Hover dots on lines */}
            {showTooltip &&
              selectedDriving.map((series) =>
                series.point ? (
                  <circle
                    key={`dot-${series.id}`}
                    cx={selectedX}
                    cy={drivingScale.yForValue(series.point.value)}
                    r={hoveredSeriesId === series.id ? 7 : 5}
                    fill={series.color}
                    stroke="#FFFDF8"
                    strokeWidth="2"
                    pointerEvents="none"
                  />
                ) : null,
              )}
            {showTooltip && selectedTeen && (
              <circle
                cx={selectedX}
                cy={teenScale.yForValue(selectedTeen.lfpr)}
                r={isTeenHovered ? 7 : 5}
                fill={isTeenHovered ? "#16616E" : "#1F7A8C"}
                stroke="#FFFDF8"
                strokeWidth="2"
                pointerEvents="none"
              />
            )}
            {showTooltip && selectedLicensure && (
              <circle
                cx={selectedX}
                cy={licensureScale.yForValue(selectedLicensure.share)}
                r="5"
                fill="#C89200"
                stroke="#FFFDF8"
                strokeWidth="2"
                pointerEvents="none"
              />
            )}
          </g>

          {/* 1974 peak annotation — outside clip path so it floats above bars */}
          {peak1974Y !== null && (
            <g pointerEvents="none">
              <line
                x1={peak1974X}
                x2={peak1974X}
                y1={peak1974Y - 28}
                y2={peak1974Y - 7}
                stroke="#A07800"
                strokeWidth="1.2"
                strokeDasharray="3 2"
              />
              <text
                x={peak1974X}
                y={peak1974Y - 34}
                className="axis-label axis-label-center"
                fill="#8A6400"
                fontWeight="700"
                fontSize="10"
              >
                All-time peak 1974
              </text>
            </g>
          )}

          {/* Tooltip */}
          {showTooltip && (
            <g pointerEvents="none">
              <rect
                x={tooltipX + 2}
                y={PLOT_TOP + 12}
                width={TOOLTIP_WIDTH}
                height={tooltipHeight}
                rx="12"
                fill="rgba(0,0,0,0.05)"
              />
              <rect
                x={tooltipX}
                y={PLOT_TOP + 10}
                width={TOOLTIP_WIDTH}
                height={tooltipHeight}
                rx="12"
                fill="#FFFFFF"
                stroke="rgba(23,32,51,0.1)"
                strokeWidth="1"
              />
              <text
                x={tooltipLabelX}
                y={PLOT_TOP + 34}
                className="axis-label axis-label-start"
                fill="#101828"
                fontWeight="800"
                fontSize="13"
              >
                {selectedYear}
              </text>
              {tooltipRows.map((row, i) => (
                <g key={row.label}>
                  <circle cx={tooltipLabelX + 5} cy={PLOT_TOP + 50 + i * 22} r="4" fill={row.color} />
                  <text
                    x={tooltipLabelX + 16}
                    y={PLOT_TOP + 54 + i * 22}
                    className="axis-label axis-label-start"
                    fill={row.color}
                    fontWeight="600"
                  >
                    {row.label}: {row.value}
                  </text>
                </g>
              ))}
            </g>
          )}

          {/* Source line */}
          <text x={PLOT_LEFT} y={SVG_HEIGHT - 32} className="axis-label axis-label-start">
            Sources: FHWA Highway Statistics DL-220 (driver counts) &nbsp;&middot;&nbsp; BLS CPI CUUR0000SETA02 (insurance) &nbsp;&middot;&nbsp; U.S. EIA (gasoline) &nbsp;&middot;&nbsp; BLS CPS annual survey (teen LFPR)
          </text>
        </svg>
      </div>

      {/* Highlights summary */}
      <div className="chart-summary chart-summary-global overlay-highlights">
        <div className="overlay-highlights-header">
          <span className="summary-label">
            1980 to 2024 &nbsp;&middot;&nbsp; Four federal data series
          </span>
          <strong>
            Insurance rose 928%. Teen driving fell 54.5%. Teen work fell 35%. Four decades of divergence, in the same frame.
          </strong>
        </div>
        <p className="overlay-highlights-note">
          Percentage changes measured from 1980 to 2024 using uninterpolated source data. Chart shows full record from 1963.
          LFPR&nbsp;= labor force participation rate, ages 16&ndash;19. Cost indices re-indexed to 1963&nbsp;=&nbsp;100. Sources: FHWA, BLS, EIA.
        </p>
        <div className="highlight-grid">
          {highlights.map((item) => (
            <div key={item.id} className="highlight-card" style={{ "--accent": item.color }}>
              <span className="highlight-label">{item.label}</span>
              <strong className="highlight-value">{item.value}</strong>
              <span className="highlight-detail">{item.detail}</span>
              <span className="highlight-note">{item.note}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
