import licensedDriversCsv from "../../licensed-drivers/licensed-drivers.csv?raw";

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const header = lines[0]
    .split(",")
    .map((cell) => cell.trim().replace(/^"|"$/g, ""));

  return lines.slice(1).map((line) => {
    const cells = [];
    let current = "";
    let inQuotes = false;

    for (let index = 0; index < line.length; index += 1) {
      const character = line[index];

      if (character === '"') {
        inQuotes = !inQuotes;
        continue;
      }

      if (character === "," && !inQuotes) {
        cells.push(current);
        current = "";
        continue;
      }

      current += character;
    }

    cells.push(current);

    return Object.fromEntries(
      header.map((key, index) => [key, (cells[index] ?? "").trim()]),
    );
  });
}

function sumDrivers(rows) {
  return rows.reduce((total, row) => total + Number.parseInt(row.Drivers.replace(/,/g, ""), 10), 0);
}

export function getYouthShareSeries() {
  const rows = parseCsv(licensedDriversCsv);
  const seriesByYear = new Map();

  for (const row of rows) {
    const year = Number.parseInt(row.Year, 10);
    const cohort = row.Cohort;
    const drivers = row.Drivers;

    if (!drivers) {
      continue;
    }

    if (!seriesByYear.has(year)) {
      seriesByYear.set(year, {
        year,
        totalDrivers: 0,
        youthDrivers: 0,
      });
    }

    const yearBucket = seriesByYear.get(year);
    const driverCount = Number.parseInt(drivers.replace(/,/g, ""), 10);
    yearBucket.totalDrivers += driverCount;

    if (cohort === "16" || cohort === "17" || cohort === "18") {
      yearBucket.youthDrivers += driverCount;
    }
  }

  return [...seriesByYear.values()]
    .sort((left, right) => left.year - right.year)
    .map((entry) => ({
      year: entry.year,
      totalDrivers: entry.totalDrivers,
      youthDrivers: entry.youthDrivers,
      share: (entry.youthDrivers / entry.totalDrivers) * 100,
    }));
}
