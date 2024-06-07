import os
import math
import time
import traceback
from typing import Dict, Optional
from dotenv import load_dotenv

from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

# https://apscheduler.readthedocs.io/en/3.x/userguide.html#installing-apscheduler
from apscheduler.schedulers.blocking import BlockingScheduler


class Config:
    def __init__(self):
        load_dotenv()
        self.BINANCE_API_KEY = os.getenv("API_KEY")
        self.BINANCE_API_SECRET_KEY = os.getenv("API_SECRET_KEY")
        self.TRADING_FREQUENCY_MINUTES = 5


class Binance:
    def __init__(self, config: Config):
        self.binance_client = Client(
            config.BINANCE_API_KEY,
            config.BINANCE_API_SECRET_KEY,
        )
        self.config = config

    def retry(self, func, *args, **kwargs):
        for attempt in range(20):
            try:
                return func(*args, **kwargs)
            except Exception:
                if attempt != 0:
                    time.sleep(1)
        return None

    def get_trade_fees(self) -> Dict[str, float]:
        return {ticker["symbol"]: float(ticker["takerCommission"]) for ticker in self.binance_client.get_trade_fee()}

    def get_using_bnb_for_fees(self):
        return self.binance_client.get_bnb_burn_spot_margin()["spotBNBBurn"]

    def get_account(self):
        """
        Get account information
        """
        return self.binance_client.get_account()
    
    def fun(self):
        price = 0.0295
        precision = 4
        price_str = "{:0.0{}f}".format(price, precision)
        return price_str
        return self.binance_client.create_margin_order(
            symbol='NOTUSDT',
            side=SIDE_SELL,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=700,
            price=price_str)


class Bot:
    def __init__(self, config:Config, binance:Binance):
        self.config = config
        self.binance = binance

    def trade(self):
        print("Decorated job.")

    def run(self):
        scheduler = BlockingScheduler()
        scheduler.add_job(self.trade, 'interval', minutes=self.config.TRADING_FREQUENCY_MINUTES)
        scheduler.start()

def main():
    config = Config()
    binance = Binance(config)
    bot = Bot(config, binance)

    print(binance.fun())


main()
