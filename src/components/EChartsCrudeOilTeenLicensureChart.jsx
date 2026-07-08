import React, { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { getCrudeOilPriceSeries, getYouthShareSeries } from "../data/licensedDrivers";

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

const START_YEAR = 1963;
const END_YEAR = 2024;

const SERIES_COLORS = {
  oil: "#244A71",
  teenLicensure: "#A07800",
};

function buildChartData() {
  const oil = new Map(getCrudeOilPriceSeries().map((row) => [row.year, row.price]));
  const teenLicensure = new Map(getYouthShareSeries().map((row) => [row.year, row.share]));

  return Array.from({ length: END_YEAR - START_YEAR + 1 }, (_, offset) => {
    const year = START_YEAR + offset;

    return {
      year,
      oilPrice: oil.get(year) ?? null,
      teenLicensure: teenLicensure.get(year) ?? null,
    };
  }).filter((row) => Number.isFinite(row.oilPrice) && Number.isFinite(row.teenLicensure));
}

function formatOil(value) {
  if (!Number.isFinite(value)) return "";
  return `$${value.toFixed(2)} / barrel`;
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "";
  return `${value.toFixed(1)}%`;
}

export default function EChartsCrudeOilTeenLicensureChart() {
  const chartRef = useRef(null);
  const chartData = useMemo(buildChartData, []);

  useEffect(() => {
    if (!chartRef.current) return undefined;

    const chart = echarts.init(chartRef.current, null, {
      renderer: "canvas",
    });

    chart.setOption({
      backgroundColor: "#ffffff",
      color: [SERIES_COLORS.oil, SERIES_COLORS.teenLicensure],
      grid: {
        left: 66,
        right: 66,
        top: 56,
        bottom: 82,
        containLabel: false,
      },
      legend: {
        bottom: 10,
        left: 66,
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
        axisPointer: { type: "line" },
        backgroundColor: "rgba(255,255,255,0.98)",
        borderColor: "rgba(23,32,51,0.14)",
        borderWidth: 1,
        textStyle: { color: "#101828" },
        formatter(params) {
          const items = Array.isArray(params) ? params : [params];
          const year = items[0]?.axisValue ?? "";
          const rows = items
            .filter((item) => item.value != null)
            .map((item) => {
              const value = Number(item.value);
              const formatted = item.seriesName === "Teen licensure" ? formatPercent(value) : formatOil(value);
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
          name: "Crude oil price ($/barrel)",
          min: 0,
          max: 100,
          interval: 20,
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
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: "Crude oil price",
          type: "line",
          data: chartData.map((row) => row.oilPrice),
          symbol: "none",
          lineStyle: { width: 3 },
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
    });

    const resize = () => chart.resize();
    const observer = new ResizeObserver(resize);
    observer.observe(chartRef.current);
    window.addEventListener("resize", resize);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [chartData]);

  return <div ref={chartRef} className="echarts-driving-costs" aria-label="Crude oil price and teen licensure chart" />;
}
