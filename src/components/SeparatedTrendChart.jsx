import React, { useMemo, useState } from "react";
import {
  getCpiInsuranceSeries,
  getGasolineShockSeries,
  getJulyYouthSeries,
  getTeenAnnualSeries,
  getYouthShareSeries,
} from "../data/licensedDrivers";

const BASE_YEAR = 1963;
const DISPLAY_END_YEAR = 2024;
const SVG_WIDTH = 1200;
const SVG_HEIGHT = 860;
const CHART_LEFT = 92;
const CHART_RIGHT = 1118;
const CHART_TOP = 150;
const CHART_BOTTOM = 760;
const YEAR_GRID = [1963, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024];
const LOG_TICKS = [50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2500, 4000];

const numberFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1,
});

function indexSeries(rows, valueKey) {
  const baseRow = rows.find((row) => row.year === BASE_YEAR) ?? rows[0];

  if (!baseRow || !Number.isFinite(baseRow[valueKey]) || baseRow[valueKey] === 0) {
    throw new Error(`Missing or invalid base year data for ${valueKey}`);
  }

  return rows
    .filter((row) => Number.isFinite(row.year) && Number.isFinite(row[valueKey]))
    .map((row) => ({
      year: row.year,
      value: (row[valueKey] / baseRow[valueKey]) * 100,
    }));
}

