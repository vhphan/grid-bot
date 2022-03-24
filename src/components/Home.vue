<template>
  <q-splitter
      v-model="splitterModel"
      horizontal
      style="height: 100vh;"
  >

    <template v-slot:before>
      <div class="q-pa-md">
        <div class="text-h4 q-mb-md">Before</div>


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
import {computed, ref} from 'vue'

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

    const processData = (d) => {
      if (!d.T) return;
      const dataType = d.T;
      switch (dataType) {
        case 'q':
          const q = {time: d.t, bid: d.bp, ask: d.ap};
          quotes.value.push(q);
          if (quotes.value.length > 8) quotes.value.shift();
          break;
        case 't':
          const t = {time: d.t, price: d.p, size: d.s};
          trades.value.push(t);
          if (trades.value.length > 8) trades.value.shift();
          break;
        case 'b':
          bars.value.push(d);
          if (bars.value.length > 1000) bars.value.shift();
          break;
      }
    }


    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      const message = data[0]["msg"];

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


    return {
      splitterModel: ref(50),
      splitterModelLeftVertical: ref(50),
      quotes,
      trades,
      bars,
      latestBar,

    }
  }
}
</script>