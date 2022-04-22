# %%
import json
import math
import sys
import time
from datetime import datetime as dt

import ccxt
import websocket
from dotenv import dotenv_values
from loguru import logger
from retry import retry

# %%
from bots.utils import read_last_n_lines

config = dotenv_values(".env")

NUM_BUY_GRID_LINES = int(config["NUM_BUY_GRID_LINES"])
SYMBOL = config["SYMBOL"]
QUOTE_SYMBOL = config["QUOTE_SYMBOL"]
POSITION_SIZE = float(config["POSITION_SIZE"])
GRID_SIZE = float(config["GRID_SIZE"])
NUM_SELL_GRID_LINES = int(config["NUM_SELL_GRID_LINES"])
API_KEY = config["BINANCE_API_KEY"]
API_SECRET = config["BINANCE_SECRET_KEY"]
CLOSED_ORDER_STATUS = config["ORDER_STATUS_FILLED"]
CHECK_ORDERS_FREQUENCY = int(config["CHECK_ORDERS_FREQUENCY"])


# initial_buy_order = exchange.create_market_buy_order(config.SYMBOL, config.POSITION_SIZE * config.NUM_SELL_GRID_LINES)


class GridBot:
    def __init__(self, web_socket_url=None):
        self.exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
        })
        self.exchange_info = self.exchange.fetch_markets()
        self.ticker = self.exchange.fetch_ticker(SYMBOL)
        self.balance = self.exchange.fetch_balance()
        self.quote_balance = self.balance[config['QUOTE_SYMBOL']]['total']
        self.base_balance = self.balance[config['BASE_SYMBOL']]['total']
        self.portfolio_value = self.quote_balance * self.ticker['last'] + self.base_balance
        self.buy_orders = []
        self.sell_orders = []
        self.closed_orders = []
        self.closed_order_ids = []
        self.errors = []
        self.initial_portfolio_value = self.portfolio_value
        if web_socket_url is not None:
            self.ws = websocket.WebSocket()
            self.ws.connect(web_socket_url)
        else:
            self.ws = None
        self.log_filename = f"logs/gridbot_{SYMBOL}_{dt.strftime(dt.now(), '%Y%m%d_%H%M%S')}.log"
        logger.add(f'{self.log_filename}', rotation='1 MB', level='DEBUG')
        logger.info(f"Starting GridBot for {SYMBOL}")
        self.min_notional = self.get_min_notional()

    def get_min_notional(self):
        try:
            filters = list(filter(lambda x: x['id'] == SYMBOL, self.exchange_info))[0]['info']['filters']
            min_notional = list(filter(lambda x: x['filterType'] == 'MIN_NOTIONAL', filters))[0]['minNotional']
            return min_notional
        except Exception as e:
            logger.error(f"Could not get min notional for {SYMBOL}")
            logger.error(e)
            raise e

    def get_portfolio_value(self):
        ticker = self.exchange.fetch_ticker(config['SYMBOL'])
        balance = self.exchange.fetch_balance()
        quote_balance = balance[config['BASE_SYMBOL']]['total']
        base_balance = balance[config['QUOTE_SYMBOL']]['total']
        return quote_balance * ticker['last'] + base_balance

    def cancel_all_orders(self):
        for order in self.buy_orders + self.sell_orders:
            self.exchange.cancel_order(order['id'], config['SYMBOL'])
            logger.info(f"Cancelled order {order['id']}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cancel_all_orders()

    @retry(tries=3, delay=1, logger=logger)
    def create_initial_order(self):
        if self.base_balance < POSITION_SIZE:
            logger.info(f"Insufficient funds to create initial order. Base balance: {self.base_balance}")
            sys.exit(1)

        current_price = self.exchange.fetch_ticker(SYMBOL)['last']
        if self.base_balance < NUM_SELL_GRID_LINES * POSITION_SIZE * current_price:
            shortage = NUM_SELL_GRID_LINES * POSITION_SIZE * self.exchange.fetch_ticker(SYMBOL)[
                'last'] - self.base_balance
            amount_to_buy = math.ceil(shortage / current_price)
            logger.info(f"Creating initial order for {amount_to_buy} {SYMBOL}")
            initial_order = self.exchange.create_market_buy_order(SYMBOL, amount_to_buy)
            logger.info(f"Initial order created. Order ID: {initial_order['id']}")

    def create_initial_grid_orders(self):
        for mode in ['buy', 'sell']:
            orders_list = self.buy_orders if mode == 'buy' else self.sell_orders
            grid_lines = NUM_BUY_GRID_LINES if mode == 'buy' else NUM_SELL_GRID_LINES
            grid_size_multiplier = -1 if mode == 'buy' else 1

            for i in range(1, grid_lines + 1):
                price = self.ticker['bid'] + grid_size_multiplier * GRID_SIZE * i
                try:

                    if mode == 'buy':
                        if POSITION_SIZE * price < float(self.min_notional):
                            logger.warning('POSITION_SIZE * price < min_notional')
                            logger.info(f"Skipping {mode} order for {price}")
                            continue

                    order = self.exchange.create_limit_order(SYMBOL, mode, POSITION_SIZE, price)
                    orders_list.append(order)
                    logger.info(f"Created {mode} order for {price}")

                except Exception as e:
                    logger.error(f"Invalid order: {e}")
                    raise e

    def get_kline(self):
        kline = self.exchange.fetch_ohlcv(SYMBOL, '1m')
        if self.ws:
            self.ws.send({'data': json.dumps(kline), 'type': 'kline'})
        return kline

    def run_bot(self):
        self.create_initial_order()
        self.create_initial_grid_orders()
        while True:
            if self.ws:
                # concatenate 3 order lists and send as jsonified string
                self.ws.send(json.dumps(
                    {'data': self.buy_orders + self.sell_orders + self.closed_orders,
                     'type': 'orders'})
                )
                log_lines = read_last_n_lines(self.log_filename, 20)
                print(log_lines)
                self.ws.send(json.dumps({'data': log_lines, 'type': 'logs'}))

            for mode in ['buy', 'sell']:

                grid_size_multiplier = 1 if mode == 'buy' else -1
                orders_list = self.buy_orders if mode == 'buy' else self.sell_orders

                for order in orders_list:

                    order = self.exchange.fetch_order(id=order['id'], symbol=SYMBOL)
                    logger.info('fetched order: ' + str(order))
                    order_info = order['info']
                    logger.info(f"Order info: {order_info}")

                    if order_info['status'] == CLOSED_ORDER_STATUS:
                        self.closed_orders.append(order_info)
                        self.closed_order_ids.append(order_info['id'])
                        logger.info(f"{mode} order executed at {order_info['price']}")

                        new_price = float(order_info['price']) + grid_size_multiplier * GRID_SIZE
                        logger.info(f"creating new limit {mode} order at {new_price}")
                        new_order_mode = 'buy' if mode == 'sell' else 'sell'
                        new_order = self.exchange.create_limit_order(SYMBOL, new_order_mode, POSITION_SIZE, new_price)
                        orders_list.append(new_order)

                    logger.info(f'Sleep for {CHECK_ORDERS_FREQUENCY} seconds')
                    time.sleep(CHECK_ORDERS_FREQUENCY)
                    logger.info(f"current portfolio value: {round(self.get_portfolio_value(), 3)} {QUOTE_SYMBOL}")

            for order_id in self.closed_order_ids:
                # self.buy_orders = list(filter(lambda order: order['id'] != order_id, self.buy_orders))
                # self.sell_orders = list(filter(lambda order: order['id'] != order_id, self.sell_orders))
                self.buy_orders = [buy_order for buy_order in self.buy_orders if buy_order['id'] != order_id]
                self.sell_orders = [sell_order for sell_order in self.sell_orders if sell_order['id'] != order_id]

            if len(self.sell_orders) == 0:
                logger.info(f"start portfolio value: {round(self.initial_portfolio_value, 3)} {QUOTE_SYMBOL}")
                logger.info(f"current portfolio value: {round(self.get_portfolio_value(), 3)} {QUOTE_SYMBOL}")
                logger.info(f"profit: {round(self.get_portfolio_value() - self.initial_portfolio_value, 3)} {QUOTE_SYMBOL}")
                # sys.exit("stopping bot, nothing left to sell")
                logger.info("stopping bot, nothing left to sell")
                self.__exit__(0, 0, None)


@retry(tries=3, delay=CHECK_ORDERS_FREQUENCY, logger=logger)
def fetch_order_info(self, order):
    return self.exchange.fetch_order(order['id'], config['SYMBOL'])


if __name__ == '__main__':
    web_socket_url = 'ws://localhost:9001'
    with GridBot(web_socket_url=web_socket_url) as bot:
        try:
            bot.run_bot()
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise e
