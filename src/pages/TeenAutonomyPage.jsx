import React from "react";
import HtmlWidget from "../components/HtmlWidget";
import teenAutonomyFigure1Html from "../../teen-autonomy-figure-1-embed.html?raw";
import teenAutonomyFigure2Html from "../../teen-autonomy-figure-2-embed.html?raw";
import teenAutonomyFigure3Html from "../../teen-autonomy-figure-3-embed.html?raw";
import teenAutonomyFigure4Html from "../../teen-autonomy-figure-4-embed.html?raw";
import teenAutonomyCallout1Html from "../../teen-autonomy-callout-1-licensure.html?raw";
import teenAutonomyCallout2Html from "../../teen-autonomy-callout-2-insurance.html?raw";
import teenAutonomyCallout3Html from "../../teen-autonomy-callout-3-labor.html?raw";
import teenAutonomyCallout4Html from "../../teen-autonomy-callout-4-living-at-home.html?raw";
import teenAutonomyCalloutsSharedHtml from "../../teen-autonomy-callouts-shared.html?raw";

function Section({ kicker, title, children, id }) {
  return (
    <section className="owid-section" id={id}>
      {kicker ? <p className="owid-section-kicker">{kicker}</p> : null}
      <h2>{title}</h2>
      <div className="owid-section-body">{children}</div>
    </section>
  );
}

