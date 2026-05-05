import React from "react";
import OverlayExperimentChart from "../components/OverlayExperimentChart";

export default function OverlayExperimentPage() {
  return (
    <div className="page-shell">
      <main className="hero-card">
        <p className="eyebrow">Experimental route</p>
        <h1>One chart with a bar overlay for teen licensure</h1>
        <p className="dek">
          This is the experiment you asked for: driving costs on the left, annual teen labor participation on a right-side line axis,
          and teen licensure as gold bars on a fixed 0-6% scale. It is useful for testing the look, but I would treat it as a draft,
          not the publication version.
        </p>

        <OverlayExperimentChart />
      </main>
    </div>
  );
}

