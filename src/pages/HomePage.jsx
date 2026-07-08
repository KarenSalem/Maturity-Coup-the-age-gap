import React from "react";

const pageLinks = [
  {
    title: "Teen Autonomy Essay",
    href: "/teen-autonomy",
    description: "Narrative page for the core age-gap thesis, with embedded figures and source notes.",
  },
  {
    title: "Driving Costs Package",
    href: "/driving-costs",
    description: "The previous homepage: insurance, gasoline, teen licensure, and teen labor participation.",
  },
  {
    title: "Polished Chart Page",
    href: "/polished",
    description: "A tighter version of the driving-cost and teen-autonomy chart package.",
  },
  {
    title: "Overlay Experiment",
    href: "/overlay-experiment",
    description: "Experimental split-chart treatment with copyable stats and export controls.",
  },
  {
    title: "Figure 1 Embed Route",
    href: "/teen-autonomy-figure-1",
    description: "React route for the first teen-autonomy embed figure.",
  },
];

const staticPages = [
  ["Figure 1 standalone embed", "/teen-autonomy-figure-1-embed.html"],
  ["Figure 2 standalone embed", "/teen-autonomy-figure-2-embed.html"],
  ["Figure 3 standalone embed", "/teen-autonomy-figure-3-embed.html"],
  ["Figure 4 standalone embed", "/teen-autonomy-figure-4-embed.html"],
  ["Legacy embed shell", "/embed.html"],
  ["Licensed drivers editorial", "/licensed-drivers/maturity-gap-editorial.html"],
  ["Maturity gap quizlet", "/licensed-drivers/maturity-gap-quizlet.html"],
  ["Maturity gap quizlet embed", "/licensed-drivers/maturity-gap-quizlet-embed.html"],
  ["Minimum wage car affordability", "/licensed-drivers/minimum-wage-car-affordability.html"],
  ["BLS editorial", "/bls/bls-editorial.html"],
  ["CPI editorial", "/cpi/cpi-editorial.html"],
];

const visualResources = [
  ["Licensed driver age rate, 2010-2024", "/licensed-drivers/licensed-drivers-age-rate-2010-2024.svg"],
  ["Licensed drivers, age split 16-21", "/licensed-drivers/licensed-drivers-age-split-16-21.svg"],
  ["Licensed drivers age pyramid, 2024", "/licensed-drivers/licensed-drivers-age-pyramid-2024.svg"],
  ["18-year-old driver callout", "/licensed-drivers/licensed-drivers-18-year-old-callout.svg"],
  ["18-year-old driver mini", "/licensed-drivers/licensed-drivers-18-year-old-mini.svg"],
  ["Licensed drivers youth shares", "/licensed-drivers/licensed-drivers-youth-shares.svg"],
  ["Licensed drivers and youth work overlay", "/licensed-drivers/licensed-drivers-youth-work-overlay.svg"],
  ["Gasoline teen context", "/licensed-drivers/licensed-drivers-gasoline-teen-context.svg"],
  ["Licensed drivers gasoline splice", "/licensed-drivers/licensed-drivers-gasoline-splice.svg"],
  ["Minimum wage car affordability", "/licensed-drivers/minimum-wage-car-affordability.svg"],
  ["BLS teen annual line", "/bls/bls-teens-annual-line.svg"],
  ["BLS A-8b age split", "/bls/bls-a8b-age-split.svg"],
  ["BLS summer July line", "/bls/bls-summer-july-line.svg"],
  ["BLS age gradient", "/bls/bls-age-gradient.svg"],
  ["Census AD-1 long trend", "/census/census-ad1-longtrend.svg"],
  ["Census living at home benchmark", "/census/census-living-at-home-benchmark.svg"],
  ["ATUS socializing by age", "/atus/atus-socializing-age-2024.svg"],
  ["ATUS alone with others by age", "/atus/atus-alone-with-others-age-2024.svg"],
  ["CPI motor vehicle insurance index", "/cpi/cpi-motor-vehicle-insurance-index.svg"],
  ["CPI motor vehicle insurance growth bars", "/cpi/cpi-motor-vehicle-insurance-growth-bars.svg"],
  ["CPI teen pricing context", "/cpi/cpi-teen-pricing-context.svg"],
];

