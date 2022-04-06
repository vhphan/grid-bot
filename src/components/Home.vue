<template>
  <q-splitter
      v-model="splitterModel"
      horizontal
      style="height: 100vh;"
  >

    <template v-slot:before >
      <q-resize-observer @resize="onResize"/>
      <div class="q-pa-md full-width full-height" style="" ref="chartContainer">
        <div class="text-h4 q-mb-md" ref="chartRef">
        </div>
      </div>
    </template>

    <template v-slot:after>
      <div class="q-pa-md">
        <q-splitter
            v-model="splitterModelLeftVertical"

            style="height: 90vh;"
        >
          <template v-slot:before>

            <q-table
                :rows="quotes"
                :pagination="{rowsPerPage: 8}"
                dense
                dark
            ></q-table>

          </template>
          <template v-slot:after>
            <q-table
                :rows="trades"
                :pagination="{rowsPerPage: 8}"
                dense
                dark
            ></q-table>

          </template>
        </q-splitter>

      </div>
    </template>

  </q-splitter>
</template>


<script>
import {computed, onMounted, ref, watch} from 'vue'
import {createChart, CrosshairMode} from "lightweight-charts";
import {useCandleChart} from "../composables/candleSticks";

export default {
  name: 'Home',
  setup() {

    const apiKey = import.meta.env.VITE_API_KEY
    const apiSecret = import.meta.env.VITE_API_SECRET

    const auth = {"action": "auth", "key": apiKey, "secret": apiSecret};
    const subscribe = {"action": "subscribe", "trades": ["ETHUSD"], "quotes": ["ETHUSD"], "bars": ["ETHUSD"]}
    const url = "wss://stream.data.alpaca.markets/v1beta1/crypto";
    const socket = new WebSocket(url);

    const quotes = ref([]);
    const trades = ref([]);
    const bars = ref([]);
    const latestBar = computed(() => bars.value[bars.value.length - 1]);

    const chartRef = ref(null);
    const chartContainer = ref(null);
    const start = new Date(Date.now() - 7200 * 1000).toISOString();
    const myCandleChart = useCandleChart();

    let chart, candleSeries, currentBar;

    onMounted(async () => {

      const obj = await myCandleChart(chartRef.value, start);
      chart = obj.chart;
      candleSeries = obj.candleSeries;
      currentBar = obj.currentBar;


      socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const message = data[0]["msg"];
        console.log(message);
        data.forEach(d => {
          processData(d);
        })

        if (message === "connected") {
          console.log("do authentication");
          socket.send(JSON.stringify(auth));
        }

        if (message === "authenticated") {
          socket.send(JSON.stringify(subscribe));
        }
      }

      if (chart) {
        chart.resize(chartContainer.value.offsetWidth, chartContainer.value.offsetHeight - 40);
      }

      // setTimeout(() => {
      //   console.log(chartContainer.value.offsetWidth);
      //   chart.resize(chartContainer.value.offsetWidth, chartContainer.value.offsetHeight - 40);
      // }, 5000);

    })



    const processData = (bar) => {
      if (!bar.T) return;
      const dataType = bar.T;
      switch (dataType) {
        case 'q':
          const q = {time: bar.t, bid: bar.bp, ask: bar.ap};
          quotes.value.push(q);
          if (quotes.value.length > 8) quotes.value.shift();
          break;
        case 't':
          const t = {time: bar.t, price: bar.p, size: bar.s};
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
          bars.value.push(bar);
          if (bars.value.length > 1000) bars.value.shift();

          const timestamp = new Date(bar.t).getTime() / 1000;

          currentBar = {
            time: timestamp,
            open: bar.o,
            high: bar.h,
            low: bar.l,
            close: bar.c,
          };

          candleSeries.update(currentBar);
          trades.value = [];

          break;
      }
    }

    const onResize = (size) => {
      console.log(size);
      if (!chart) return;
      chart.resize(size.width, size.height - 40);
    }

    return {
      splitterModel: ref(50),
      splitterModelLeftVertical: ref(50),
      quotes,
      trades,
      bars,
      latestBar,
      chartRef,
      onResize,
      chartContainer

    }
  }
}
</script>