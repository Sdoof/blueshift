# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 11:49:54 2018

@author: prodipta
"""

from blueshift.execution.backtester import BackTesterAPI 
from blueshift.trades.clocks import SimulationClock, RealtimeClock, BARS
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import BrokerType

class Algorithm(object):
    
    def __init__(self, *args, **kwargs):
        self.api = kwargs.get("broker",None)
        self.clock = kwargs.get("clock", None)
        self.calendar = kwargs.get("calendar", None)
        self.context = kwargs.get("context", None)
        
        
    def initialize(self, timestamp):
        print("initialize called at {}".format(timestamp))
    
    def before_trading_start(self,timestamp):
        print("before_trading_start called at {}".format(timestamp))
    
    def handle_data(self,timestamp):
        print("handle_data called at {}".format(timestamp))
    
    def after_trading_hours(self,timestamp):
        print("after_trading_hours called at {}".format(timestamp))
    
    def analyze(self,timestamp):
        print("analyze called at {}".format(timestamp))
        
    def heartbeat(self, timestamp):
        print("heartbeat called at {}".format(timestamp))
    
    def run(self):
        t1 = pd.Timestamp.now()
        for t, bar in self.clock:
            if bar == BARS.ALGO_START:
                self.initialize(t)
            elif bar == BARS.ALGO_END:
                self.analyze(t)
            elif bar == BARS.BEFORE_TRADING_START:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.before_trading_start(ts)
            elif bar == BARS.AFTER_TRADING_HOURS:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.after_trading_hours(ts)
            elif bar == BARS.TRADING_BAR:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.handle_data(ts)
                algo.api.login(ts)
            elif bar == BARS.HEAR_BEAT:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.heartbeat(ts)
                
        t2 = pd.Timestamp.now()
        elapsed_time = (t2-t1).total_seconds()*1000
        print("run complete in {} milliseconds".format(elapsed_time))
    
import pandas as pd
start_dt = pd.Timestamp('2010-01-01')
end_dt = pd.Timestamp('2018-10-04')
ist_cal = TradingCalendar('IST',tz='Asia/Calcutta',opens=(9,15,0), 
                          closes=(15,30,0))
clock = SimulationClock(ist_cal,1,start_dt,end_dt)
broker = BackTesterAPI('blueshift',BrokerType.BACKTESTER,ist_cal)

algo = Algorithm(clock=clock, calendar = ist_cal, broker=broker)
algo.run()

