# %%

import ccxt
from dotenv import dotenv_values
from loguru import logger

config = dotenv_values(".env")

NUM_BUY_GRID_LINES = int(config["NUM_BUY_GRID_LINES"])
SYMBOL = config["SYMBOL"]
POSITION_SIZE = float(config["POSITION_SIZE"])
GRID_SIZE = int(config["GRID_SIZE"])
NUM_SELL_GRID_LINES = int(config["NUM_SELL_GRID_LINES"])
API_KEY = config["BINANCE_API_KEY"]
API_SECRET = config["BINANCE_SECRET_KEY"]
CLOSED_ORDER_STATUS = config["CLOSED_ORDER_STATUS"]

# initial_buy_order = exchange.create_market_buy_order(config.SYMBOL, config.POSITION_SIZE * config.NUM_SELL_GRID_LINES)


class GridBot:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
        })
        self.ticker = self.exchange.fetch_ticker(SYMBOL)
        self.balance = self.exchange.fetch_balance()
        self.quote_balance = self.balance[config['BASE_SYMBOL']]['total']
        self.base_balance = self.balance[config['QUOTE_SYMBOL']]['total']
        self.portfolio_value = self.quote_balance * self.ticker['last'] + self.base_balance
        self.buy_orders = []
        self.sell_orders = []
        self.closed_order_ids = []

    def get_portfolio_value(self):
        ticker = self.exchange.fetch_ticker(config['SYMBOL'])
        balance = self.exchange.fetch_balance()
        quote_balance = balance[config['BASE_SYMBOL']]['total']
        base_balance = balance[config['QUOTE_SYMBOL']]['total']
        return quote_balance * ticker['last'] + base_balance

    def create_initial_orders(self):
        for mode in ['buy', 'sell']:
            orders_list = self.buy_orders if mode == 'buy' else self.sell_orders
            grid_lines = NUM_BUY_GRID_LINES if mode == 'buy' else NUM_SELL_GRID_LINES
            grid_size_multiplier = 1 if mode == 'buy' else -1
            for i in range(grid_lines, 1):
                price = self.ticker['bid'] + grid_size_multiplier * GRID_SIZE * i
                order = self.exchange.create_limit_order(SYMBOL, mode, POSITION_SIZE, price)
                orders_list.append(order)

    def run_bot(self):
        self.create_initial_orders()
        while True:
            for mode in ['buy', 'sell']:
                orders_list = self.buy_orders if mode == 'buy' else self.sell_orders
                for order in orders_list:
                    order = self.exchange.fetch_order(order['id'], config['SYMBOL'])
                    order_info = order['info']
                    if order_info['status'] == CLOSED_ORDER_STATUS:
                        self.closed_order_ids.append(order_info['id'])
                        logger.info(f"buy order executed at {order_info['price']}")
