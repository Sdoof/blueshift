# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 11:49:54 2018

@author: prodipta
"""

from blueshift.execution.backtester import BackTesterAPI 
from blueshift.trades.clocks import SimulationClock, RealtimeClock, BARS
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import BrokerType
from blueshift.trades._order import Order
from blueshift.trades._order_types import OrderSide
from blueshift.assets.assets import (
        AssetDBConfiguration,
        AssetDBQueryEngineCSV,
        AssetFinder)

import random

class AlgoContext(object):
    pass

class Algorithm(object):
    
    def __init__(self, *args, **kwargs):
        self.api = kwargs.get("broker",None)
        self.clock = kwargs.get("clock", None)
        self.calendar = kwargs.get("calendar", None)
        self.context = kwargs.get("context", AlgoContext())
        self.asset_finder = kwargs.get("asset_finder", None)
        
        
    def initialize(self, timestamp):
        self.context.asset = self.asset_finder.lookup_symbol('NIFTY-I')
    
    def before_trading_start(self,timestamp):
        pass
    
    def handle_data(self,timestamp):
        qty = random.randint(-50,50)
        if qty == 0:
            return
        side = OrderSide.BUY if qty > 0 else OrderSide.SELL
        o = Order(abs(qty),side,self.context.asset)
        self.api.place_order(o)
    
    def after_trading_hours(self,timestamp):
        pass
    
    def analyze(self,timestamp):
        self.context.positions = self.api.positions()
        self.context.orders = self.api.orders()
        self.open_orders = self.api.open_orders()
        
        
    def heartbeat(self, timestamp):
        pass
    
    def run(self):
        t1 = pd.Timestamp.now()
        for t, bar in self.clock:
            if bar == BARS.ALGO_START:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.algo_start(ts)
                self.initialize(t)
            elif bar == BARS.ALGO_END:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.algo_end(ts)
                self.analyze(t)
            elif bar == BARS.BEFORE_TRADING_START:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.before_trading_start(ts)
                self.before_trading_start(ts)
            elif bar == BARS.AFTER_TRADING_HOURS:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.after_trading_hours(ts)
                self.after_trading_hours(ts)
            elif bar == BARS.TRADING_BAR:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.trading_bar(ts)
                self.handle_data(ts)
                #algo.api.login(ts)
            elif bar == BARS.HEAR_BEAT:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.hear_beat(ts)
                self.heartbeat(ts)
                
        t2 = pd.Timestamp.now()
        elapsed_time = (t2-t1).total_seconds()*1000
        print("run complete in {} milliseconds".format(elapsed_time))
    
import pandas as pd
start_dt = pd.Timestamp('2010-01-04')
end_dt = pd.Timestamp('2018-01-04')
ist_cal = TradingCalendar('IST',tz='Asia/Calcutta',opens=(9,15,0), 
                          closes=(15,30,0))
clock = SimulationClock(ist_cal,1,start_dt,end_dt)
broker = BackTesterAPI('blueshift',BrokerType.BACKTESTER,ist_cal)

asset_db_config = AssetDBConfiguration()
asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
asset_finder = AssetFinder(asset_db_query_engine)

algo = Algorithm(clock=clock, calendar = ist_cal, broker=broker,
                 asset_finder=asset_finder)
algo.run()

