import React, { useMemo, useState } from "react";
import {
  getCpiInsuranceSeries,
  getGasolineShockSeries,
  getTeenAnnualSeries,
  getYouthShareSeries,
} from "../data/licensedDrivers";

const BASE_YEAR = 1963;
const END_YEAR = 2024;
const SVG_WIDTH = 1540;
const SVG_HEIGHT = 760;
const PLOT_LEFT = 100;
const PLOT_RIGHT = 1080;
const PLOT_TOP = 180;
const PLOT_BOTTOM = 620;
const YEAR_GRID = [1963, 1970, 1980, 1990, 2000, 2010, 2020, 2024];
const LICENSURE_AXIS_X = 1190;
const TEEN_AXIS_X = 1400;
const NUMBER_FORMATTER = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

function formatNumber(value) {
  return NUMBER_FORMATTER.format(value);
}

function formatSignedPercent(value) {
  const prefix = value >= 0 ? "+" : "−";
  return `${prefix}${formatNumber(Math.abs(value))}%`;
}

function percentChange(start, end) {
  return ((end - start) / start) * 100;
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
  const ticks = [80, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 4000].filter(
    (tick) => tick >= domainMin && tick <= domainMax,
  );

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

function buildYouthShareSeries() {
  return getYouthShareSeries().filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR);
}

function buildDrivingSeries() {
  const driving = [
    {
      id: "insurance",
      label: "Motor vehicle insurance",
      color: "#C65A6A",
      points: getCpiInsuranceSeries()
        .map((row) => ({ year: row.year, value: row.insurance }))
        .filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR),
    },
    {
      id: "gasoline",
      label: "Gasoline price",
      color: "#244A71",
      points: getGasolineShockSeries()
        .map((row) => ({ year: row.year, value: row.gasoline }))
        .filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR),
    },
  ];

  const licensure = buildYouthShareSeries();

  return { driving, licensure };
}

function buildTeenLaborSeries() {
  return {
    teenLabor: getTeenAnnualSeries().filter((row) => row.year >= BASE_YEAR && row.year <= END_YEAR),
    licensure: buildYouthShareSeries(),
  };
}

function PanelFrame({ kicker, title, subtitle, badge, children }) {
  return (
    <section className="panel-chart">
      <div className="panel-chart-header">
        <div>
          <p className="panel-chart-kicker">{kicker}</p>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        <div className="chart-badge">{badge}</div>
      </div>
      {children}
    </section>
  );
}

