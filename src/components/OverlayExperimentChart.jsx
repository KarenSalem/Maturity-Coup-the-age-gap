import React, { useMemo, useState } from "react";
import {
  getCpiInsuranceSeries,
  getGasolineShockSeries,
  getTeenAnnualSeries,
  getYouthShareSeries,
} from "../data/licensedDrivers";

const BASE_YEAR = 1963;
const END_YEAR = 2024;
const SVG_WIDTH = 1320;
const SVG_HEIGHT = 940;
const PLOT_LEFT = 100;
const PLOT_RIGHT = 1020;
const PLOT_TOP = 160;
const PLOT_BOTTOM = 770;
const YEAR_GRID = [1963, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024];

const numberFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1,
});

function formatNumber(value) {
  return numberFormatter.format(value);
}

function indexSeries(rows, key) {
  const baseRow = rows.find((row) => row.year === BASE_YEAR) ?? rows[0];
  const baseValue = baseRow?.[key];

  if (!Number.isFinite(baseValue) || baseValue === 0) {
    throw new Error(`Missing base year data for ${key}`);
  }

  return rows
    .filter((row) => Number.isFinite(row.year) && Number.isFinite(row[key]))
    .map((row) => ({
      year: row.year,
      value: (row[key] / baseValue) * 100,
    }));
}

