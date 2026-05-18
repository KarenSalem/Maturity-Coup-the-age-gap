import React from "react";
import SeparatedTrendChart from "../components/SeparatedTrendChart";

export default function HomePage() {
  return (
    <div className="page-shell">
      <main className="hero-card">
        <p className="eyebrow">Data package · 1963–2024</p>
        <h1>Auto Insurance Has Risen 32× Since 1963. Teen Licensure Has Fallen 61% From Its Peak.</h1>
        <p className="dek">
          A 61-year dataset from BLS and federal highway records maps motor vehicle insurance costs,
          gasoline prices, and teen driver licensure in the main chart, with annual teen labor participation
          separated out below as a supporting panel. The correlation is hard to ignore - and deliberately
          left for you to interpret.
        </p>

        <div className="stat-row">
          <div className="stat-item">
            <span className="stat-value">32×</span>
            <span className="stat-label">Insurance cost increase since 1963, indexed</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">−61%</span>
            <span className="stat-label">Teen licensure share, 1974 peak to 2023</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">61 yrs</span>
            <span className="stat-label">Of federal data, 1963–2024</span>
          </div>
        </div>

        <div className="context-block">
          <p className="context-body">
            Motor vehicle insurance, indexed to 1963 = 100, has outpaced gasoline, wages, and overall CPI
            by a wide margin. Over the same period, the share of 18-year-olds who hold a driver's license
            has declined from its mid-1970s peak. This chart places those two trends on a shared timeline
            without asserting that one caused the other.
          </p>
          <p className="caveat">
            This data does not claim that insurance costs caused the decline in teen licensure. Graduated
            driver licensing laws, ride-sharing, and urbanization are co-occurring trends. The chart is a
            visual prompt for that conversation, not a conclusion.
          </p>
        </div>

        <SeparatedTrendChart />

        <div className="sources-block">
          <p className="sources-title">Sources</p>
          <div className="sources-grid">
            <div>
              <p className="sources-axis">Left axis — indexed to 1963 = 100</p>
              <ul className="sources-list">
                <li>Motor vehicle insurance — BLS Consumer Price Index, series CUUR0000SETD</li>
                <li>Gasoline — EIA / BLS CPI, historical leaded regular series</li>
              </ul>
            </div>
            <div>
              <p className="sources-axis">Right axis — percent</p>
              <ul className="sources-list">
                <li>Teen licensure share — FHWA Highway Statistics, Table DL-20 (ages 16–18 as share of all licensed drivers)</li>
              </ul>
            </div>
          </div>
          <p className="sources-axis" style={{ marginTop: "16px" }}>Supporting chart below</p>
          <ul className="sources-list">
            <li>Annual teen labor participation — BLS Current Population Survey, annual teen LFPR (ages 16–19)</li>
          </ul>
          <p className="sources-axis" style={{ marginTop: "16px" }}>
            New essay: <a href="/teen-autonomy">/teen-autonomy</a>
          </p>
          <p className="sources-axis" style={{ marginTop: "16px" }}>
            Experimental overlay route: <a href="/overlay-experiment">/overlay-experiment</a>
          </p>
        </div>
      </main>
    </div>
  );
}