function DrivingCostsChart() {
  const [hoverYear, setHoverYear] = useState(2024);
  const { driving, licensure } = useMemo(buildDrivingSeries, []);
  const licensure1980 = licensure.find((row) => row.year === 1980);
  const licensure2024 = licensure.find((row) => row.year === 2024);
  const driving1980 = {
    insurance: driving[0].points.find((point) => point.year === 1980),
    gasoline: driving[1].points.find((point) => point.year === 1980),
  };
  const driving2024 = {
    insurance: driving[0].points.find((point) => point.year === 2024),
    gasoline: driving[1].points.find((point) => point.year === 2024),
  };

  const allYears = useMemo(
    () =>
      [...new Set([...driving.flatMap((series) => series.points.map((point) => point.year)), ...licensure.map((row) => row.year)])].sort(
        (a, b) => a - b,
      ),
    [driving, licensure],
  );

  const xForYear = useMemo(() => {
    const span = allYears[allYears.length - 1] - allYears[0];
    return (year) => PLOT_LEFT + ((year - allYears[0]) / span) * (PLOT_RIGHT - PLOT_LEFT);
  }, [allYears]);

  const drivingScale = useMemo(
    () => buildLogScale(driving.flatMap((series) => series.points.map((point) => point.value)), PLOT_TOP, PLOT_BOTTOM),
    [driving],
  );
  const licensureScale = useMemo(
    () => buildLinearScale(licensure.map((row) => row.share), PLOT_TOP, PLOT_BOTTOM, { min: 0, max: 8, tickCount: 5, paddingRatio: 0 }),
    [licensure],
  );

  const selectedYear = hoverYear ?? allYears[allYears.length - 1];
  const selectedX = xForYear(selectedYear);
  const yearGridYears = YEAR_GRID.filter((year) => year >= allYears[0] && year <= allYears[allYears.length - 1]);

  const selectedDriving = driving.map((series) => ({
    ...series,
    point: series.points.find((point) => point.year === selectedYear),
  }));
  const selectedLicensure = licensure.find((row) => row.year === selectedYear);

  const eventMarkers = useMemo(
    () => [
      { type: "line", year: 1973, label: "1973-74 oil embargo", labelX: -10, y: PLOT_TOP + 36 },
      { type: "line", year: 1979, label: "1979-80 oil shock", labelX: 12, y: PLOT_TOP + 74 },
      { type: "span", start: 1996, end: 2006, label: "1996-2006 GDL laws spread", y: PLOT_TOP + 36 },
    ].map((event) => {
      if (event.type === "span") {
        const x1 = xForYear(event.start);
        const x2 = xForYear(event.end);
        return { ...event, x1, x2, labelX: (x1 + x2) / 2 };
      }

      return { ...event, x: xForYear(event.year) };
    }),
    [xForYear],
  );

  const handleHover = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * SVG_WIDTH;
    const clamped = Math.max(PLOT_LEFT, Math.min(PLOT_RIGHT, x));
    const span = allYears[allYears.length - 1] - allYears[0];
    const rawYear = allYears[0] + ((clamped - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT)) * span;
    const nearest = allYears.reduce(
      (best, candidate) => (Math.abs(candidate - rawYear) < Math.abs(best - rawYear) ? candidate : best),
      allYears[0],
    );
    setHoverYear(nearest);
  };

  const drivingPaths = driving.map((series) => ({
    ...series,
    d: buildLinePath(series.points, xForYear, drivingScale.yForValue),
  }));

  const peak1974 = licensure.find((row) => row.year === 1974);
  const peak1974X = xForYear(1974);
  const peak1974Y = peak1974 ? licensureScale.yForValue(peak1974.share) : null;

  return (
    <PanelFrame
      kicker="Driving costs vs. teen licensure"
      title="Insurance rose steadily while teen licensure fell."
      subtitle="Gasoline and insurance are indexed on the left. Teen licensure is shown separately on the right."
      badge="Costs + licensure"
    >
      <div className="panel-chart-frame" onPointerMove={handleHover} onPointerLeave={() => setHoverYear(null)}>
        <svg
          className="panel-chart-svg"
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          role="img"
          aria-label="Driving costs and teen licensure chart."
          style={{ cursor: "crosshair" }}
        >
          <defs>
            <clipPath id="clip-driving">
              <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={PLOT_BOTTOM - PLOT_TOP} />
            </clipPath>
          </defs>
          <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} rx="24" fill="#FFFDF8" />

          <text x={PLOT_LEFT} y="56" className="svg-kicker">
            Main panel
          </text>
          <text x={PLOT_LEFT} y="86" className="svg-title">
            Driving costs and teen licensure, 1963 to 2024
          </text>
          <text x={PLOT_LEFT} y="112" className="svg-subtitle">
            Insurance and gasoline are indexed on the left. The gold bars show 16-18 licensed drivers as a share of all licensed
            drivers on the right.
          </text>

          <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={PLOT_BOTTOM - PLOT_TOP} className="plot-backdrop" />

          {eventMarkers.map((event) =>
            event.type === "span" ? (
              <g key={event.label} pointerEvents="none">
                <rect x={event.x1} y={PLOT_TOP} width={event.x2 - event.x1} height={PLOT_BOTTOM - PLOT_TOP} fill="rgba(36,74,113,0.055)" />
                <line x1={event.x1} x2={event.x1} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(36,74,113,0.18)" strokeWidth="1" strokeDasharray="4 5" />
                <line x1={event.x2} x2={event.x2} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(36,74,113,0.18)" strokeWidth="1" strokeDasharray="4 5" />
                <text x={event.labelX} y={event.y} className="axis-label axis-label-center" fill="#475467" fontWeight="700" fontSize="10">
                  {event.label}
                </text>
              </g>
            ) : (
              <g key={event.label} pointerEvents="none">
                <line x1={event.x} x2={event.x} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(101,85,28,0.36)" strokeWidth="1.2" strokeDasharray="4 4" />
                <text x={event.x + event.labelX} y={event.y} className={`axis-label axis-label-${event.labelX < 0 ? "right" : "start"}`} fill="#5F4B00" fontWeight="700" fontSize="10">
                  {event.label}
                </text>
              </g>
            ),
          )}

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
          <text x={PLOT_LEFT - 10} y={PLOT_TOP - 16} className="axis-label axis-label-right" fill="#667085" fontWeight="700">
            Index
          </text>
          <text x={PLOT_LEFT - 10} y={PLOT_TOP - 4} className="axis-label axis-label-right" fill="#667085">
            1963=100
          </text>

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
          <line x1={LICENSURE_AXIS_X} x2={LICENSURE_AXIS_X} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="#D4A017" strokeWidth="1.5" strokeDasharray="6 4" />
          <text x={LICENSURE_AXIS_X} y={PLOT_TOP - 18} className="axis-label axis-label-center" fill="#8A6400" fontWeight="700">
            16-18 driver share
          </text>

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

          <g clipPath={`url(#clip-driving)`}>
            {licensure.map((row) => {
              const x = xForYear(row.year);
              const barTop = licensureScale.yForValue(row.share);
              const barBase = licensureScale.yForValue(0);
              const barH = Math.max(0, barBase - barTop);
              const isSelected = row.year === selectedYear;

              return (
                <rect
                  key={`lic-${row.year}`}
                  x={x - (isSelected ? 10 : 7) / 2}
                  y={barTop}
                  width={isSelected ? 10 : 7}
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

            {drivingPaths.map((series) => (
              <path
                key={series.id}
                d={series.d}
                fill="none"
                stroke={series.color}
                strokeWidth={series.id === "insurance" ? 4 : 3.2}
                strokeLinecap="round"
                strokeLinejoin="round"
                pointerEvents="none"
              />
            ))}

            {selectedDriving.map((series) =>
              series.point ? (
                <circle
                  key={`dot-${series.id}`}
                  cx={selectedX}
                  cy={drivingScale.yForValue(series.point.value)}
                  r="5"
                  fill={series.color}
                  stroke="#FFFDF8"
                  strokeWidth="2"
                  pointerEvents="none"
                />
              ) : null,
            )}

            {selectedLicensure && (
              <circle cx={selectedX} cy={licensureScale.yForValue(selectedLicensure.share)} r="5" fill="#C89200" stroke="#FFFDF8" strokeWidth="2" pointerEvents="none" />
            )}

            <line x1={selectedX} x2={selectedX} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(23,32,51,0.2)" strokeWidth="1.5" strokeDasharray="5 5" pointerEvents="none" />

            {peak1974Y !== null && (
              <g pointerEvents="none">
                <line x1={peak1974X} x2={peak1974X} y1={peak1974Y - 28} y2={peak1974Y - 7} stroke="#A07800" strokeWidth="1.2" strokeDasharray="3 2" />
                <text x={peak1974X} y={peak1974Y - 34} className="axis-label axis-label-center" fill="#8A6400" fontWeight="700" fontSize="10">
                  All-time peak 1974
                </text>
              </g>
            )}
          </g>

          <text x={selectedX + 8} y={PLOT_TOP + 20} className="hover-year-label">
            {selectedYear}
          </text>
        </svg>
      </div>

      <div className="chart-summary chart-summary-global">
        <span className="summary-label">Driving summary</span>
        <div className="summary-grid">
          <div className="summary-pill">
            <span className="summary-swatch" style={{ background: "#C65A6A" }} aria-hidden="true" />
            <div>
              <span className="summary-name">Insurance, 1980 to 2024</span>
              <strong>{formatSignedPercent(percentChange(driving1980.insurance.value, driving2024.insurance.value))}</strong>
            </div>
          </div>
          <div className="summary-pill">
            <span className="summary-swatch" style={{ background: "#244A71" }} aria-hidden="true" />
            <div>
              <span className="summary-name">Gasoline, 1980 to 2024</span>
              <strong>{formatSignedPercent(percentChange(driving1980.gasoline.value, driving2024.gasoline.value))}</strong>
            </div>
          </div>
          <div className="summary-pill">
            <span className="summary-swatch" style={{ background: "#8A6400" }} aria-hidden="true" />
            <div>
              <span className="summary-name">Teen licensure, 1980 to 2024</span>
              <strong>{formatSignedPercent(percentChange(licensure1980.share, licensure2024.share))}</strong>
            </div>
          </div>
        </div>
      </div>
    </PanelFrame>
  );
}

function TeenWorkChart() {
  const [hoverYear, setHoverYear] = useState(2024);
  const { teenLabor, licensure } = useMemo(buildTeenLaborSeries, []);
  const teen1979 = teenLabor.find((row) => row.year === 1979);
  const teen2024 = teenLabor.find((row) => row.year === 2024);
  const licensure1980 = licensure.find((row) => row.year === 1980);
  const licensure2024 = licensure.find((row) => row.year === 2024);

  const allYears = useMemo(
    () =>
      [...new Set([...teenLabor.map((row) => row.year), ...licensure.map((row) => row.year)])].sort((a, b) => a - b),
    [teenLabor, licensure],
  );

  const xForYear = useMemo(() => {
    const span = allYears[allYears.length - 1] - allYears[0];
    return (year) => PLOT_LEFT + ((year - allYears[0]) / span) * (PLOT_RIGHT - PLOT_LEFT);
  }, [allYears]);

  const teenScale = useMemo(
    () => buildLinearScale(teenLabor.map((row) => row.lfpr), PLOT_TOP, PLOT_BOTTOM, { min: 30, tickCount: 5, paddingRatio: 0.04 }),
    [teenLabor],
  );
  const licensureScale = useMemo(
    () => buildLinearScale(licensure.map((row) => row.share), PLOT_TOP, PLOT_BOTTOM, { min: 0, max: 8, tickCount: 5, paddingRatio: 0 }),
    [licensure],
  );

  const selectedYear = hoverYear ?? allYears[allYears.length - 1];
  const selectedX = xForYear(selectedYear);
  const yearGridYears = YEAR_GRID.filter((year) => year >= allYears[0] && year <= allYears[allYears.length - 1]);
  const selectedTeen = teenLabor.find((row) => row.year === selectedYear);
  const selectedLicensure = licensure.find((row) => row.year === selectedYear);
  const path = buildLinePath(
    teenLabor.map((row) => ({ year: row.year, value: row.lfpr })),
    xForYear,
    teenScale.yForValue,
  );

  const eventMarkers = useMemo(
    () => [
      { start: 2007, end: 2009, label: "2007-09 Great Recession", y: PLOT_TOP + 42 },
    ].map((event) => {
      const x1 = xForYear(event.start);
      const x2 = xForYear(event.end);
      return { ...event, x1, x2, labelX: (x1 + x2) / 2 };
    }),
    [xForYear],
  );

  const handleHover = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * SVG_WIDTH;
    const clamped = Math.max(PLOT_LEFT, Math.min(PLOT_RIGHT, x));
    const span = allYears[allYears.length - 1] - allYears[0];
    const rawYear = allYears[0] + ((clamped - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT)) * span;
    const nearest = allYears.reduce(
      (best, candidate) => (Math.abs(candidate - rawYear) < Math.abs(best - rawYear) ? candidate : best),
      allYears[0],
    );
    setHoverYear(nearest);
  };

  const teenPeak = teenLabor.reduce((best, row) => (row.lfpr > best.lfpr ? row : best), teenLabor[0]);

  return (
    <PanelFrame
      kicker="Teen work vs. teen licensure"
      title="Teen work and teen licensure declined over the same broad period."
      subtitle="Teen labor force participation is shown on the left. Teen licensure is repeated on the right."
      badge="Work + licensure"
    >
      <div className="panel-chart-frame" onPointerMove={handleHover} onPointerLeave={() => setHoverYear(null)}>
        <svg
          className="panel-chart-svg"
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          role="img"
          aria-label="Teen labor participation and teen licensure chart."
          style={{ cursor: "crosshair" }}
        >
          <defs>
            <clipPath id="clip-teen">
              <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={PLOT_BOTTOM - PLOT_TOP} />
            </clipPath>
          </defs>
          <rect x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT} rx="24" fill="#FFFDF8" />
          <text x={PLOT_LEFT} y="56" className="svg-kicker">
            Supporting panel
          </text>
          <text x={PLOT_LEFT} y="86" className="svg-title">
            Teen labor participation and teen licensure, 1963 to 2024
          </text>
          <text x={PLOT_LEFT} y="112" className="svg-subtitle">
            Teen LFPR is the teal line on the left. The gold bars repeat 16-18 licensed share on the right so the reader can compare
            them directly.
          </text>

          <rect x={PLOT_LEFT} y={PLOT_TOP} width={PLOT_RIGHT - PLOT_LEFT} height={PLOT_BOTTOM - PLOT_TOP} className="plot-backdrop" />

          {eventMarkers.map((event) => (
            <g key={event.label} pointerEvents="none">
              <rect x={event.x1} y={PLOT_TOP} width={event.x2 - event.x1} height={PLOT_BOTTOM - PLOT_TOP} fill="rgba(31,122,140,0.04)" />
              <line x1={event.x1} x2={event.x1} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(31,122,140,0.18)" strokeWidth="1" strokeDasharray="4 5" />
              <line x1={event.x2} x2={event.x2} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(31,122,140,0.18)" strokeWidth="1" strokeDasharray="4 5" />
              <text x={event.labelX} y={event.y} className="axis-label axis-label-center" fill="#475467" fontWeight="700" fontSize="10">
                {event.label}
              </text>
            </g>
          ))}

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
          <text x={TEEN_AXIS_X} y={PLOT_TOP - 18} className="axis-label axis-label-center" fill="#1F7A8C" fontWeight="700">
            Annual teen LFPR
          </text>

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
          <line x1={LICENSURE_AXIS_X} x2={LICENSURE_AXIS_X} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="#D4A017" strokeWidth="1.5" strokeDasharray="6 4" />
          <text x={LICENSURE_AXIS_X} y={PLOT_TOP - 18} className="axis-label axis-label-center" fill="#8A6400" fontWeight="700">
            16-18 driver share
          </text>

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

          <g clipPath={`url(#clip-teen)`}>
            {licensure.map((row) => {
              const x = xForYear(row.year);
              const barTop = licensureScale.yForValue(row.share);
              const barBase = licensureScale.yForValue(0);
              const barH = Math.max(0, barBase - barTop);
              const isSelected = row.year === selectedYear;

              return (
                <rect
                  key={`lic-${row.year}`}
                  x={x - (isSelected ? 10 : 7) / 2}
                  y={barTop}
                  width={isSelected ? 10 : 7}
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

            <path d={path} fill="none" stroke="#1F7A8C" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" pointerEvents="none" />

            {selectedTeen && (
              <circle cx={selectedX} cy={teenScale.yForValue(selectedTeen.lfpr)} r="5" fill="#1F7A8C" stroke="#FFFDF8" strokeWidth="2" pointerEvents="none" />
            )}
            {selectedLicensure && (
              <circle cx={selectedX} cy={licensureScale.yForValue(selectedLicensure.share)} r="5" fill="#C89200" stroke="#FFFDF8" strokeWidth="2" pointerEvents="none" />
            )}

            <line x1={selectedX} x2={selectedX} y1={PLOT_TOP} y2={PLOT_BOTTOM} stroke="rgba(23,32,51,0.2)" strokeWidth="1.5" strokeDasharray="5 5" pointerEvents="none" />

            {teenPeak && (
              <g pointerEvents="none">
                <line
                  x1={xForYear(teenPeak.year)}
                  x2={xForYear(teenPeak.year)}
                  y1={teenScale.yForValue(teenPeak.lfpr) - 26}
                  y2={teenScale.yForValue(teenPeak.lfpr) - 7}
                  stroke="#16616E"
                  strokeWidth="1.2"
                  strokeDasharray="3 2"
                />
                <text
                  x={xForYear(teenPeak.year)}
                  y={teenScale.yForValue(teenPeak.lfpr) - 32}
                  className="axis-label axis-label-center"
                  fill="#1F7A8C"
                  fontWeight="700"
                  fontSize="10"
                >
                  Teen LFPR peak 1979
                </text>
              </g>
            )}
          </g>

          <text x={selectedX + 8} y={PLOT_TOP + 20} className="hover-year-label">
            {selectedYear}
          </text>
        </svg>
      </div>

      <div className="chart-summary chart-summary-global">
        <span className="summary-label">Work summary</span>
        <div className="summary-grid">
          <div className="summary-pill">
            <span className="summary-swatch" style={{ background: "#1F7A8C" }} aria-hidden="true" />
            <div>
              <span className="summary-name">Teen LFPR, 1979 to 2024</span>
              <strong>{formatSignedPercent(percentChange(teen1979.lfpr, teen2024.lfpr))}</strong>
            </div>
          </div>
          <div className="summary-pill">
            <span className="summary-swatch" style={{ background: "#8A6400" }} aria-hidden="true" />
            <div>
              <span className="summary-name">Teen licensure, 1980 to 2024</span>
              <strong>{formatSignedPercent(percentChange(licensure1980.share, licensure2024.share))}</strong>
            </div>
          </div>
          <div className="summary-pill">
            <span className="summary-swatch" style={{ background: "#1F7A8C" }} aria-hidden="true" />
            <div>
              <span className="summary-name">Recession marker</span>
              <strong>2007-09</strong>
            </div>
          </div>
        </div>
      </div>
    </PanelFrame>
  );
}

export default function OverlayExperimentSplitChart() {
  return (
    <div className="chart-stack">
      <DrivingCostsChart />
      <TeenWorkChart />
    </div>
  );
}
