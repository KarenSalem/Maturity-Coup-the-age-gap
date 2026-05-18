import React, { useRef, useState, useCallback } from "react";
import OverlayExperimentSplitChart from "../components/OverlayExperimentSplitChart";

function useClipboard(timeout = 2000) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(
    async (text) => {
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const el = document.createElement("textarea");
        el.value = text;
        el.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(el);
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), timeout);
    },
    [timeout],
  );
  return [copied, copy];
}

function StatItem({ value, label, citation }) {
  const [copied, copy] = useClipboard();
  return (
    <div className="stat-item">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
      <button className="stat-copy-btn" onClick={() => copy(citation)}>
        {copied ? "Copied" : "Copy stat"}
      </button>
    </div>
  );
}

const INLINE_SVG_STYLES = `
  text { font-family: Arial, Helvetica, sans-serif; }
  .svg-kicker { font-size: 13px; font-weight: 700; fill: #667085; letter-spacing: 0.08em; text-transform: uppercase; }
  .svg-title { font-size: 23px; font-weight: 700; fill: #101828; font-family: Georgia, serif; }
  .svg-subtitle { font-size: 13px; fill: #667085; }
  .axis-label { fill: #667085; font-size: 12px; }
  .axis-label-right { text-anchor: end; }
  .axis-label-center { text-anchor: middle; }
  .axis-label-start { text-anchor: start; }
  .grid-line { stroke: rgba(23,32,51,0.1); stroke-width: 1; }
  .vertical-grid-line { stroke: rgba(23,32,51,0.06); stroke-width: 1; }
  .plot-backdrop { fill: #fffdf9; }
  .axis-tick { stroke: rgba(23,32,51,0.18); stroke-width: 1; }
`;

function downloadChartAsPng(containerRef) {
  const svgEls = Array.from(containerRef.current?.querySelectorAll("svg") ?? []);
  if (!svgEls.length) return;

  const loadImage = (svgEl) =>
    new Promise((resolve, reject) => {
      const clone = svgEl.cloneNode(true);
      clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      const styleEl = document.createElementNS("http://www.w3.org/2000/svg", "style");
      styleEl.textContent = INLINE_SVG_STYLES;
      clone.prepend(styleEl);
      const svgStr = new XMLSerializer().serializeToString(clone);
      const blob = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(url);
        resolve(img);
      };
      img.onerror = (error) => {
        URL.revokeObjectURL(url);
        reject(error);
      };
      img.src = url;
    });

  Promise.all(svgEls.map(loadImage)).then((images) => {
    const scale = 2;
    const gap = 40;
    const widths = svgEls.map((svgEl) => Number(svgEl.viewBox.baseVal.width || svgEl.getAttribute("width") || 1540));
    const heights = svgEls.map((svgEl) => Number(svgEl.viewBox.baseVal.height || svgEl.getAttribute("height") || 760));
    const canvasWidth = Math.max(...widths) * scale;
    const canvasHeight = (heights.reduce((sum, value) => sum + value, 0) + gap * (images.length - 1)) * scale;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    ctx.scale(scale, scale);
    ctx.fillStyle = "#FFFDF8";
    ctx.fillRect(0, 0, canvasWidth / scale, canvasHeight / scale);

    let offsetY = 0;
    images.forEach((img, index) => {
      ctx.drawImage(img, 0, offsetY, widths[index], heights[index]);
      offsetY += heights[index] + gap;
    });

    canvas.toBlob((pngBlob) => {
      if (!pngBlob) return;
      const pngUrl = URL.createObjectURL(pngBlob);
      const a = document.createElement("a");
      a.href = pngUrl;
      a.download = "teen-driving-data-panels-1963-2024.png";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(pngUrl);
    }, "image/png");
  });
}

