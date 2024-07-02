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
        self.MAX_RETRIES = 3
        self.POLL_INTERVAL_SECONDS = 5
        self.LIMIT_ORDER_SPREAD = 0.002
        self.BASE_CURRENCY = 'USDT'
        self.TRADE_MAX_DURATION_MINUTES = 30

@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    in_price: float
    profit_price: float
    loss_price: float
    price_precision: int
    max_duration_mins: int = Config().TRADE_MAX_DURATION_MINUTES
    
@dataclass
class State:
    open_symbol: str = None
    

class Bot:
    def __init__(self, config: Config, binance: Client):
        self.config = config
        self.binance = binance
        self.state = State()
        
    def round_up_amount(self, symbol: str, amount: float) -> float:
        self.binance.get_symbol_info(symbol=symbol).get('filters')
    
    def close_positions(self):
        try:
            '''
            List and cancel all open orders. Try a few times to make sure all are closed.
            '''
            for attempt in range(self.config.MAX_RETRIES):
                if attempt > 0:
                    time.sleep(seconds=self.config.POLL_INTERVAL_SECONDS)
                open_orders = self.binance.get_open_margin_orders(symbol=self.state.open_symbol)
                for order in open_orders:
                    self.binance.cancel_margin_order(
                        symbol=self.state.open_symbol,
                        orderId=order.get('orderId'))
                
                
            assets = self.binance.get_margin_account().get('userAssets')
            for asset in assets:
                ticker = asset.get('asset')
                symbol = ticker + self.config.BASE_CURRENCY
                debt_qty = asset.get('borrowed') + asset.get('interest')
                if debt_qty > 0:
                    repay_order = self.binance.create_margin_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_MARKET,
                        timeInForce=TIME_IN_FORCE_GTC,
                        sideEffectType=AUTO_REPAY_TYPE,
                        quantity=self.round_up_amount(debt_qty))
                    self.complete_order(symbol=symbol, order_id=repay_order.get("orderId"))
                self.binance.transf


            
            self.state.open_symbol = None
        
        except Exception as e:
            print("Positions closing failed, need manual action.")

    
    def can_trade(self) -> bool:
        return True
    
    def get_best_trade(self) -> Trade | None:
        current_price = float(self.binance.get_symbol_ticker(symbol='ACHUSDT').get('price'))
        symbol_info = self.binance.get_symbol_info(symbol='ACHUSDT')
        print(symbol_info)
        return Trade()
    
    def get_price_str(self, price, precision):
        return "{:0.0{}f}".format(price, precision)

    def complete_order(self, symbol, order_id):
        for attempt in range(self.config.MAX_RETRIES):
            if attempt > 0:
                time.sleep(seconds=self.config.POLL_INTERVAL_SECONDS)
            order_status = self.binance.get_margin_order(
                symbol=symbol, 
                orderId=order_id).get('status')
            if order_status == ORDER_STATUS_FILLED:
                return        
        raise Exception("Order %s failed.", order_id)
        
    
    def order_long(self, trade: Trade):
        if trade.side != SIDE_BUY:
            raise Exception("Must be a BUY trade for LONG order.")
        
        '''
        There are a few caveats for BUY orders:
          - If you place order for X amount, it buys X - trading fee amout,
          so repay amount will be X - trading fee rounded to min tradeable precision
          - Anything else?
          - Will implement later
        '''
        
        raise Exception("Unimplemented.")
    
    def order_short(self, trade: Trade):
        if trade.side != SIDE_SELL:
            raise Exception("Must be a SELL trade for SHORT order.")
        
        try:
            '''
            Get into the SHORT SELL position with a limit order on ENTRY price
            '''
            order = self.binance.create_margin_order(
                symbol=trade.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                sideEffectType=MARGIN_BUY_TYPE,
                quantity=trade.quantity,
                price=self.get_price_str(trade.in_price, trade.price_precision))
            self.complete_order(symbol=trade.symbol, order_id=order.get("orderId"))
            
            '''
            Place a REPAY BUY limit order at minimum acceptable PROFIT price
            '''
            self.binance.create_margin_order(
                symbol=trade.symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                sideEffectType=AUTO_REPAY_TYPE,
                quantity=trade.quantity,
                price=self.get_price_str(trade.profit_price, trade.price_precision))
        
            '''
            Place a REPAY BUY stop-loss limit order at maximum acceptable LOSS price
            '''
            stop_loss_price = trade.loss_price * (1 - self.config.LIMIT_ORDER_SPREAD)
            self.binance.create_margin_order(
                symbol=trade.symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                sideEffectType=AUTO_REPAY_TYPE,
                quantity=trade.quantity,
                price=self.get_price_str(trade.loss_price, trade.price_precision),
                stopPrice=self.get_price_str(stop_loss_price, trade.price_precision))
        
        except Exception as e:
            print(e)
            self.close_positions()

    def trade(self, trade: Trade):
        self.state.open_symbol = trade.symbol
        
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
    
    binance.transfer_dust(asset='BCH', accountType='MARGIN')

main()
