import {createChart, CrosshairMode} from "lightweight-charts";

export const useCandleChart = (symbol) => {
    return async function (chartRef, start) {
        const chart = createChart(chartRef, {
            width: 700,
            height: 250,
            layout: {
                backgroundColor: "#000000",
                textColor: "#ffffff",
            },
            grid: {
                vertLines: {
                    color: "#404040",
                },
                horzLines: {
                    color: "#404040",
                },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            priceScale: {
                borderColor: "#cccccc",
            },
            timeScale: {
                borderColor: "#cccccc",
                timeVisible: true,
            },
        });
        const candleSeries = chart.addCandlestickSeries();
        const barsUrl =
            `https://data.alpaca.markets/v1beta1/crypto/${symbol}/bars?exchanges=CBSE&timeframe=1Min&start=${start}`;
        const apiKey = import.meta.env.VITE_API_KEY
        const apiSecret = import.meta.env.VITE_API_SECRET
        let currentBar;
        const r = await fetch(barsUrl, {
            headers: {
                "APCA-API-KEY-ID": apiKey,
                "APCA-API-SECRET-KEY": apiSecret,
            }
        })
        const response = await r.json();
        const data = response.bars.map((bar) => ({
            open: bar.o,
            high: bar.h,
            low: bar.l,
            close: bar.c,
            time: Date.parse(bar.t) / 1000,
        }));
        currentBar = data[data.length - 1];
        console.log(data);
        candleSeries.setData(data);
        return {chart, candleSeries, currentBar};
    }
}