function buildLinePath(points, xForYear, yForValue) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${xForYear(point.year).toFixed(1)} ${yForValue(point.value).toFixed(1)}`).join(" ");
}

function niceStep(rawStep) {
  if (!Number.isFinite(rawStep) || rawStep <= 0) {
    return 1;
  }

  const exponent = Math.floor(Math.log10(rawStep));
  const fraction = rawStep / 10 ** exponent;
  const niceFraction = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 2.5 ? 2.5 : fraction <= 5 ? 5 : 10;
  return niceFraction * 10 ** exponent;
}

function buildLinearScale(values, plotTop, plotBottom, { min = 0, max = null, tickCount = 5, paddingRatio = 0.08 } = {}) {
  const finiteValues = values.filter((value) => Number.isFinite(value));
  const maxValue = max ?? Math.max(...finiteValues, min);
  const span = Math.max(maxValue - min, 1);
  const paddedMax = max ?? maxValue + span * paddingRatio;
  const step = niceStep((paddedMax - min) / Math.max(1, tickCount - 1));
  const domainMin = min;
  const domainMax = max ?? Math.ceil(paddedMax / step) * step;
  const ticks = [];

  for (let tick = domainMin; tick <= domainMax + step / 2; tick += step) {
    ticks.push(Number(tick.toFixed(6)));
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
  const finiteValues = values.filter((value) => Number.isFinite(value));
  const domainMin = 50;
  const domainMax = Math.max(...finiteValues, domainMin) * 1.08;
  const logMin = Math.log10(domainMin);
  const logMax = Math.log10(domainMax);

  return {
    domainMin,
    domainMax,
    ticks: [50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2500, 4000].filter((tick) => tick >= domainMin && tick <= domainMax),
    yForValue: (value) => {
      const bounded = Math.max(value, domainMin);
      return plotBottom - ((Math.log10(bounded) - logMin) / (logMax - logMin)) * (plotBottom - plotTop);
    },
  };
}

export default function OverlayExperimentChart() {
  const [hoverYear, setHoverYear] = useState(2024);

  const driving = [
    {
      id: "insurance",
      label: "Motor vehicle insurance",
      color: "#C65A6A",
      points: indexSeries(
        getCpiInsuranceSeries().map((row) => ({ year: row.year, insurance: row.insurance })),
        "insurance",
      ).filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR),
    },
    {
      id: "gasoline",
      label: "Gasoline price",
      color: "#244A71",
      points: indexSeries(
        getGasolineShockSeries().map((row) => ({ year: row.year, gasoline: row.gasoline })),
        "gasoline",
      ).filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR),
    },
  ];

  const teenLabor = getTeenAnnualSeries().filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR);
  const licensure = getYouthShareSeries().filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR);

  const allYears = [...new Set([
    ...driving.flatMap((series) => series.points.map((point) => point.year)),
    ...teenLabor.map((row) => row.year),
    ...licensure.map((row) => row.year),
  ])].sort((a, b) => a - b);

  const xForYear = (year) => {
    const span = allYears[allYears.length - 1] - allYears[0];
    return PLOT_LEFT + ((year - allYears[0]) / span) * (PLOT_RIGHT - PLOT_LEFT);
  };

  const drivingScale = buildLogScale(driving.flatMap((series) => series.points.map((point) => point.value)), PLOT_TOP, PLOT_BOTTOM);
  const teenScale = buildLinearScale(teenLabor.map((row) => row.lfpr), PLOT_TOP, PLOT_BOTTOM, { min: 30, tickCount: 6, paddingRatio: 0 });
  const licensureScale = buildLinearScale(licensure.map((row) => row.share), PLOT_TOP, PLOT_BOTTOM, { min: 0, max: 6, tickCount: 4, paddingRatio: 0 });
  const teenAxisX = 1128;
  const licensureAxisX = 1078;
  const licensureTopX = 1048;
  const clipPathId = "overlay-experiment-clip";

  const drivingPath = (series) => buildLinePath(series.points, xForYear, drivingScale.yForValue);
  const teenPath = buildLinePath(
    teenLabor.map((row) => ({ year: row.year, value: row.lfpr })),
    xForYear,
    teenScale.yForValue,
  );

  const plotHeight = PLOT_BOTTOM - PLOT_TOP;
  const yearGridYears = YEAR_GRID.filter((year) => year >= allYears[0] && year <= allYears[allYears.length - 1]);
  const selectedYear = hoverYear ?? allYears[allYears.length - 1];
  const showTooltip = hoverYear !== null;
  const selectedX = xForYear(selectedYear);

  const selectedDriving = useMemo(
    () =>
      driving.map((series) => ({
        ...series,
        point: series.points.find((point) => point.year === selectedYear),
      })),
    [driving, selectedYear],
  );
  const selectedTeen = useMemo(
    () => teenLabor.find((row) => row.year === selectedYear),
    [teenLabor, selectedYear],
  );
  const selectedLicensure = useMemo(
    () => licensure.find((row) => row.year === selectedYear),
    [licensure, selectedYear],
  );

  const handlePointerMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * SVG_WIDTH;
    const clamped = Math.max(PLOT_LEFT, Math.min(PLOT_RIGHT, x));
    const span = allYears[allYears.length - 1] - allYears[0];
    const year = Math.round(allYears[0] + ((clamped - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT)) * span);
    const nearest = allYears.reduce((best, candidate) =>
      Math.abs(candidate - year) < Math.abs(best - year) ? candidate : best,
    allYears[0]);
    setHoverYear(nearest);
  };

  return (
    <section className="chart-card chart-card-separated">
      <div className="panel-chart-header">
        <div>
          <p className="panel-chart-kicker">Experimental overlay</p>
          <h3>One combo chart with a bar overlay for teen licensure</h3>
          <p>
            This version keeps driving costs on the left, puts annual teen LFPR on the right line axis, and uses gold bars for teen
            licensure on a fixed 0-6% bar scale. It is a useful experiment, but the dual right-side percentage scales make it more
            complex than the cleaner split-panel version.
          </p>
        </div>
        <div className="chart-badge">Separate route</div>
      </div>

      <div className="panel-chart-frame">
        <svg
          className="panel-chart-svg"
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          role="img"
          aria-label="Experimental chart with driving costs, teen licensure bars, and annual teen labor participation."
          onPointerMove={handlePointerMove}
          onPointerLeave={() => setHoverYear(null)}
        >
          <defs>
            <clipPath id={clipPathId}>
              <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={plotHeight} />
            </clipPath>
          </defs>
          <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} rx="24" fill="#FFFDF8" />
          <text x={PLOT_LEFT} y="58" className="svg-kicker">Experimental combo</text>
          <text x={PLOT_LEFT} y="86" className="svg-title">Driving costs, teen licensure, and annual teen labor participation in one frame.</text>
          <text x={PLOT_LEFT} y="114" className="svg-subtitle">
            Bars use a fixed 0-6% licensure scale. The teal line is annual teen LFPR. The left axis stays on indexed driving costs.
          </text>

          <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={plotHeight} className="plot-backdrop" />

          {drivingScale.ticks.map((tick) => {
            const y = drivingScale.yForValue(tick);
            return (
              <g key={`drive-${tick}`}>
                <line x1={PLOT_LEFT} x2={PLOT_LEFT + 10} y1={y} y2={y} className="axis-tick" />
                <text x={PLOT_LEFT - 14} y={y + 4} className="axis-label axis-label-right">{formatNumber(tick)}</text>
              </g>
            );
          })}

          {teenScale.ticks.map((tick) => {
            const y = teenScale.yForValue(tick);
            return (
              <g key={`teen-${tick}`}>
                <line x1={PLOT_LEFT} x2={PLOT_RIGHT} y1={y} y2={y} className="grid-line" />
                <text x={teenAxisX} y={y + 4} className="axis-label axis-label-start">{formatNumber(tick)}%</text>
              </g>
            );
          })}

          {yearGridYears.map((year) => {
            const x = xForYear(year);
            return (
              <g key={year}>
                <line x1={x} x2={x} y1={PLOT_TOP} y2={PLOT_BOTTOM} className="vertical-grid-line" />
                <text x={x} y={PLOT_BOTTOM + 26} className="axis-label axis-label-center">{year}</text>
              </g>
            );
          })}

          {licensureScale.ticks.map((tick) => {
            const y = licensureScale.yForValue(tick);
            return (
              <g key={`lic-${tick}`}>
                <line x1={licensureAxisX - 10} x2={licensureAxisX} y1={y} y2={y} className="axis-tick" />
                <text x={licensureAxisX - 14} y={y + 4} className="axis-label axis-label-right" fill="#A15922">{formatNumber(tick)}%</text>
              </g>
            );
          })}

          <line x1={licensureAxisX} x2={licensureAxisX} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="#D4A017" strokeWidth="2" strokeDasharray="6 5" />
          <text x={licensureAxisX} y={PLOT_TOP - 20} className="axis-label axis-label-center" fill="#8A6400" fontWeight="700">Licensure bars 0-6%</text>
          <line x1={teenAxisX} x2={teenAxisX} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(23, 32, 51, 0.12)" strokeWidth="1" />
          <text x={teenAxisX} y={PLOT_TOP - 20} className="axis-label axis-label-start" fill="#1F7A8C" fontWeight="700">Annual teen LFPR</text>

          <g clipPath={`url(#${clipPathId})`}>
            {driving.map((series) => (
              <path
                key={series.id}
                d={drivingPath(series)}
                fill="none"
                stroke={series.color}
                strokeWidth={series.id === "insurance" ? 4.5 : 3.8}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}

            {licensure.map((row) => {
              const x = xForYear(row.year);
              const barTop = licensureScale.yForValue(row.share);
              const barBase = licensureScale.yForValue(0);
              const barHeight = Math.max(0, barBase - barTop);
              const isSelected = row.year === selectedYear;
              return (
                <rect
                  key={`lic-${row.year}`}
                  x={x - 4}
                  y={barTop}
                  width="8"
                  height={barHeight}
                  rx="2"
                  fill="#E0B24C"
                  opacity="0.55"
                  stroke={isSelected ? "#8A6400" : "none"}
                  strokeWidth={isSelected ? "1.5" : "0"}
                />
              );
            })}

            <path
              d={teenPath}
              fill="none"
              stroke="#1F7A8C"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            <line x1={selectedX} x2={selectedX} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(23, 32, 51, 0.24)" strokeWidth="1.5" strokeDasharray="6 6" />
            {selectedDriving.map((series) => {
              if (!series.point) {
                return null;
              }
              return (
                <circle
                  key={`sel-${series.id}`}
                  cx={selectedX}
                  cy={drivingScale.yForValue(series.point.value)}
                  r="5.5"
                  fill={series.color}
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
              );
            })}
            {selectedTeen ? (
              <circle
                cx={selectedX}
                cy={teenScale.yForValue(selectedTeen.lfpr)}
                r="5.5"
                fill="#1F7A8C"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
            ) : null}
            {selectedLicensure ? (
              <circle
                cx={selectedX}
                cy={licensureScale.yForValue(selectedLicensure.share)}
                r="5.5"
                fill="#D4A017"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
            ) : null}
          </g>

          <text x={licensureTopX} y={PLOT_BOTTOM + 56} className="axis-label axis-label-center" fill="#8A6400" fontWeight="700">Gold bars: 18-year-old licensure share</text>
          <text x={teenAxisX} y={PLOT_BOTTOM + 56} className="axis-label axis-label-start" fill="#1F7A8C" fontWeight="700">Teal line: annual teen labor participation</text>
          <text x={PLOT_LEFT} y={900} className="axis-label axis-label-start">
            Source: BLS annual teen LFPR; FHWA DL-220 licensed-driver counts; BLS and EIA data for driving cost indices.
          </text>

          {showTooltip && selectedLicensure && selectedTeen ? (
            <g>
              <rect x={Math.min(selectedX + 18, 1000)} y={PLOT_TOP + 10} width="240" height="146" rx="14" fill="#FFFFFF" stroke="rgba(23, 32, 51, 0.12)" />
              <text x={Math.min(selectedX + 34, 1016)} y={PLOT_TOP + 36} className="axis-label axis-label-start" fill="#101828" fontWeight="700">
                {selectedYear}
              </text>
              <text x={Math.min(selectedX + 34, 1016)} y={PLOT_TOP + 58} className="axis-label axis-label-start" fill="#8A6400" fontWeight="700">
                Licensure {formatNumber(selectedLicensure.share)}%
              </text>
              <text x={Math.min(selectedX + 34, 1016)} y={PLOT_TOP + 80} className="axis-label axis-label-start" fill="#1F7A8C" fontWeight="700">
                Annual teen LFPR {formatNumber(selectedTeen.lfpr)}%
              </text>
              <text x={Math.min(selectedX + 34, 1016)} y={PLOT_TOP + 102} className="axis-label axis-label-start" fill="#C65A6A" fontWeight="700">
                Insurance index {formatNumber(selectedDriving[0]?.point?.value ?? 0)}
              </text>
              <text x={Math.min(selectedX + 34, 1016)} y={PLOT_TOP + 124} className="axis-label axis-label-start" fill="#244A71" fontWeight="700">
                Gasoline index {formatNumber(selectedDriving[1]?.point?.value ?? 0)}
              </text>
            </g>
          ) : null}
        </svg>
      </div>
    </section>
  );
}
