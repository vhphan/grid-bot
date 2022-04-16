import {ref} from "vue";

export const zipArrays = function (a, b) {
    return a.map(function (e, i) {
        return [e, b[i]];
    });
};

export const useAlpaca = function (symbol) {

    const apiKey = import.meta.env.VITE_API_KEY
    const apiSecret = import.meta.env.VITE_API_SECRET

    const url = "wss://stream.data.alpaca.markets/v1beta1/crypto";
    const auth = {"action": "auth", "key": apiKey, "secret": apiSecret};
    const subscribe = {"action": "subscribe", "trades": [symbol], "quotes": [symbol], "bars": [symbol]}

    const quotes = ref([]);
    const trades = ref([]);
    const bars = ref([]);
    const createSocket = function (candleSeries, currentBar) {
        const processData = (dataElement) => {
            if (!dataElement.T) return;
            const dataType = dataElement.T;
            switch (dataType) {
                case 'q':
                    const q = {time: dataElement.t, bid: dataElement.bp, ask: dataElement.ap};
                    quotes.value.push(q);
                    if (quotes.value.length > 8) quotes.value.shift();
                    break;
                case 't':
                    const t = {time: dataElement.t, price: dataElement.p, size: dataElement.s};
                    trades.value.push(t.price);
                    if (trades.value.length > 8) trades.value.shift();

                    let open = trades.value[0];
                    let high = Math.max(...trades.value);
                    let low = Math.min(...trades.value);
                    let close = trades.value[trades.value.length - 1];

                    candleSeries.update({
                        time: currentBar.time + 60,
                        open: open,
                        high: high,
                        low: low,
                        close: close,
                    });
                    break;

                case 'b':
                    bars.value.push(dataElement);
                    if (bars.value.length > 1000) bars.value.shift();

                    const timestamp = new Date(dataElement.t).getTime() / 1000;

                    currentBar = {
                        time: timestamp,
                        open: dataElement.o,
                        high: dataElement.h,
                        low: dataElement.l,
                        close: dataElement.c,
                    };

                    candleSeries.update(currentBar);
                    trades.value = [];

                    break;
            }
        };
        let marketDataSocket = new WebSocket(url);

        marketDataSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            const message = data[0]["msg"];

            data.forEach(d => {
                processData(d);
            });

            if (message === 'auth timeout') {
                $q.notify({
                    message: 'Authentication timeout. Retrying in 5 sec...',
                    color: 'negative',
                    icon: 'error',
                    position: 'top'
                })

            }

            if (message === "connected") {
                $q.notify({
                    message: 'Data Streaming socket is connected....',
                    color: 'positive',
                    icon: 'done',
                    position: 'top'
                })

                console.log("do authentication");
                marketDataSocket.send(JSON.stringify(auth));
            }

            if (message === "authenticated") {
                $q.notify({
                    message: 'Socket is authenticated....',
                    color: 'positive',
                    icon: 'done',
                    position: 'top'
                })
                marketDataSocket.send(JSON.stringify(subscribe));
            }
        }
        marketDataSocket.onclose = () => {
            marketDataSocket = null;
            $q.notify({
                message: 'Data streaming socket closed',
                color: 'red',
                icon: 'error',
                position: 'top',
                timeout: 2000
            })
            setTimeout(createSocket, 300_000)
        };

        //   for testing purposes
        setTimeout(() => {
            marketDataSocket.close();
        }, 120_000)

    };
    return {quotes, trades, bars, createSocket};
};

export const useBinance = function (symbol) {
    const tzOffset = (new Date()).getTimezoneOffset() * 60_000;

    const url = 'wss://stream.binance.com:9443';
    const streams = `ws/${symbol}@kline_5m/${symbol}@trade/${symbol}@depth@1000ms`;
    const quotes = ref([]);
    const trades = ref([]);
    const bars = ref([]);
    const createSocket = function (candleSeries, currentBar) {

        let marketDataSocket = new WebSocket(url + '/' + streams);
        marketDataSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            const messageType = data.e;
            switch (messageType) {
                case 'kline':
                    const bar = {
                        t: data.k.t - tzOffset,
                        o: data.k.o,
                        h: data.k.h,
                        l: data.k.l,
                        c: data.k.c,
                        v: data.k.v,
                    };
                    bars.value.push(bar);
                    if (bars.value.length > 1000) bars.value.shift();

                    const timestamp = bar.t / 1000 ;

                    currentBar = {
                        time: timestamp,
                        open: bar.o,
                        high: bar.h,
                        low: bar.l,
                        close: bar.c,
                    };

                    candleSeries.update(currentBar);
                    break;

                case 'trade':
                    const trade = {
                        time: new Date(parseFloat(data.T)).toLocaleString(),
                        price: data.p,
                        quantity: data.q,
                    };
                    trades.value.push(trade);
                    if (trades.value.length > 1000) trades.value.shift();
                    break;

                case 'depthUpdate':

                    if (!data.b && !data.a) break;
                    if (!data.b.length && !data.a.length) break;

                    let bidsArray = data.b.map(bid => {
                        return {
                            bid: bid[0],
                            bidSize: parseFloat(bid[1]).toFixed(3),
                        };
                    });
                    let asksArray = data.a.map(ask => {
                        return {
                            ask: ask[0],
                            askSize: parseFloat(ask[1]).toFixed(3),
                        }
                    });
                    let maxArrayLength = Math.max(bidsArray.length, asksArray.length);

                    for (let i = 0; i < maxArrayLength; i++) {
                        if (bidsArray[i]) {
                            quotes.value.push({
                                time: new Date(parseFloat(data.E)).toLocaleString(),
                                bid: bidsArray[i]?.bid,
                                bidSize: bidsArray[i]?.bidSize,
                                ask: asksArray[i]?.ask,
                                askSize: asksArray[i]?.askSize,
                            });
                        }
                    }
                    while (quotes.value.length > 1000) {
                        quotes.value.shift();
                    }
                    break;
            }
        };

        return marketDataSocket;
    }
    return {quotes, trades, bars, createSocket};
};