const sourceGroups = [
  {
    title: "Licensed Drivers",
    links: [
      ["Source notes", "/licensed-drivers/source.md"],
      ["Why this matters", "/licensed-drivers/why-this-matters.md"],
      ["Licensed drivers CSV", "/licensed-drivers/licensed-drivers.csv"],
      ["Youth work overlay CSV", "/licensed-drivers/licensed-drivers-youth-work-overlay.csv"],
      ["Gasoline teen context CSV", "/licensed-drivers/licensed-drivers-gasoline-teen-context.csv"],
      ["Crude oil first purchase price CSV", "/licensed-drivers/crude-oil-first-purchase-price.csv"],
      ["Minimum wage car affordability CSV", "/licensed-drivers/minimum-wage-car-affordability.csv"],
      ["Youth work overlay notes", "/licensed-drivers/licensed-drivers-youth-work-overlay/why-this-matters.md"],
    ],
  },
  {
    title: "BLS Labor",
    links: [
      ["Source notes", "/bls/source.md"],
      ["Quote pack", "/bls/bls-quote-pack.md"],
      ["Teen annual LFPR CSV", "/bls/teen-annual-lfpr.csv"],
      ["A-8b age split history CSV", "/bls/a8b-age-split-history.csv"],
      ["July youth LFPR history CSV", "/bls/july-youth-lfpr-history.csv"],
    ],
  },
  {
    title: "Census Household Independence",
    links: [
      ["Source notes", "/census/source.md"],
      ["Summary facts", "/census/summary-facts.md"],
      ["AD-1 living at home CSV", "/census/ad1-living-at-home.csv"],
      ["Living at home benchmark CSV", "/census/living-at-home-benchmark.csv"],
    ],
  },
  {
    title: "ATUS Social Connection",
    links: [
      ["Source notes", "/atus/source.md"],
      ["Summary facts", "/atus/summary-facts.md"],
      ["Microdata plan", "/atus/microdata-plan.md"],
      ["Socializing by age CSV", "/atus/socializing-by-age-2024.csv"],
      ["Alone with others CSV", "/atus/alone-with-others-2024.csv"],
    ],
  },
  {
    title: "CPI Driving Costs",
    links: [
      ["Source notes", "/cpi/source.md"],
      ["Insurance history CSV", "/cpi/cpi-motor-vehicle-insurance-history.csv"],
      ["Insurance annual CSV", "/cpi/cpi-motor-vehicle-insurance-annual.csv"],
      ["Why this matters", "/cpi/cpi-motor-vehicle-insurance/why-this-matters.md"],
    ],
  },
  {
    title: "Research and Outreach",
    links: [
      ["Project instructions", "/AGENTS.md"],
      ["Maturity quizlet research", "/maturity%20quizlet/research.md"],
      ["Journalist research and pitches", "/journalists/top-journalists_gemini-deep-research-jlh.md"],
      ["Reference PDF", "/sec9_6.pdf"],
    ],
  },
];

function LinkList({ items }) {
  return (
    <ul className="directory-link-list">
      {items.map(([label, href]) => (
        <li key={href}>
          <a href={href}>{label}</a>
        </li>
      ))}
    </ul>
  );
}

export default function HomePage() {
  return (
    <main className="directory-page">
      <header className="directory-header">
        <p className="eyebrow">Maturity coup data package</p>
        <h1>Site Directory</h1>
        <p>
          A navigational index for the pages, embeds, figures, source notes, and source data in this repo.
        </p>
      </header>

      <section className="directory-section" aria-labelledby="page-routes">
        <div className="directory-section-head">
          <p className="directory-kicker">Pages</p>
          <h2 id="page-routes">Primary routes</h2>
        </div>
        <div className="directory-card-grid">
          {pageLinks.map((link) => (
            <a className="directory-card" href={link.href} key={link.href}>
              <span>{link.title}</span>
              <p>{link.description}</p>
            </a>
          ))}
        </div>
      </section>

      <section className="directory-section" aria-labelledby="standalone-pages">
        <div className="directory-section-head">
          <p className="directory-kicker">Standalone</p>
          <h2 id="standalone-pages">HTML pages and embeds</h2>
        </div>
        <LinkList items={staticPages} />
      </section>

      <section className="directory-section" aria-labelledby="visual-assets">
        <div className="directory-section-head">
          <p className="directory-kicker">Figures</p>
          <h2 id="visual-assets">SVG visual assets</h2>
        </div>
        <LinkList items={visualResources} />
      </section>

      <section className="directory-section" aria-labelledby="source-files">
        <div className="directory-section-head">
          <p className="directory-kicker">Sources</p>
          <h2 id="source-files">Notes and data files</h2>
        </div>
        <div className="directory-source-grid">
          {sourceGroups.map((group) => (
            <div className="directory-source-group" key={group.title}>
              <h3>{group.title}</h3>
              <LinkList items={group.links} />
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
