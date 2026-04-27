import licensedDriversCsv from "../../licensed-drivers/licensed-drivers.csv?raw";
import teenAnnualCsv from "../../bls/teen-annual-lfpr.csv?raw";
import julyYouthHistoryCsv from "../../bls/july-youth-lfpr-history.csv?raw";
import julyYouthCsv from "../../bls/july-youth-lfpr.csv?raw";
import cpiInsuranceCsv from "../../cpi/cpi-motor-vehicle-insurance-annual.csv?raw";
import gasolineContextCsv from "../../licensed-drivers/licensed-drivers-gasoline-teen-context.csv?raw";

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

function parseNumber(value) {
  return Number.parseFloat(String(value).replace(/,/g, ""));
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

export function getTeenAnnualSeries() {
  return parseCsv(teenAnnualCsv)
    .map((row) => ({
      year: Number.parseInt(row.Year, 10),
      lfpr: parseNumber(row.LFPR),
    }))
    .filter((entry) => Number.isFinite(entry.year) && Number.isFinite(entry.lfpr));
}

export function getJulyYouthSeries() {
  const history = parseCsv(julyYouthHistoryCsv).map((row) => ({
    year: Number.parseInt(row.Year, 10),
    lfpr: parseNumber(row.Total),
  }));

  const current = parseCsv(julyYouthCsv).map((row) => ({
    year: Number.parseInt(row.Year, 10),
    lfpr: parseNumber(row.Total),
  }));

  const combined = new Map();
  for (const entry of [...history, ...current]) {
    if (Number.isFinite(entry.year) && Number.isFinite(entry.lfpr)) {
      combined.set(entry.year, entry);
    }
  }

  return [...combined.values()]
    .sort((left, right) => left.year - right.year)
    .map((entry) => ({
      year: entry.year,
      lfpr: entry.lfpr,
    }));
}

export function getCpiInsuranceSeries() {
  return parseCsv(cpiInsuranceCsv)
    .map((row) => ({
      year: Number.parseInt(row.Year, 10),
      allItems: parseNumber(row.AllItems),
      insurance: parseNumber(row.MotorVehicleInsurance),
      allItemsIndex1960: parseNumber(row.AllItemsIndex1960),
      insuranceIndex1960: parseNumber(row.MotorVehicleInsuranceIndex1960),
    }))
    .filter((entry) => Number.isFinite(entry.year) && Number.isFinite(entry.insurance));
}

export function getGasolineShockSeries() {
  return parseCsv(gasolineContextCsv)
    .map((row) => ({
      year: Number.parseInt(row.Year, 10),
      gasoline: parseNumber(row.LeadedRegularGasoline),
      gasolineIndex1978: parseNumber(row.GasolineIndex1978),
      youthJulLFPR: parseNumber(row.YouthJulLFPR),
      licensed18Share: parseNumber(row.Licensed18Share),
    }))
    .filter((entry) => Number.isFinite(entry.year) && Number.isFinite(entry.gasoline));
}
