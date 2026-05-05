import React from "react";
import SeparatedTrendChart from "../components/SeparatedTrendChart";

export default function PolishedPage() {
  return (
    <div className="page-shell">
      <main className="hero-card">
        <p className="eyebrow">Maturity coup data package</p>
        <h1>One chart for driving costs and teen autonomy</h1>
        <p className="dek">
          The driving-cost lines stay indexed to 1963 = 100 so the price shocks remain comparable. Teen licensure gets the main
          percent axis, while annual teen labor participation moves to a separate supporting panel below so neither series gets
          flattened into a compromise scale.
        </p>

        <SeparatedTrendChart />
        <p className="chart-foot">
          <span>
            Experimental overlay route: <a href="/overlay-experiment">/overlay-experiment</a>
          </span>
        </p>
      </main>
    </div>
  );
}