export default function OverlayExperimentPage() {
  const chartRef = useRef(null);
  const [embedCopied, copyEmbed] = useClipboard();
  const [citeCopied, copyCite] = useClipboard();

  const pageUrl =
    typeof window !== "undefined" ? window.location.origin + window.location.pathname : "";
  const embedCode = `<iframe src="${pageUrl}" width="100%" height="1450" frameborder="0" title="Teen Driving Costs and Youth Labor Data, 1980–2024" style="border:none;border-radius:12px;"></iframe>`;
  const citationText = `"The Generation That Stopped Driving." 5K Research. ${pageUrl}. Data: FHWA Highway Statistics DL-220; BLS CPI Motor Vehicle Insurance (CUUR0000SETA02); BLS Current Population Survey teen LFPR; U.S. EIA gasoline price data; Federal Reserve History oil-shock context; IIHS graduated driver licensing context. Accessed May 2026.`;

  return (
    <div className="page-shell">
      <main className="hero-card">
        <p className="eyebrow">Data Report &nbsp;&middot;&nbsp; Youth &amp; Mobility</p>

        <h1>The Generation That Stopped Driving</h1>

        <p className="dek">
          Teenagers once claimed more than 6 percent of every licensed driver in the United States.
          By 2024, that share had fallen by 61 percent from its peak. Federal Highway Administration
          records go back to 1963&mdash;and the charts below show when the slide emerged,
          which explanations fit the timing, and which ones need more caution.
        </p>

        <div className="stat-row stat-row-4">
          <StatItem
            value="&minus;54.5%"
            label="Teen share of licensed U.S. drivers, 1980 to 2024 (5.41% &rarr; 2.46%)"
            citation="Teen share of licensed U.S. drivers fell 54.5%—from 5.41% in 1980 to 2.46% in 2024. Source: FHWA Highway Statistics DL-220."
          />
          <StatItem
            value="+928%"
            label="Motor vehicle insurance nominal increase, 1980 to 2024"
            citation="Motor vehicle insurance rose 928% between 1980 and 2024, vs. 281% for overall CPI inflation. Source: BLS CPI Motor Vehicle Insurance (CUUR0000SETA02)."
          />
          <StatItem
            value="2.7&times;"
            label="Real cost of auto insurance today vs. 1980, after inflation adjustment"
            citation="Motor vehicle insurance costs 2.7 times more in real (inflation-adjusted) terms today than in 1980. Source: BLS CPI Motor Vehicle Insurance and CPI-U All Items."
          />
          <StatItem
            value="&minus;35%"
            label="Teen labor force participation decline, 1980 to 2024 (56.7% &rarr; 36.9%)"
            citation="Teen labor force participation fell 35%—from 56.7% in 1980 to 36.9% in 2024. Source: BLS Current Population Survey, ages 16–19."
          />
        </div>

        <div className="journalist-toolbar">
          <span className="journalist-toolbar-label">Use this data</span>
          <div className="journalist-toolbar-actions">
            <button className="tool-btn" onClick={() => downloadChartAsPng(chartRef)}>
              Download chart PNG
            </button>
            <button className="tool-btn" onClick={() => copyEmbed(embedCode)}>
              {embedCopied ? "Embed code copied" : "Copy embed code"}
            </button>
            <button className="tool-btn" onClick={() => copyCite(citationText)}>
              {citeCopied ? "Citation copied" : "Copy citation"}
            </button>
          </div>
        </div>

        <div ref={chartRef}>
          <OverlayExperimentSplitChart />
        </div>

        {/* Story 1: The Number */}
        <div className="context-block story-section">
          <p className="story-section-kicker">The Number</p>
          <h2>One Figure That Reframes the Story of Teen Independence</h2>
          <p className="context-body">
            In 1974, teenagers aged 16 to 18 made up 6.28 percent of every licensed driver in the
            United States&mdash;their highest share on record, according to Federal Highway
            Administration data stretching back to 1963. Today, they hold 2.46 percent.
          </p>
          <p className="context-body">
            That is a 61 percent decline from peak. Not a one-year dip. Not a pandemic-era
            interruption. A long structural decline that has never returned to its mid-1970s level.
          </p>
          <p className="context-body">
            The total U.S. driver population grew from 145 million in 1980 to nearly 240 million in
            2024&mdash;a 65 percent expansion. Over the same span, the absolute number of licensed
            16-to-18-year-olds fell from 7.9 million to 5.9 million, even as the overall pool grew
            by tens of millions. The road got far more crowded. Teenagers, in proportional terms,
            were simply not filling those seats.
          </p>
        </div>

        {/* Story 2: The Wrong Suspect */}
        <div className="context-block story-section">
          <p className="story-section-kicker">The Usual Suspect</p>
          <h2>Gas Prices Are the Familiar Suspect. The Data Points Elsewhere.</h2>
          <p className="context-body">
            One familiar explanation is gasoline prices. The oil shocks of the late
            1970s&mdash;the Iranian Revolution in 1979, the second oil shock in 1980&mdash;became
            cultural shorthand for why Americans changed their driving habits. The driving-costs chart now marks
            both the 1973-74 oil embargo and the 1979-80 second oil shock so readers can see those
            moments against the longer teen-licensing decline.
          </p>
          <div className="pull-stat">
            <span className="pull-stat-value">94&cent;</span>
            <span className="pull-stat-label">
              What a 2024 gallon of gas costs in 1980 dollars&mdash;less than the $1.19 it cost during the oil shock
            </span>
          </div>
          <p className="context-body">
            U.S. Energy Information Administration records show a gallon of regular gasoline cost
            $1.19 in 1980. In 2024, it cost $3.58. That sounds alarming&mdash;until you adjust for
            44 years of inflation. In 1980 dollars, that $3.58 gallon costs about 94 cents.
            Gasoline, in real terms, is <em>cheaper</em> today than it was during the oil shock era.
          </p>
          <p className="context-body">
            Motor vehicle insurance tells a completely different story. Bureau of Labor Statistics
            Consumer Price Index data shows that motor vehicle insurance costs rose 928 percent
            between 1980 and 2024&mdash;more than three times the rate of overall inflation, which
            rose 281 percent over the same period. In real, inflation-adjusted dollars, insuring a
            car today costs 2.7 times what it cost in 1980. Since 1960, the divergence is even
            starker: insurance is up 3,183 percent, versus 960 percent for overall prices.
          </p>
          <div className="pull-stat pull-stat-rose">
            <span className="pull-stat-value">3,183%</span>
            <span className="pull-stat-label">
              Motor vehicle insurance increase since 1960&mdash;vs. 960% for overall CPI inflation over the same period
            </span>
          </div>
          <p className="context-body">
            The structural difference between these two costs matters. Gasoline is a variable
            expense&mdash;it scales with miles driven and can be managed or deferred. Insurance
            is a fixed threshold. It must be paid before anyone turns a key. For a teenager with
            limited income, no vehicle equity, and a statistically higher actuarial risk profile,
            a rising insurance baseline can function less like a line item and more like an entry
            barrier. The CPI series is not teen-specific, so this should be read as affordability
            pressure rather than a complete causal explanation.
          </p>
        </div>

        {/* Story 3: Work Decline */}
        <div className="context-block story-section">
          <p className="story-section-kicker">The Other Half of the Story</p>
          <h2>As Costs Rose, Teen Work Receded</h2>
          <p className="context-body">
            The cost side of the equation moved against young drivers. So did the income side.
          </p>
          <p className="context-body">
            Bureau of Labor Statistics annual survey data shows the teen labor force participation
            rate&mdash;the share of teenagers working or actively seeking work&mdash;peaked at
            57.9 percent in 1979. It fell almost continuously for three decades afterward.
            By 2011, it had reached 34.1 percent, a figure that would have seemed statistically
            unthinkable in 1979. In 2024, it stood at 36.9 percent&mdash;barely recovered from
            that low range, and still 36 percent below its 1979 peak.
          </p>
          <div className="pull-stat pull-stat-teal">
            <span className="pull-stat-value">57.9% &rarr; 34.1%</span>
            <span className="pull-stat-label">
              Teen labor force participation from 1979 peak to 2011 trough&mdash;a 41 percent decline over three decades
            </span>
          </div>
          <p className="context-body">
            The convergence in the charts above does not prove one trend caused the other, but it is
            hard to dismiss as irrelevant. As teens exited the labor market, one financial
            underpinning of teen driving weakened in parallel. A license requires fees. A vehicle
            requires insurance before it can be legally operated. Insurance requires income. The
            economic foundation for teen driving thinned as the cost of building that foundation rose.
          </p>
          <p className="context-body">
            The charts&apos; teal line&mdash;annual teen labor participation&mdash;and the gold
            bars&mdash;teen share of licensed drivers&mdash;trace the same broad downward arc,
            though their peaks are not identical: licensure peaks in 1974, while teen LFPR peaks in
            1979. This parallel descent across two independent federal data series&mdash;the FHWA
            driver count and the BLS labor survey&mdash;is one of the clearest patterns in the
            dataset.
          </p>
        </div>

        {/* Story 4: The 1978 Inflection */}
        <div className="context-block story-section">
          <p className="story-section-kicker">The Inflection</p>
          <h2>The Peak Was 1974. It Has Never Recovered.</h2>
          <p className="context-body">
            The data has a visible inflection point. In 1974, teenagers aged 16 to 18 reached their
            highest share of the U.S. driver population: 6.28 percent. The annotation on the chart
            marks it. It happened during the same period as the first Arab oil embargo, but the
            timing cuts against a simple gas-price story: teen driver share did not peak before the
            first oil shock; it peaked during the immediate aftermath. Teen labor force participation
            was also still climbing, reaching 57.9 percent by 1979.
          </p>
          <p className="context-body">
            Then came the Iranian Revolution oil shock in 1979. Gasoline prices nearly doubled to
            86 cents, then crossed $1.19 in 1980. The gasoline index line in the chart spikes
            sharply at that moment. Teen driving share, which had begun retreating from its 1974
            peak, accelerated downward. Teen LFPR peaked at 57.9 percent in 1979 and turned.
          </p>
          <p className="context-body">
            Here is what the full 61-year record then reveals: when gasoline prices fell and
            stabilized through the mid-1980s, teen licensure did not recover. The gasoline line
            in the chart falls steeply after 1981. The gold bars keep falling regardless. When
            gas crashed to 86 cents per gallon in 1986&mdash;essentially the same nominal price
            as the 1979 shock&mdash;teen driving share kept falling. When gas touched a
            post-shock low of $1.12 per gallon in 1998, teen driving share kept falling.
            Fuel prices clearly mattered to household budgets, but the teen-licensing decline
            persisted through multiple fuel-price retreats.
          </p>
          <p className="context-body">
            The insurance line in the chart tells a different story. From 1963 to 2024, it trends
            sharply upward, with only a few small annual dips. That does not make insurance the sole
            cause of the teen-driving decline. It does make insurance a serious affordability
            pressure that moves in the opposite direction from teen licensure over the long run.
          </p>
          <p className="caveat">
            This analysis does not assert insurance as the sole cause of the teen-driving decline.
            The new chart markers show two other major contextual periods: graduated driver
            licensing laws spread across states from 1996 to 2006, and the 2007-09 Great Recession
            coincided with a sharp teen-labor drop. BLS also points to higher school enrollment,
            more summer school, tougher coursework, and parental emphasis on college as contributors
            to lower teen labor-force participation. The question the data raises is narrower and
            stronger: if gasoline is cheaper in real terms today than in 1980, what combination of
            costs, policy rules, school pressure, and teen work patterns has kept licensure from
            returning to its 1974 level?
          </p>
        </div>

        {/* Sources */}
        <div className="sources-block">
          <p className="sources-title">Data Sources &amp; Methodology</p>
          <div className="sources-grid">
            <div>
              <p className="sources-axis">Licensed Driver Counts</p>
              <ul className="sources-list">
                <li>
                  Federal Highway Administration. <em>Highway Statistics Series, Table DL-220: Licensed Drivers by Age Group.</em> Annual data, 1963&ndash;2024. U.S. Department of Transportation.
                </li>
                <li>
                  Youth driver share computed as 16-to-18-year-old licensed drivers as a
                  percentage of all licensed U.S. drivers, per annual FHWA counts.
                </li>
              </ul>
            </div>
            <div>
              <p className="sources-axis">Teen Labor Force Participation</p>
              <ul className="sources-list">
                <li>
                  Bureau of Labor Statistics. <em>Current Population Survey: Labor Force Participation Rate, Age 16&ndash;19.</em> Annual averages, 1948&ndash;2024. U.S. Department of Labor.
                </li>
              </ul>
            </div>
            <div>
              <p className="sources-axis">Driving Cost Indices</p>
              <ul className="sources-list">
                <li>
                  Bureau of Labor Statistics. <em>CPI-U: Motor Vehicle Insurance</em> (Series CUUR0000SETA02). Annual averages, 1960&ndash;2024. U.S. Department of Labor.
                </li>
                <li>
                  Bureau of Labor Statistics. <em>CPI-U All Items</em> (Series CUUR0000SA0). Annual averages, 1960&ndash;2024. Used as deflator for real-dollar calculations.
                </li>
                <li>
                  U.S. Energy Information Administration. <em>U.S. Regular Conventional Gas Price.</em> Annual average, 1978&ndash;2024.
                </li>
                <li>
                  Federal Reserve History. <em>Oil Shock of 1978-79.</em> Used for the 1979-80
                  second-oil-shock context marker.
                </li>
                <li>
                  Insurance Institute for Highway Safety. <em>History and current status of state
                  graduated driver licensing laws.</em> Used for the 1996-2006 GDL context marker.
                </li>
              </ul>
            </div>
            <div>
              <p className="sources-axis">Methodology</p>
              <ul className="sources-list">
                <li>
                  Cost indices re-indexed to 1963 = 100 to align with the FHWA driver count
                  series start. Real-dollar comparisons use BLS CPI-U All Items as deflator.
                </li>
                <li>
                  Percentage changes calculated as (end &minus; start) / start &times; 100 on
                  raw source values, without interpolation.
                </li>
                <li>
                  Youth driver share denominator includes all licensed drivers of all ages
                  per FHWA DL-220. Numerator includes cohorts 16, 17, and 18 only.
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
