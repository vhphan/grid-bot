import {createApp} from 'vue'
import {Notify, Quasar} from 'quasar'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'

// Import Quasar css
import 'quasar/src/css/index.sass'

// Assumes your root component is App.vue
// and placed in same folder as main.js
import App from './App.vue'

const myApp = createApp(App)

myApp.use(Quasar, {

    plugins: {
        Notify
    },
    config: {
        notify: { /* look at QuasarConfOptions from the API card */}
    }
})

// Assumes you have a <div id="app"></div> in your index.html
myApp.mount('#app')
