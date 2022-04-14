import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import {quasar, transformAssetUrls} from '@quasar/vite-plugin'

// https://vitejs.dev/config/
export default defineConfig({
    server: {
        port: process.env.VITE_PORT || 3003,
    },
    plugins: [

        vue({
            template: {transformAssetUrls}
        }),

        quasar({
            sassVariables: 'src/quasar-variables.sass'
        }),
    ]
})