function buildLinePath(points, xForYear, yForValue) {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xForYear(point.year).toFixed(1)} ${yForValue(point.value).toFixed(1)}`)
    .join(" ");
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

function buildLinearScale(values, plotTop, plotBottom, { tickCount = 5, min = null, paddingRatio = 0.12 } = {}) {
  const finiteValues = values.filter((value) => Number.isFinite(value));
  const minValue = min ?? Math.min(...finiteValues);
  const maxValue = Math.max(...finiteValues);
  const span = Math.max(maxValue - minValue, 1);
  const paddedMin = min == null ? minValue - span * paddingRatio : min;
  const paddedMax = maxValue + span * paddingRatio;
  const step = niceStep((paddedMax - paddedMin) / Math.max(1, tickCount - 1));
  const domainMin = min == null ? Math.floor(paddedMin / step) * step : min;
  const domainMax = Math.ceil(paddedMax / step) * step;
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
  const ticks = LOG_TICKS.filter((tick) => tick >= domainMin && tick <= domainMax);
  const logMin = Math.log10(domainMin);
  const logMax = Math.log10(domainMax);

  return {
    domainMin,
    domainMax,
    ticks,
    yForValue: (value) => {
      const bounded = Math.max(value, domainMin);
      return plotBottom - ((Math.log10(bounded) - logMin) / (logMax - logMin)) * (plotBottom - plotTop);
    },
  };
}

function formatNumber(value) {
  return numberFormatter.format(value);
}

export default function SeparatedTrendChart() {
  const [hoverYear, setHoverYear] = useState(2024);

  const data = useMemo(() => {
    const driving = [
      {
        id: "insurance",
        label: "Motor vehicle insurance",
        color: "#C65A6A",
        points: indexSeries(
          getCpiInsuranceSeries().map((row) => ({ year: row.year, insurance: row.insurance })),
          "insurance",
        ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR),
      },
      {
        id: "gasoline",
        label: "Gasoline price",
        color: "#244A71",
        points: indexSeries(
          getGasolineShockSeries().map((row) => ({ year: row.year, gasoline: row.gasoline })),
          "gasoline",
        ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR),
      },
    ];

    const percent = [
      {
        id: "licensure",
        label: "18-year-old licensure share",
        color: "#8A6400",
        points: getYouthShareSeries()
          .filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR)
          .map((row) => ({
            year: row.year,
            value: row.share,
          })),
      },
      {
        id: "schoolYear",
        label: "School-year work",
        color: "#1F7A8C",
        points: getTeenAnnualSeries()
          .filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR)
          .map((row) => ({
            year: row.year,
            value: row.lfpr,
          })),
      },
      {
        id: "summer",
        label: "Summer work",
        color: "#6C4AB6",
        points: getJulyYouthSeries()
          .filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR)
          .map((row) => ({
            year: row.year,
            value: row.lfpr,
          })),
      },
    ];

    return { driving, percent };
  }, []);

  const allYears = useMemo(() => {
    const yearSet = new Set();
    for (const group of Object.values(data)) {
      for (const item of group) {
        for (const point of item.points) {
          yearSet.add(point.year);
        }
      }
    }
    return [...yearSet].sort((left, right) => left - right);
  }, [data]);

  const selectedYear = hoverYear ?? allYears[allYears.length - 1] ?? DISPLAY_END_YEAR;

  const xForYear = (year) => {
    const span = allYears[allYears.length - 1] - allYears[0];
    return CHART_LEFT + ((year - allYears[0]) / span) * (CHART_RIGHT - CHART_LEFT);
  };

  const drivingScale = useMemo(() => {
    const values = data.driving.flatMap((item) => item.points.map((point) => point.value));
    return buildLogScale(values, CHART_TOP, CHART_BOTTOM);
  }, [data.driving]);

  const percentScale = useMemo(() => {
    const values = data.percent.flatMap((item) => item.points.map((point) => point.value));
    return buildLinearScale(values, CHART_TOP, CHART_BOTTOM, {
      tickCount: 6,
      min: 0,
      paddingRatio: 0,
    });
  }, [data.percent]);

  const selectedValues = useMemo(() => {
    const valueForYear = (item) => item.points.find((point) => point.year === selectedYear)?.value;

    return [
      ...data.driving.map((item) => ({ ...item, value: valueForYear(item), unit: "" })),
      ...data.percent.map((item) => ({ ...item, value: valueForYear(item), unit: "%" })),
    ].filter((item) => Number.isFinite(item.value));
  }, [data, selectedYear]);

  const handleHover = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * SVG_WIDTH;
    const clampedX = Math.max(CHART_LEFT, Math.min(CHART_RIGHT, x));
    const span = allYears[allYears.length - 1] - allYears[0];
    const year = Math.round(allYears[0] + ((clampedX - CHART_LEFT) / (CHART_RIGHT - CHART_LEFT)) * span);
    setHoverYear(Math.max(allYears[0], Math.min(allYears[allYears.length - 1], year)));
  };

  const yearGridYears = YEAR_GRID.filter((year) => year >= allYears[0] && year <= allYears[allYears.length - 1]);
  const chartYearX = xForYear(selectedYear);

  return (
    <section className="chart-card chart-card-onechart">
      <div className="chart-head chart-head-stack">
        <div>
          <h2>One chart, two y-axes</h2>
          <p>
            The cost lines stay indexed on the left, while licensure and teen work share the same percent axis on the right. That
            keeps all five series in one frame and stops the teen lines from getting flattened.
          </p>
        </div>
        <div className="chart-badge">Hover a year</div>
      </div>

      <div className="chart-frame chart-frame-onechart" onPointerMove={handleHover} onPointerLeave={() => setHoverYear(null)}>
        <svg
          className="chart-svg chart-svg-onechart"
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          role="img"
          aria-label="One chart with indexed driving costs on the left axis and percent-based teen measures on the right axis."
        >
          <defs>
            <clipPath id="plotClip">
              <rect x={CHART_LEFT} y={CHART_TOP} width={CHART_RIGHT - CHART_LEFT} height={CHART_BOTTOM - CHART_TOP} />
            </clipPath>
          </defs>

          <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} rx="24" fill="#FFFDF8" />
          <text x={CHART_LEFT} y="58" className="svg-kicker">
            One history, two scales
          </text>
          <text x={CHART_LEFT} y="86" className="svg-title">
            Driving costs, licensure, and teen work now sit in the same chart.
          </text>
          <text x={CHART_LEFT} y="114" className="svg-subtitle">
            Costs are indexed to 1963 = 100 on the left. Licensure, school-year work, and summer work share the percent axis on the
            right.
          </text>

          <rect x={CHART_LEFT} y={CHART_TOP} width={CHART_RIGHT - CHART_LEFT} height={CHART_BOTTOM - CHART_TOP} className="plot-backdrop" />

          {drivingScale.ticks.map((tick) => {
            const y = drivingScale.yForValue(tick);
            return (
              <g key={`drive-${tick}`}>
                <line x1={CHART_LEFT} x2={CHART_LEFT + 10} y1={y} y2={y} className="axis-tick" />
                <text x={CHART_LEFT - 14} y={y + 4} className="axis-label axis-label-right">
                  {formatNumber(tick)}
                </text>
              </g>
            );
          })}

          {percentScale.ticks.map((tick) => {
            const y = percentScale.yForValue(tick);
            return (
              <g key={`percent-${tick}`}>
                <line x1={CHART_LEFT} x2={CHART_RIGHT} y1={y} y2={y} className="grid-line" />
                <text x={CHART_RIGHT + 12} y={y + 4} className="axis-label axis-label-start">
                  {formatNumber(tick)}%
                </text>
              </g>
            );
          })}

          {yearGridYears.map((year) => {
            const x = xForYear(year);
            return (
              <g key={year}>
                <line x1={x} x2={x} y1={CHART_TOP} y2={CHART_BOTTOM} className="vertical-grid-line" />
                <text x={x} y={CHART_BOTTOM + 26} className="axis-label axis-label-center">
                  {year}
                </text>
              </g>
            );
          })}

          <g clipPath="url(#plotClip)">
            {data.driving.map((item) => {
              const points = item.points.map((point) => ({
                year: point.year,
                value: point.value,
              }));
              return (
                <path
                  key={item.id}
                  d={buildLinePath(points, xForYear, drivingScale.yForValue)}
                  className={`series-line ${item.id}-line`}
                  stroke={item.color}
                  strokeWidth={item.id === "insurance" ? 4.5 : 3.8}
                />
              );
            })}

            {data.percent.map((item) => {
              const points = item.points.map((point) => ({
                year: point.year,
                value: point.value,
              }));
              return (
                <path
                  key={item.id}
                  d={buildLinePath(points, xForYear, percentScale.yForValue)}
                  className={`series-line ${item.id}-line`}
                  stroke={item.color}
                  strokeWidth={item.id === "licensure" ? 4.2 : 3.5}
                />
              );
            })}

            {[
              ...data.driving,
              ...data.percent,
            ].map((item) => {
              const point = item.points.find((entry) => entry.year === selectedYear);
              if (!point) {
                return null;
              }

              const y = item.id === "insurance" || item.id === "gasoline"
                ? drivingScale.yForValue(point.value)
                : percentScale.yForValue(point.value);

              return (
                <circle
                  key={item.id}
                  cx={chartYearX}
                  cy={y}
                  r="5"
                  fill={item.color}
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
              );
            })}
          </g>

          <line x1={chartYearX} x2={chartYearX} y1={CHART_TOP} y2={CHART_BOTTOM} className="hover-line" />
          <text x={chartYearX + 8} y={CHART_TOP + 18} className="hover-year-label">
            {selectedYear}
          </text>
        </svg>
      </div>

      <div className="chart-summary chart-summary-global">
        <span className="summary-label">Selected year</span>
        <div className="summary-grid">
          {selectedValues.map((item) => (
            <div key={item.id} className="summary-pill">
              <span className="summary-swatch" style={{ background: item.color }} aria-hidden="true" />
              <div>
                <span className="summary-name">{item.label}</span>
                <strong>
                  {formatNumber(item.value)}
                  {item.unit}
                </strong>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
