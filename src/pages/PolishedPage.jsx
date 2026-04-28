import React from "react";
import SeparatedTrendChart from "../components/SeparatedTrendChart";

export default function PolishedPage() {
  return (
    <div className="page-shell">
      <main className="hero-card">
        <p className="eyebrow">Maturity coup data package</p>
        <h1>One chart for driving costs and teen autonomy</h1>
        <p className="dek">
          The driving-cost lines stay indexed to 1963 = 100 so the price shocks remain comparable. The teen-autonomy lines each get
          their own native y-axis so licensure and work trends do not get flattened into one compromise scale.
        </p>

        <SeparatedTrendChart />
      </main>
    </div>
  );
}
