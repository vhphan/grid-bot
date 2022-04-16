<template>
  <q-splitter
      v-model="sideModel"
      width="300"
      min-width="300"
      max-width="300"
      style="background-color: #f0f0f0;">
    <template v-slot:before>
      <q-splitter
          v-model="splitterModel"
          horizontal
          style="height: 100vh;"
      >


        <template v-slot:before>
          <q-resize-observer @resize="onResize"/>
          <div class="q-pa-md full-width full-height" style="" ref="chartContainer">
            <div class="text-h4" ref="chartRef">
            </div>
          </div>
        </template>

        <template v-slot:after>
          <div class="q-pa-md">
            <q-splitter
                v-model="splitterModelLeftVertical"

                style="height: 40vh;"
            >
              <template v-slot:before>

                <q-table
                    title="Quotes"
                    :rows="quotes.slice(-numOfRows)"
                    :pagination="{rowsPerPage: numOfRows}"
                    dense
                    dark
                    :hide-bottom="true"
                ></q-table>

              </template>
              <template v-slot:after>
                <q-table
                    title="Trades"
                    :rows="trades.slice(-numOfRows)"
                    :pagination="{rowsPerPage: numOfRows}"
                    dense
                    dark
                    :hide-bottom="true"
                ></q-table>

              </template>
            </q-splitter>

          </div>
        </template>


      </q-splitter>

    </template>
    <template v-slot:after>

      <q-table
          title="Open Orders"
          :rows="openOrders.slice(-numOfRows)"
          :pagination="{rowsPerPage: numOfRows}"
          dense
          dark
          class="q-ma-xs"
      >
        <template v-slot:body="props">
          <q-tr :props="props" :class="(props.row.side==='buy')?'bg-black text-green':'bg-black text-red'">


            <q-td key="id" :props="props">
              {{ props.row.id }}
            </q-td>

            <q-td key="side" :props="props">
              {{ props.row.side }}
            </q-td>

            <q-td key="price" :props="props">
              {{ props.row.price }}
            </q-td>

            <q-td key="status" :props="props">
              {{ props.row.status }}
            </q-td>
          </q-tr>
        </template>

      </q-table>
      <q-table
          title="Closed Orders"
          :rows="closedOrders.slice(-numOfRows)"
          :pagination="{rowsPerPage: numOfRows}"
          dense
          dark
          class="q-ma-xs"
      ></q-table>

      <q-separator/>

      <div style="height: 390px; display: flex; flex-direction: column-reverse;" class="list scroll">
        <q-list
            dense
            class="q-ma-xs bg-black"
            bordered
            dark
        >
          <q-item-section class="text-h6 bg-blue-9" style="position: sticky; top:0; z-index: 10;">Bot Logs</q-item-section>
          <q-separator dark/>
          <q-item v-for="item in logList.slice(-numOfRows)">
            {{ item }}
          </q-item>
        </q-list>
      </div>

    </template>

  </q-splitter>
</template>

<script>
import {computed, onMounted, ref} from 'vue'
import {LineStyle} from "lightweight-charts";
import {useCandleChart} from "../composables/candleSticks";
import {useQuasar} from "quasar";
import {useAlpaca, useBinance} from "../composables/marketDataSockets";

export default {
  name: 'Home',
  setup() {
    const symbol = import.meta.env.VITE_SYMBOL;
    const $q = useQuasar();
    const numOfRows = ref(10);

    // const {quotes, trades, bars, createSocket} = useAlpaca(symbol);
    const {quotes, trades, bars, createSocket} = useBinance(symbol.toLowerCase());

    const latestBar = computed(() => bars.value[bars.value.length - 1]);
    const chartRef = ref(null);
    const chartContainer = ref(null);
    const start = new Date(Date.now() - 7200 * 1000).toISOString();
    const myCandleChart = useCandleChart(symbol, 'binance');

    let chart, candleSeries, currentBar;

    const onResize = (size) => {
      console.log(size);
      if (!chart) return;
      chart.resize(size.width - 40, size.height - 40);
    }

    const priceLines = [];
    const openOrders = ref([]);
    const closedOrders = ref([]);
    const logData = ref([]);
    let orderSocket;

    function processOrderData(order) {
      const {id, side, price, status, fee} = order;
      console.log({id, side, price, status});

      if (status === 'closed') {
        closedOrders.value.push({id, side, price, status});
      } else {
        openOrders.value.push({id, side, price, status});
        let priceLine = {
          price: order.price,
          color: side === 'buy' ? '#00ff00' : '#ff0000',
          lineWidth: 2,
          lineVisible: true,
          lineStyle: LineStyle.Solid,
          axisLabelVisible: true,
          title: order.side
        };
        console.log(candleSeries);
        let line = candleSeries.createPriceLine(priceLine);
        priceLines.push(line);
      }
    }

    const createOrderSocket = function () {
      orderSocket = new WebSocket("ws://localhost:9001");
      orderSocket.onopen = () => {
        console.log("order socket connected");
      };

      orderSocket.onclose = () => {
        orderSocket = null;
        $q.notify({
          message: 'Order socket closed',
          color: 'red',
          icon: 'error',
          position: 'top',
          timeout: 2000
        })
      };

      orderSocket.onmessage = function (event) {
        try {
          console.log(event);
          let socketData = JSON.parse(event.data);
          if (socketData.type === 'orders') {
            const orderData = socketData.data;
            priceLines.forEach(priceLine => candleSeries.removePriceLine(priceLine));
            openOrders.value = [];
            closedOrders.value = [];
            orderData.forEach(order => {
              processOrderData(order);
            });

          }

          if (socketData.type === 'logs') {
            logData.value = socketData.data;
            console.log(logData.value);
          }
        } catch (e) {
          console.log(e);
          console.log(event.data);

          $q.notify({
            message: 'Error processing order socket data.',
            color: 'red',
            icon: 'error',
            position: 'top',
            timeout: 2000
          })
        }
      }
    };


    onMounted(async () => {

      const obj = await myCandleChart(chartRef.value, start);
      chart = obj.chart;
      candleSeries = obj.candleSeries;
      currentBar = obj.currentBar;

      let marketSocket = createSocket(candleSeries, currentBar);

      console.log(marketSocket);
      try {
        createOrderSocket()
      } catch (e) {
        console.log(e);
        $q.notify({
          message: 'Error creating order socket',
          color: 'red',
          icon: 'error',
          position: 'top',
          timeout: 2000
        })
      }
      if (chart) {
        chart.resize(chartContainer.value.offsetWidth - 40, chartContainer.value.offsetHeight - 40);
      }
    })

    return {
      numOfRows,
      sideModel: ref(70),
      splitterModel: ref(50),
      splitterModelLeftVertical: ref(50),
      quotes,
      trades,
      bars,
      latestBar,
      chartRef,
      onResize,
      chartContainer,
      closedOrders,
      openOrders,
      logList: logData,
    }
  }
}
</script>