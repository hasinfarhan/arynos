import os
import math
import time
import traceback
from typing import Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# https://python-binance.readthedocs.io/en/latest
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
        self.DEFAULT_PRICE_PRECISION = 6

@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    in_price: float
    profit_price: float
    loss_price: float
    max_duration_mins: int

class Bot:
    def __init__(self, config: Config, binance: Client):
        self.config = config
        self.binance = binance
        
    def retry(self, func, *args, **kwargs):
        for attempt in range(20):
            try:
                return func(*args, **kwargs)
            except Exception:
                if attempt != 0:
                    time.sleep(1)
        return None
    
    def close_positions(self):
        print("todo")
    
    def can_trade(self) -> bool:
        return True
    
    def get_best_trade(self) -> Trade | None:
        return Trade()
    
    def get_price_str(self, price):
        return "{:0.0{}f}".format(price, self.config.DEFAULT_PRICE_PRECISION)
    
    def order_long(self, trade: Trade):
        if trade.side != SIDE_BUY:
            raise Exception("Must be a BUY trade for LONG order.")
        
        self.binance.create_margin_order(
            symbol=trade.symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType=MARGIN_BUY_TYPE,
            quantity=trade.quantity,
            price=self.get_price_str(trade.in_price))
        
        self.binance.create_margin_order(
            symbol=trade.symbol,
            side=self.reverse_side(trade.side),
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType=AUTO_REPAY_TYPE,
            quantity=trade.quantity,
            price=self.get_price_str(trade.profit_price))
        
        
        return self.binance.create_margin_order(
            symbol=trade.symbol,
            side=self.reverse_side(trade.side),
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType=AUTO_REPAY_TYPE,
            quantity=trade.quantity,
            price=self.get_price_str(trade.loss_price))
    
    def order_short(self, trade: Trade) -> bool:
        if trade.side != SIDE_SELL:
            raise Exception("Must be a SELL trade for SHORT order.")
        
        try:
            self.binance.create_margin_order(
                symbol=trade.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                sideEffectType=MARGIN_BUY_TYPE,
                quantity=trade.quantity,
                price=self.get_price_str(trade.in_price))
            
            self.binance.create_margin_order(
                symbol=trade.symbol,
                side=self.reverse_side(trade.side),
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                sideEffectType=AUTO_REPAY_TYPE,
                quantity=trade.quantity,
                price=self.get_price_str(trade.profit_price))
        
        
            self.binance.create_margin_order(
                symbol=trade.symbol,
                side=self.reverse_side(trade.side),
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                sideEffectType=AUTO_REPAY_TYPE,
                quantity=trade.quantity,
                price=self.get_price_str(trade.loss_price))
        
        except Exception:
            self.close_positions()
            return False

    def trade(self, trade: Trade):
        if trade.side == SIDE_BUY:
            self.order_long(trade)
        elif trade.side == SIDE_SELL:
            self.order_short(trade)
        else:
            raise Exception("Trade side should be BUY/SELL, but given " + trade.side)

    def step(self):
        if self.can_trade():
            best_trade = self.get_best_trade()
            if best_trade is not None:
                self.trade(trade=best_trade)

    def run(self):
        scheduler = BlockingScheduler()
        scheduler.add_job(self.step, 'interval', minutes=self.config.TRADING_FREQUENCY_MINUTES)
        scheduler.start()

def main():
    config = Config()
    binance = Client(
        config.BINANCE_API_KEY,
        config.BINANCE_API_SECRET_KEY,
    )
    bot = Bot(config, binance)
    
    # print(binance.get_margin_symbol(symbol='ACHUSDT'))
    # print("\n")
    # print(binance.get_symbol_info(symbol='BTCUSDT').get('filters'))
    # print("\n")
    # print(binance.get_symbol_ticker(symbol='ACHUSDT'))
    
    assets = binance.get_margin_account().get('userAssets')
    for asset in assets:
        if asset.get('asset') == 'ACH':
            print(asset)
            return
    
    # return binance.create_margin_order(
    #         symbol='ACHUSDT',
    #         side=SIDE_BUY,
    #         type=ORDER_TYPE_LIMIT,
    #         timeInForce=TIME_IN_FORCE_GTC,
    #         sideEffectType=MARGIN_BUY_TYPE,
    #         quantity=500,
    #         price=bot.get_price_str(0.0272))
    # return binance.create_margin_order(
    #         symbol='ACHUSDT', 
    #         side=SIDE_SELL,
    #         type=ORDER_TYPE_STOP_LOSS_LIMIT,
    #         timeInForce=TIME_IN_FORCE_GTC,
    #         sideEffectType=AUTO_REPAY_TYPE,
    #         quantity=499,
    #         price=bot.get_price_str(0.025),
    #         stopPrice=bot.get_price_str(0.024))

print(main())
