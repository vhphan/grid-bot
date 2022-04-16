# Grid Bot using Python & Javascript

## Introduction
A grid bot using Python & Javascript. 
- Vue.js / Quasar framework used for the frontend ui.
- Market data uses the Binance REST and websocket API.
- References:
  - [Part Time Larry YouTube Playlist on Grid Bot](https://www.youtube.com/playlist?list=PLvzuUVysUFOtb2wF0gQ10_YD3ushEDtrd)

1) Install node packages
   - yarn install
2) Create python virtual environment. Install packages in requirements.txt
   - pip install -r requirements.txt
3) Create .env file using sample.env as a template. Enter your API keys and other settings here.
4) Start web socket server:
   - python -m server.ws_server:
5) Start grid bot:
   - python -m bot.grid_bot
6) Start web client:
   - yarn run dev
   
![Web UI Snapshot](snapshots/snapshot_web_ui.JPG)


