import React from "react";
import HtmlWidget from "../components/HtmlWidget";
import teenAutonomyFigure1Html from "../../teen-autonomy-figure-1-embed.html?raw";

export default function TeenAutonomyFigure1EmbedPage() {
  return (
    <div className="owid-page-shell">
      <main className="owid-page" style={{ paddingTop: "24px", paddingBottom: "24px" }}>
        <section className="owid-figure-block" aria-label="Figure 1">
          <div className="owid-figure-frame">
            <HtmlWidget html={teenAutonomyFigure1Html} />
          </div>
        </section>
      </main>
    </div>
  );
}
