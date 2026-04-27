import React, { useMemo, useState } from "react";
import {
  getCpiInsuranceSeries,
  getGasolineShockSeries,
  getJulyYouthSeries,
  getTeenAnnualSeries,
  getYouthShareSeries,
} from "./data/licensedDrivers";

const BASE_YEAR = 1963;
const DISPLAY_END_YEAR = 2024;
const SVG_WIDTH = 1200;
const SVG_HEIGHT = 760;
const CHART_LEFT = 92;
const CHART_RIGHT = 1118;
const CHART_TOP = 132;
const CHART_BOTTOM = 602;
const YEAR_GRID = [1963, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024];
const INDEX_TICKS = [50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2500, 4000];

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
      rawValue: row[valueKey],
      indexValue: (row[valueKey] / baseRow[valueKey]) * 100,
    }));
}

function buildLinePath(points, xForYear, yForValue) {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xForYear(point.year).toFixed(1)} ${yForValue(point.value).toFixed(1)}`)
    .join(" ");
}

function joinNumbers(values) {
  return values.map((value) => numberFormatter.format(value)).join(" ");
}

export default function App() {
  const [showAll, setShowAll] = useState(true);
  const [visible, setVisible] = useState({
    insurance: true,
    gasoline: true,
    licensure: true,
    schoolYear: true,
    summer: true,
  });
  const [hoverYear, setHoverYear] = useState(null);

  const series = useMemo(() => {
    const youthShare = indexSeries(
      getYouthShareSeries().map((row) => ({ year: row.year, value: row.share })),
      "value",
    ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR);
    const teenAnnual = indexSeries(
      getTeenAnnualSeries().map((row) => ({ year: row.year, value: row.lfpr })),
      "value",
    ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR);
    const julyYouth = indexSeries(
      getJulyYouthSeries().map((row) => ({ year: row.year, value: row.lfpr })),
      "value",
    ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR);
    const insurance = indexSeries(
      getCpiInsuranceSeries().map((row) => ({ year: row.year, value: row.insurance })),
      "value",
    ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR);
    const gasoline = indexSeries(
      getGasolineShockSeries().map((row) => ({ year: row.year, value: row.gasoline })),
      "value",
    ).filter((row) => row.year >= BASE_YEAR && row.year <= DISPLAY_END_YEAR);

    return [
      {
        id: "insurance",
        group: "Driving costs",
        label: "Motor vehicle insurance",
        color: "#C65A6A",
        points: insurance,
      },
      {
        id: "gasoline",
        group: "Driving costs",
        label: "Gasoline price",
        color: "#244A71",
        points: gasoline,
      },
      {
        id: "licensure",
        group: "Teen autonomy",
        label: "18-year-old licensure share",
        color: "#8A6400",
        points: youthShare,
      },
      {
        id: "schoolYear",
        group: "Teen autonomy",
        label: "School-year work",
        color: "#1F7A8C",
        points: teenAnnual,
      },
      {
        id: "summer",
        group: "Teen autonomy",
        label: "Summer work",
        color: "#6C4AB6",
        points: julyYouth,
      },
    ];
  }, []);

  const years = useMemo(() => {
    const yearSet = new Set();
    for (const item of series) {
      for (const point of item.points) {
        yearSet.add(point.year);
      }
    }
    return [...yearSet].sort((left, right) => left - right);
  }, [series]);

  const commonYears = useMemo(() => {
    return years.filter((year) => series.every((item) => item.points.some((point) => point.year === year)));
  }, [series, years]);

  const yearMapBySeries = useMemo(() => {
    const map = new Map();
    for (const item of series) {
      map.set(item.id, new Map(item.points.map((point) => [point.year, point])));
    }
    return map;
  }, [series]);

  const visibleSeries = series.filter((item) => visible[item.id]);
  const selectedYear = hoverYear ?? commonYears[commonYears.length - 1] ?? years[years.length - 1];

  const allVisible = showAll && Object.values(visible).every(Boolean);
  const visibleValues = visibleSeries.flatMap((item) =>
    item.points
      .filter((point) => point.year === selectedYear)
      .map((point) => point.indexValue),
  );
  const yMin = 50;
  const yMax = Math.max(120, ...(visibleValues.length ? visibleValues : [0]), ...visibleSeries.flatMap((item) => item.points.map((point) => point.indexValue))) * 1.08;
  const logMin = Math.log10(yMin);
  const logMax = Math.log10(yMax);

  const xForYear = (year) => {
    const span = years[years.length - 1] - years[0];
    return CHART_LEFT + ((year - years[0]) / span) * (CHART_RIGHT - CHART_LEFT);
  };

  const yForValue = (value) => {
    const bounded = Math.max(value, yMin);
    return CHART_BOTTOM - ((Math.log10(bounded) - logMin) / (logMax - logMin)) * (CHART_BOTTOM - CHART_TOP);
  };

  const chartYearX = xForYear(selectedYear);

  const setSeries = (id, nextValue) => {
    setVisible((current) => {
      const next = { ...current, [id]: nextValue };
      const allChecked = Object.values(next).every(Boolean);
      setShowAll(allChecked);
      return next;
    });
  };

  const toggleAll = (nextValue) => {
    setShowAll(nextValue);
    setVisible({
      insurance: nextValue,
      gasoline: nextValue,
      licensure: nextValue,
      schoolYear: nextValue,
      summer: nextValue,
    });
  };

  const handleHover = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * SVG_WIDTH;
    const clampedX = Math.max(CHART_LEFT, Math.min(CHART_RIGHT, x));
    const span = years[years.length - 1] - years[0];
    const year = Math.round(years[0] + ((clampedX - CHART_LEFT) / (CHART_RIGHT - CHART_LEFT)) * span);
    setHoverYear(Math.max(years[0], Math.min(years[years.length - 1], year)));
  };

  const selectedYearRows = visibleSeries
    .map((item) => {
      const point = yearMapBySeries.get(item.id)?.get(selectedYear);
      return point
        ? { ...item, point }
        : null;
    })
    .filter(Boolean);

  const selectedYearLabel =
    selectedYear === commonYears[commonYears.length - 1]
      ? `${selectedYear} latest common year`
      : `year ${selectedYear}`;

  return (
    <div className="page-shell">
      <main className="hero-card">
        <p className="eyebrow">Maturity coup data package</p>
        <h1>One chart for driving costs and teen autonomy</h1>
        <p className="dek">
          All five lines are indexed to <strong>1963 = 100</strong> so gasoline, insurance, licensure, and youth work can live on
          one axis. The gasoline line is the spliced 1963-2024 series, with leaded regular through 1990 and regular gasoline after
          that.
        </p>

        <section className="control-card" aria-label="Series controls">
          <div className="control-card-header">
            <div>
              <h2>Series controls</h2>
              <p>Check the parent box to show everything, or hide individual series below.</p>
            </div>
            <label className="series-row series-row-parent">
              <input
                type="checkbox"
                checked={allVisible}
                onChange={(event) => toggleAll(event.target.checked)}
              />
              <span className="swatch swatch-parent" aria-hidden="true" />
              <span>Show all lines</span>
            </label>
          </div>

          <div className="toggle-groups">
            <div className="toggle-group">
              <p className="toggle-group-title">Driving costs</p>
              <label className="series-row">
                <input
                  type="checkbox"
                  checked={visible.insurance}
                  onChange={(event) => setSeries("insurance", event.target.checked)}
                />
                <span className="swatch swatch-insurance" aria-hidden="true" />
                <span>Motor vehicle insurance</span>
              </label>
              <label className="series-row">
                <input
                  type="checkbox"
                  checked={visible.gasoline}
                  onChange={(event) => setSeries("gasoline", event.target.checked)}
                />
                <span className="swatch swatch-gasoline" aria-hidden="true" />
                <span>Gasoline price</span>
              </label>
            </div>

            <div className="toggle-group">
              <p className="toggle-group-title">Teen autonomy</p>
              <label className="series-row">
                <input
                  type="checkbox"
                  checked={visible.licensure}
                  onChange={(event) => setSeries("licensure", event.target.checked)}
                />
                <span className="swatch swatch-licensure" aria-hidden="true" />
                <span>18-year-old licensure share</span>
              </label>
              <label className="series-row">
                <input
                  type="checkbox"
                  checked={visible.schoolYear}
                  onChange={(event) => setSeries("schoolYear", event.target.checked)}
                />
                <span className="swatch swatch-school" aria-hidden="true" />
                <span>School-year work</span>
              </label>
              <label className="series-row">
                <input
                  type="checkbox"
                  checked={visible.summer}
                  onChange={(event) => setSeries("summer", event.target.checked)}
                />
                <span className="swatch swatch-summer" aria-hidden="true" />
                <span>Summer work</span>
              </label>
            </div>
          </div>
        </section>

        <section className="chart-card">
          <div className="chart-head">
            <div>
              <h2>Indexed together on one axis</h2>
              <p>
                Hover the line chart to read the selected year. The 1970s gasoline shock, insurance inflation, and teen labor shifts
                now sit in the same frame.
              </p>
            </div>
            <div className="chart-badge">1963 = 100</div>
          </div>

          <div className="chart-frame" onPointerMove={handleHover} onPointerLeave={() => setHoverYear(null)}>
            <svg
              className="chart-svg"
              viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
              role="img"
              aria-label="Indexed chart of gasoline, insurance, teen licensure, school-year work, and summer work."
            >
              <defs>
                <clipPath id="plotClip">
                  <rect x={CHART_LEFT} y={CHART_TOP} width={CHART_RIGHT - CHART_LEFT} height={CHART_BOTTOM - CHART_TOP} />
                </clipPath>
              </defs>

              <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} rx="24" fill="#FFFDF8" />
              <text x="92" y="58" className="svg-kicker">
                One history, one scale
              </text>
              <text x="92" y="86" className="svg-title">
                Driving costs and teen autonomy move together only when you force them onto the same base year.
              </text>

              {INDEX_TICKS.filter((tick) => tick >= yMin && tick <= yMax).map((tick) => {
                const y = yForValue(tick);
                return (
                  <g key={tick}>
                    <line x1={CHART_LEFT} x2={CHART_RIGHT} y1={y} y2={y} className="grid-line" />
                    <text x={CHART_LEFT - 14} y={y + 4} className="axis-label axis-label-right">
                      {tick}
                    </text>
                  </g>
                );
              })}

              {YEAR_GRID.filter((year) => year >= years[0] && year <= years[years.length - 1]).map((year) => {
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

              <rect x={CHART_LEFT} y={CHART_TOP} width={CHART_RIGHT - CHART_LEFT} height={CHART_BOTTOM - CHART_TOP} className="plot-backdrop" />

              <g clipPath="url(#plotClip)">
                <rect x={CHART_LEFT} y={CHART_TOP} width={CHART_RIGHT - CHART_LEFT} height={CHART_BOTTOM - CHART_TOP} className="focus-band" opacity="0.06" />

                {visibleSeries.map((item) => {
                  const points = item.points.map((point) => ({
                    year: point.year,
                    value: point.indexValue,
                  }));
                  return (
                    <g key={item.id}>
                      <path
                        d={buildLinePath(points, xForYear, yForValue)}
                        className={`series-line ${item.id}-line`}
                        stroke={item.color}
                        strokeWidth={item.id === "insurance" ? 4.5 : 3.8}
                      />
                    </g>
                  );
                })}

                {selectedYearRows.map((item) => {
                  const y = yForValue(item.point.indexValue);
                  return (
                    <circle
                      key={item.id}
                      cx={chartYearX}
                      cy={y}
                      r="5.5"
                      fill={item.color}
                      stroke="#FFFFFF"
                      strokeWidth="2"
                    />
                  );
                })}
              </g>

              {visibleSeries.length > 0 && (
                <g>
                  <line x1={chartYearX} x2={chartYearX} y1={CHART_TOP} y2={CHART_BOTTOM} className="hover-line" />
                  <text x={chartYearX + 8} y={CHART_TOP + 18} className="hover-year-label">
                    {selectedYear}
                  </text>
                </g>
              )}
            </svg>
          </div>

          <div className="chart-summary">
            <div className="chart-summary-year">
              <span className="summary-label">Selected</span>
              <strong>{selectedYearLabel}</strong>
            </div>
            <div className="summary-grid">
              {selectedYearRows.map((item) => (
                <div key={item.id} className="summary-pill">
                  <span className="summary-swatch" style={{ background: item.color }} aria-hidden="true" />
                  <div>
                    <span className="summary-name">{item.label}</span>
                    <strong>{numberFormatter.format(item.point.indexValue)}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-foot">
            <span>All lines indexed to 1963 = 100</span>
            <span>Gasoline is spliced across the leaded-to-regular transition</span>
            <span>Hover to move the year readout</span>
          </div>
        </section>
      </main>
    </div>
  );
}