export default function TeenAutonomyPage() {
  return (
    <div className="owid-page-shell">
      <main className="owid-page">
        <HtmlWidget html={teenAutonomyCalloutsSharedHtml} />

        <header className="owid-hero">
          <h1>Teen Autonomy</h1>
          <p className="owid-dek">
            Are today&apos;s 18-year-olds less independent than earlier generations? How much of that change can
            be seen in the federal records on driving, work, and the cost of getting on the road?
          </p>
        </header>

        <section className="owid-opening" aria-label="Introduction">
          <p>
            For much of the late 20th century, the route into adult life was visible in ordinary teenage
            routines: get a job, get a license, borrow or buy access to a car, and begin moving through the
            world without a parent in the passenger seat.
          </p>
          <p>
            That route has narrowed. The share of licensed drivers who are 16 to 18 years old peaked in 1974.
            Teen labor force participation peaked five years later. Since then, both measures have moved down
            while the cost of driving, especially gas and insurance, has moved sharply up.
          </p>
        </section>

        <Section
          id="chart"
          title="Teen licensure fell while one fixed cost kept rising"
        >
          <p>
            In 1963, teenagers aged 16 to 18 made up 4.78 percent of all licensed drivers in the United States.
            By 1974, their share reached 6.28 percent, the highest point in the federal record.
          </p>
          <p>
            Then the pattern changed. Fuel prices rose and fell through the oil shocks and their aftermath, but
            motor vehicle insurance climbed more steadily. By 2024, the teen share of licensed drivers had fallen
            to 2.46 percent.
          </p>
        </Section>

        <section className="owid-figure-block">
          <div className="owid-figure-frame">
            <HtmlWidget html={teenAutonomyFigure1Html} />
          </div>
        </section>

        <Section
          id="headline"
          title="Teen licensure never recovered from its 1970s peak."
        >
          <p>
            In 1974, teenagers aged 16 to 18 made up 6.28 percent of all licensed drivers in the United States.
            By 2024, that share had fallen to 2.46 percent. That is a 61 percent decline from peak, and it did not
            stop at the pandemic or rebound afterward.
          </p>
          <p>
            The important point is the shape of the decline. It begins in the mid-1970s, continues through the
            1980s and 1990s, and never returns to the old peak. That makes the question less about one shock
            and more about a set of conditions that changed the economics and habits of teen independence.
          </p>
        </Section>

        <HtmlWidget html={teenAutonomyCallout1Html} />

        <section className="owid-figure-block">
          <div className="owid-figure-frame">
            <HtmlWidget html={teenAutonomyFigure2Html} />
          </div>
        </section>

        <section className="owid-figure-block">
          <div className="owid-figure-frame">
            <HtmlWidget html={teenAutonomyFigure3Html} />
          </div>
        </section>

        <Section
          id="costs"
          title="Gas spikes were real, but insurance is the steadier long-run pressure."
        >
          <p>
            Oil shocks matter here because they are the most visible price shocks in the record. The first oil embargo,
            the Iranian Revolution, and the 1979-80 shock are all real events that affected household budgets.
            But the data on teen licensure do not map cleanly onto a story in which gasoline alone explains the decline.
          </p>
          <p>
            The more durable price signal is motor vehicle insurance. Insurance rose much faster than overall prices,
            and unlike gasoline it did so with only minor dips over time. That does not prove insurance caused fewer
            teens to drive. It does make insurance a credible affordability barrier that stayed in place long after
            the oil shocks faded.
          </p>
          <p>
            The familiar gas-price explanation is incomplete. The insurance series does not prove causation,
            but it fits the long decline better than a one-off fuel shock does.
          </p>
        </Section>

        <HtmlWidget html={teenAutonomyCallout2Html} />

        <Section
          id="work"
          title="Teen labor participation fell in parallel, which makes the story broader than cars alone."
        >
          <p>
            Teen labor force participation peaked at 57.9 percent in 1979 and fell to 36.9 percent in 2024.
            That is not the same series as licensure, and the peaks are not perfectly aligned. But the overall
            direction is the same, which matters. Teens were not only driving less; they were also spending less
            time in the labor market that once helped finance the move into adulthood.
          </p>
          <p>
            That broadens the picture beyond a simple driving-cost story. No single variable explains the decline
            in teen autonomy on its own. School pressure, transport costs, family expectations, and policy changes
            all appear to be moving together.
          </p>
        </Section>

        <HtmlWidget html={teenAutonomyCallout3Html} />

        <Section
          id="living-arrangements"
          title="The independence question doesn't end at 18. It shows up in who is still living at home."
        >
          <p>
            Census data on living arrangements picks up the story where the driving and labor numbers leave off.
            Among 18-to-24-year-olds, the share of women living in their parents&apos; home has nearly doubled since
            1960, climbing from 34.9 percent to 56.4 percent in 2024. The share of young men living at home has
            moved far less over the same period, but it has not moved down. It sat at 52.4 percent in 1960 and was
            58.3 percent in 2024, after spending most of the 1980s through today above 55 percent.
          </p>
          <p>
            The headline is less &quot;more young adults live with their parents&quot; than &quot;the gap between
            young men and young women has closed.&quot; In 1960, a 17.5-point gap separated the two lines. By 2024,
            that gap had shrunk to 1.9 points. Men&apos;s living-at-home rate never returned to its 1960s-70s floor,
            and women&apos;s rate rose to meet it.
          </p>
        </Section>

        <HtmlWidget html={teenAutonomyCallout4Html} />

        <section className="owid-figure-block">
          <div className="owid-figure-frame">
            <HtmlWidget html={teenAutonomyFigure4Html} />
          </div>
        </section>

        <Section
          id="notes"
          title="Sources and methods"
        >
          <p>
            The figures combine public federal data to answer a timing question: what changed first, what changed
            together, and what changed later?
          </p>
          <p>
            The charts do not claim that one series is the sole cause of another. They show how teen licensure,
            teen labor participation, and driving costs moved across the same historical period.
          </p>
          <div className="owid-sources-grid">
            <div>
              <h3>Licensed drivers</h3>
              <ul>
                <li>Federal Highway Administration, Highway Statistics, Table DL-220, 1963-2024.</li>
                <li>Youth share computed as licensed drivers ages 16-18 divided by all licensed drivers.</li>
              </ul>
            </div>
            <div>
              <h3>Teen labor</h3>
              <ul>
                <li>Bureau of Labor Statistics, Current Population Survey annual teen labor force participation rate.</li>
                <li>Series used as a broad teen benchmark, not a pure 18-year-old-only measure.</li>
              </ul>
            </div>
            <div>
              <h3>Driving costs</h3>
              <ul>
                <li>BLS Consumer Price Index for motor vehicle insurance.</li>
                <li>U.S. Energy Information Administration gasoline price history.</li>
                <li>Federal Reserve History and IIHS used for the event markers in the driving panel.</li>
              </ul>
            </div>
            <div>
              <h3>Living arrangements</h3>
              <ul>
                <li>U.S. Census Bureau, Historical Living Arrangements of Adults, Table AD-1.</li>
                <li>Share of 18-24-year-olds living in the parental home, by sex, 1960-2025.</li>
              </ul>
            </div>
            <div>
              <h3>Method</h3>
              <ul>
                <li>All percentage changes use raw source values, without interpolation.</li>
                <li>Charted cost series are indexed to 1963 = 100 for visual comparability.</li>
              </ul>
            </div>
          </div>
        </Section>
      </main>
    </div>
  );
}
