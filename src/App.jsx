import React, { useMemo, useState } from "react";
import { getYouthShareSeries } from "./data/licensedDrivers";

const chartMargin = {
  top: 36,
  right: 28,
  bottom: 48,
  left: 64,
};

const chartWidth = 1120;
const chartHeight = 540;
const innerWidth = chartWidth - chartMargin.left - chartMargin.right;
const innerHeight = chartHeight - chartMargin.top - chartMargin.bottom;

const tickYears = [1963, 1973, 1983, 1993, 2003, 2013, 2024];
const yTicks = [0, 2, 4, 6, 8];

function formatPercent(value) {
  return `${value.toFixed(2)}%`;
}

function formatMillions(value) {
  return `${(value / 1000).toFixed(2)}M`;
}

function scaleX(year, minYear, maxYear) {
  return chartMargin.left + ((year - minYear) / (maxYear - minYear)) * innerWidth;
}

function scaleY(value, maxValue) {
  return chartMargin.top + innerHeight - (value / maxValue) * innerHeight;
}

function buildPath(points) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

function nearestPoint(points, pointerX) {
  let bestPoint = points[0];
  let bestDistance = Math.abs(points[0].x - pointerX);

  for (const point of points) {
    const distance = Math.abs(point.x - pointerX);
    if (distance < bestDistance) {
      bestPoint = point;
      bestDistance = distance;
    }
  }

  return bestPoint;
}

function App() {
  const series = useMemo(() => getYouthShareSeries(), []);
  const firstPoint = series.length > 0 ? series[0] : null;
  const lastPoint = series.length > 0 ? series[series.length - 1] : null;
  const [showYouthShare, setShowYouthShare] = useState(true);
  const [hoveredYear, setHoveredYear] = useState(lastPoint ? lastPoint.year : null);

  if (!firstPoint || !lastPoint) {
    return (
      <main className="page-shell">
        <section className="hero-card">
          <div className="hero-copy">
            <p className="eyebrow">Licensed Drivers</p>
            <h1>Chart unavailable</h1>
            <p className="dek">
              The licensed-driver series did not load. Check the CSV import and refresh the page.
            </p>
          </div>
        </section>
      </main>
    );
  }

  const minYear = firstPoint.year;
  const maxYear = lastPoint.year;
  const maxValue = 8;

  const plottedSeries = useMemo(
    () =>
      series.map((entry) => ({
        ...entry,
        x: scaleX(entry.year, minYear, maxYear),
        y: scaleY(entry.share, maxValue),
      })),
    [maxYear, minYear, series],
  );

  const youthSharePath = useMemo(() => buildPath(plottedSeries), [plottedSeries]);
  const activePoint =
    plottedSeries.find((point) => point.year === hoveredYear) ?? plottedSeries[plottedSeries.length - 1];

  function handlePointerMove(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const pointerX = event.clientX - bounds.left;
    setHoveredYear(nearestPoint(plottedSeries, pointerX).year);
  }

  return (
    <main className="page-shell">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Licensed Drivers</p>
          <h1>The road stopped being teen-heavy</h1>
          <p className="dek">
            Interactive React foundation for the same core series currently shown in
            <code> licensed-drivers-youth-shares.svg</code>: ages 16, 17, and 18 as a share of
            all licensed drivers.
          </p>
        </div>

        <div className="metric-row">
          <article className="metric-card">
            <span className="metric-label">Start</span>
            <strong>{formatPercent(series[0].share)}</strong>
            <span>in {firstPoint.year}</span>
          </article>
          <article className="metric-card">
            <span className="metric-label">Latest</span>
            <strong>{formatPercent(lastPoint.share)}</strong>
            <span>in {lastPoint.year}</span>
          </article>
          <article className="metric-card">
            <span className="metric-label">Teen Drivers</span>
            <strong>{formatMillions(activePoint.youthDrivers)}</strong>
            <span>ages 16-18 in {activePoint.year}</span>
          </article>
        </div>

        <div className="chart-panel">
          <div className="panel-header">
            <div>
              <h2>Youth share of all licensed drivers</h2>
              <p>Toggle layers on and off here as we add them.</p>
            </div>

            <label className="series-toggle">
              <input
                type="checkbox"
                checked={showYouthShare}
                onChange={(event) => setShowYouthShare(event.target.checked)}
              />
              <span className="toggle-swatch" />
              <span>16-18 combined share</span>
            </label>
          </div>

          <div className="chart-frame">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="chart-svg"
              role="img"
              aria-label="Ages 16 to 18 as a share of all licensed drivers from 1963 to 2024"
              onPointerMove={handlePointerMove}
              onPointerLeave={() => setHoveredYear(lastPoint.year)}
            >
              <rect x="0" y="0" width={chartWidth} height={chartHeight} rx="28" className="plot-backdrop" />

              {yTicks.map((tick) => {
                const y = scaleY(tick, maxValue);
                return (
                  <g key={tick}>
                    <line x1={chartMargin.left} x2={chartWidth - chartMargin.right} y1={y} y2={y} className="grid-line" />
                    <text x={chartMargin.left - 14} y={y + 5} className="axis-label axis-label-right">
                      {tick}%
                    </text>
                  </g>
                );
              })}

              {tickYears.map((tick) => {
                const x = scaleX(tick, minYear, maxYear);
                return (
                  <g key={tick}>
                    <line x1={x} x2={x} y1={chartMargin.top} y2={chartHeight - chartMargin.bottom} className="grid-line vertical-grid-line" />
                    <text x={x} y={chartHeight - 16} className="axis-label axis-label-center">
                      {tick}
                    </text>
                  </g>
                );
              })}

              <rect
                x={chartMargin.left}
                y={scaleY(4.7, maxValue)}
                width={innerWidth}
                height={scaleY(2.6, maxValue) - scaleY(4.7, maxValue)}
                rx="18"
                className="focus-band"
              />

              {showYouthShare && (
                <path d={youthSharePath} className="series-line youth-share-line" pathLength="1" />
              )}

              {showYouthShare &&
                plottedSeries.map((point) => (
                  <circle
                    key={point.year}
                    cx={point.x}
                    cy={point.y}
                    r={point.year === activePoint.year ? 5.5 : 3}
                    className={point.year === activePoint.year ? "series-dot active-dot" : "series-dot"}
                  />
                ))}

              {showYouthShare && activePoint && (
                <g>
                  <line
                    x1={activePoint.x}
                    x2={activePoint.x}
                    y1={chartMargin.top}
                    y2={chartHeight - chartMargin.bottom}
                    className="hover-line"
                  />
                  <g transform={`translate(${Math.min(activePoint.x + 16, chartWidth - 196)}, ${Math.max(activePoint.y - 88, 24)})`}>
                    <rect width="180" height="72" rx="16" className="tooltip-card" />
                    <text x="16" y="24" className="tooltip-year">
                      {activePoint.year}
                    </text>
                    <text x="16" y="46" className="tooltip-value">
                      {formatPercent(activePoint.share)}
                    </text>
                    <text x="16" y="62" className="tooltip-note">
                      {formatMillions(activePoint.youthDrivers)} drivers ages 16-18
                    </text>
                  </g>
                </g>
              )}
            </svg>
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;
