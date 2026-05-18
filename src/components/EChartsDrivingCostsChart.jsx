import React, { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts/core";
import {
  LineChart,
} from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import {
  getCpiInsuranceSeries,
  getGasolineShockSeries,
  getYouthShareSeries,
} from "../data/licensedDrivers";

echarts.use([
  LineChart,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  TooltipComponent,
  CanvasRenderer,
]);

const START_YEAR = 1963;
const END_YEAR = 2024;

const SERIES_COLORS = {
  insurance: "#C65A6A",
  gasoline: "#244A71",
  teenLicensure: "#A07800",
};

function indexToBase(value, baseValue) {
  return (value / baseValue) * 100;
}

function buildChartData() {
  const licensure = new Map(getYouthShareSeries().map((row) => [row.year, row.share]));
  const insurance = new Map(getCpiInsuranceSeries().map((row) => [row.year, row.insurance]));
  const gasoline = new Map(getGasolineShockSeries().map((row) => [row.year, row.gasoline]));

  const baseYearValues = {
    teenLicensure: licensure.get(START_YEAR),
    insurance: insurance.get(START_YEAR),
    gasoline: gasoline.get(START_YEAR),
  };

  return Array.from({ length: END_YEAR - START_YEAR + 1 }, (_, offset) => {
    const year = START_YEAR + offset;
    const teenLicensure = licensure.get(year);
    const insuranceValue = insurance.get(year);
    const gasolineValue = gasoline.get(year);

    return {
      year,
      insurance:
        Number.isFinite(insuranceValue) && Number.isFinite(baseYearValues.insurance)
          ? indexToBase(insuranceValue, baseYearValues.insurance)
          : null,
      gasoline:
        Number.isFinite(gasolineValue) && Number.isFinite(baseYearValues.gasoline)
          ? indexToBase(gasolineValue, baseYearValues.gasoline)
          : null,
      teenLicensure: Number.isFinite(teenLicensure) ? teenLicensure : null,
    };
  });
}

function formatIndex(value) {
  if (!Number.isFinite(value)) return "";
  return value >= 1000 ? Math.round(value).toLocaleString("en-US") : value.toFixed(0);
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "";
  return `${value.toFixed(1)}%`;
}

export default function EChartsDrivingCostsChart() {
  const chartRef = useRef(null);
  const chartData = useMemo(buildChartData, []);

  useEffect(() => {
    if (!chartRef.current) return undefined;

    const chart = echarts.init(chartRef.current, null, {
      renderer: "canvas",
    });
    const option = {
      backgroundColor: "#ffffff",
      color: [SERIES_COLORS.insurance, SERIES_COLORS.gasoline, SERIES_COLORS.teenLicensure],
      grid: {
        left: 66,
        right: 66,
        top: 72,
        bottom: 52,
        containLabel: false,
      },
      legend: {
        top: 18,
        left: 8,
        itemGap: 18,
        icon: "roundRect",
        textStyle: {
          color: "#475467",
          fontSize: 12,
          fontWeight: 600,
        },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "line",
        },
        backgroundColor: "rgba(255,255,255,0.98)",
        borderColor: "rgba(23,32,51,0.14)",
        borderWidth: 1,
        textStyle: {
          color: "#101828",
        },
        formatter(params) {
          const items = Array.isArray(params) ? params : [params];
          const year = items[0]?.axisValue ?? "";
          const rows = items
            .filter((item) => item.value != null)
            .map((item) => {
              const value = Number(item.value);
              const formatted =
                item.seriesName === "Teen licensure"
                  ? formatPercent(value)
                  : formatIndex(value);
              return `<div style="display:flex;justify-content:space-between;gap:14px;align-items:center;margin-top:6px;">
                <span style="display:inline-flex;align-items:center;gap:8px;color:#475467;">
                  <span style="width:10px;height:10px;border-radius:999px;background:${item.color};display:inline-block;"></span>
                  ${item.seriesName}
                </span>
                <strong style="font-variant-numeric:tabular-nums;color:#101828;">${formatted}</strong>
              </div>`;
            })
            .join("");

          return `<div style="min-width:220px;">
            <div style="font-size:12px;font-weight:700;color:#475467;">${year}</div>
            ${rows}
          </div>`;
        },
      },
      toolbox: {
        right: 0,
        top: 8,
        feature: {
          saveAsImage: {
            title: "Download PNG",
            name: "teen-driving-costs-1963-2024",
            backgroundColor: "#ffffff",
            pixelRatio: 2,
          },
        },
        iconStyle: {
          borderColor: "#667085",
        },
        emphasis: {
          iconStyle: {
            borderColor: "#101828",
          },
        },
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: chartData.map((row) => row.year),
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "rgba(23,32,51,0.16)" } },
        axisLabel: {
          color: "#667085",
          margin: 14,
          interval: 4,
        },
      },
      yAxis: [
        {
          type: "value",
          name: "Index (1963 = 100)",
          min: 50,
          max: 3500,
          interval: 500,
          axisLabel: {
            color: "#667085",
            formatter: (value) => `${value}`,
          },
          nameTextStyle: {
            color: "#667085",
            fontWeight: 600,
            padding: [0, 0, 0, 10],
          },
          splitLine: {
            lineStyle: {
              color: "rgba(23,32,51,0.1)",
            },
          },
        },
        {
          type: "value",
          name: "Teen licensure share",
          min: 0,
          max: 8,
          interval: 2,
          axisLabel: {
            color: "#667085",
            formatter: (value) => `${value}%`,
          },
          nameTextStyle: {
            color: "#667085",
            fontWeight: 600,
            padding: [0, 10, 0, 0],
          },
          splitLine: {
            show: false,
          },
        },
      ],
      series: [
        {
          name: "Motor vehicle insurance",
          type: "line",
          data: chartData.map((row) => row.insurance),
          symbol: "none",
          lineStyle: { width: 3 },
          emphasis: { focus: "series" },
        },
        {
          name: "Gasoline",
          type: "line",
          data: chartData.map((row) => row.gasoline),
          symbol: "none",
          lineStyle: { width: 2.5 },
          emphasis: { focus: "series" },
        },
        {
          name: "Teen licensure",
          type: "line",
          yAxisIndex: 1,
          data: chartData.map((row) => row.teenLicensure),
          symbol: "none",
          lineStyle: { width: 3 },
          emphasis: { focus: "series" },
        },
      ],
    };

    chart.setOption(option);

    const resizeChart = () => {
      chart.resize();
    };

    const observer = new ResizeObserver(() => {
      chart.resize();
    });
    observer.observe(chartRef.current);
    window.addEventListener("resize", resizeChart);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", resizeChart);
      chart.dispose();
    };
  }, [chartData]);

  return <div ref={chartRef} className="echarts-driving-costs" aria-label="Teen licensure and driving costs chart" />;
}
