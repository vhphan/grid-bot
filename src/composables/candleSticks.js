import {createChart, CrosshairMode} from "lightweight-charts";


async function barData(symbol, start, candleSeries, api) {
    let data;

    if (api === 'binance') {
        const barsUrl = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=5m&limit=500`;
        const r = await fetch(barsUrl);
        const klines = await r.json();
        data = klines.map(k => {
            return {
                time: k[0] / 1000,
                open: k[1],
                high: k[2],
                low: k[3],
                close: k[4],
            }
        });
    }

    if (api === 'alpaca') {

        const barsUrl =
            `https://data.alpaca.markets/v1beta1/crypto/${symbol}/bars?exchanges=CBSE&timeframe=5Min&start=${start}`;
        const apiKey = import.meta.env.VITE_API_KEY;
        const apiSecret = import.meta.env.VITE_API_SECRET;
        const r = await fetch(barsUrl, {
            headers: {
                "APCA-API-KEY-ID": apiKey,
                "APCA-API-SECRET-KEY": apiSecret,
            }
        });
        const response = await r.json();
        console.log(response);
        data = response.bars.map((bar) => ({
            open: bar.o,
            high: bar.h,
            low: bar.l,
            close: bar.c,
            time: Date.parse(bar.t) / 1000,
        }));
    }


    const currentBar = data[data.length - 1];
    console.log(data);
    candleSeries.setData(data);
    return currentBar;
}

export const useCandleChart = (symbol, apiDataProvider = 'alpaca') => {
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
        let currentBar = await barData(symbol, start, candleSeries, apiDataProvider);

        return {chart, candleSeries, currentBar};
    }
}

