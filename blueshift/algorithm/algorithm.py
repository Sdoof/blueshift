# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 11:49:54 2018

@author: prodipta
"""
from enum import Enum
import os
import pandas as pd
from functools import partial

import blueshift.algorithm.api
from blueshift.algorithm.context import AlgoContext
from blueshift.utils.cutils import check_input
from blueshift.execution.backtester import BackTesterAPI 
from blueshift.execution._clock import SimulationClock, BARS
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import BrokerType
from blueshift.trades._order import Order
from blueshift.trades._order_types import OrderSide

from blueshift.utils.exceptions import (
        StateMachineError,
        APIValidationError,
        InitializationError)

import random

class MODE(Enum):
    BACKTEST = 0
    LIVE = 1
    
class STATE(Enum):
    STARTUP = 0
    BEFORE_TRADING_START = 1
    TRADING_BAR = 2
    AFTER_TRADING_HOURS = 3
    SHUTDOWN = 4
    HEARTBEAT = 5
    DORMANT = 6


def api_method(f):
    '''
        decorator to map bound API functions to unbound user 
        functions. First add to the function to the list of available 
        API functions in the api module. Then set the api attribute to 
        scan during init for late binding.
    '''
    setattr(blueshift.algorithm.api, f.__name__, f)
    blueshift.algorithm.api.__all__.append(f.__name__)
    f.is_api = True
    return f

class Algorithm(object):
    
    def __init__(self, *args, **kwargs):
        self.mode = kwargs.get("mode",MODE.BACKTEST)
        self.state = STATE.DORMANT
        self.namespace = {}
        
        self.api = kwargs.get("broker",None)
        self.clock = kwargs.get("clock", None)
        self.calendar = kwargs.get("calendar", None)
        self.context = kwargs.get("context", AlgoContext())
        self.asset_finder = kwargs.get("asset_finder", None)
        
        
        # extract the user algo
        def noop(*args, **kwargs):
            pass
        
        self.algo = kwargs.get("algo", None)
        if self.algo is None:
            self.algo = self.context.algo
            algo_file = "<context>"
        elif os.path.isfile(self.algo):
            algo_file = os.path.basename(self.algo)
            with open(self.algo) as algofile:
                self.algo = algofile.read()
        elif isinstance(self.algo, str):
            algo_file = "<string>"
        
        code = compile(self.algo, algo_file, 'exec')
        exec(code, self.namespace)
        
        # bind the API methods to this instance. This is one time
        # binding, rather than fetching the instance at every call
        for k in self.namespace:
            if callable(self.namespace[k]):
                is_api = getattr(self.namespace[k],"is_api",None)
                if is_api:
                    self.namespace[k] = partial(self.namespace[k],self)
        
        self._initialize = self.namespace.get('initialize', noop) 
        self._handle_data = self.namespace.get('handle_data', noop)
        self._before_trading_start = self.namespace.get('before_trading_start', noop)
        self._after_trading_hours = self.namespace.get('after_trading_hours', noop)
        self._heartbeat = self.namespace.get('heartbeat', noop)
        self._analyze = self.namespace.get('analyze', noop)

    def initialize(self, timestamp):
        if self.state != STATE.DORMANT:
            raise StateMachineError("Initialize called from wrong state")
        self._initialize(self.context)
        # ready to go to the next state
        self.state = STATE.STARTUP
    
    def before_trading_start(self,timestamp):
        if self.state not in [STATE.STARTUP, \
                              STATE.AFTER_TRADING_HOURS,\
                              STATE.HEARTBEAT]:
            raise StateMachineError("Before trading start called from wrong state")
        self._before_trading_start(self.context, self.context.data)
        # ready to go to the next state
        self.state = STATE.BEFORE_TRADING_START
    
    def handle_data(self,timestamp):
        # we take a risk not checking the state maching state at 
        # handle_data, primarily to speed up things
        self._handle_data(self.context, self.context.data)
#        qty = random.randint(-50,50)
#        if qty == 0:
#            return
#        side = OrderSide.BUY if qty > 0 else OrderSide.SELL
#        o = Order(abs(qty),side,self.context.asset)
#        self.api.place_order(o)
        
    
    def after_trading_hours(self,timestamp):
        # we jump from before trading to after trading hours!
        if self.state not in [STATE.BEFORE_TRADING_START, \
                              STATE.TRADING_BAR]:
            raise StateMachineError("After trading hours called from wrong state")
        self._after_trading_hours(self.context, self.context.data)
        # ready to go to the next state
        self.state = STATE.AFTER_TRADING_HOURS
    
    def analyze(self,timestamp):
        if self.state not in [STATE.HEARTBEAT, \
                              STATE.AFTER_TRADING_HOURS]:
            raise StateMachineError("Analyze called from wrong state")
        self._heartbeat(self.context)
        
        
    def heartbeat(self, timestamp):
        if self.state not in [STATE.BEFORE_TRADING_START, \
                              STATE.AFTER_TRADING_HOURS, \
                              STATE.TRADING_BAR]:
            raise StateMachineError("Heartbeat called from wrong state")
        self._heartbeat(self.context)
        self.state = STATE.HEARTBEAT
    
    def run(self):
        t1 = pd.Timestamp.now()
        for t, bar in self.clock:
            if bar == BARS.TRADING_BAR:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.trading_bar(ts)
                self.context.BAR_update(ts)
                self.handle_data(ts)
            elif bar == BARS.ALGO_START:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.algo_start(ts)
                self.context.set_up(timestamp=ts, broker=self.api)
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
                self.context.BAR_update(ts)
                self.context.EOD_update(ts)
                self.after_trading_hours(ts)
                #algo.api.login(ts)
            elif bar == BARS.HEAR_BEAT:
                ts = pd.Timestamp(t,unit='ns',tz=self.calendar.tz)
                self.api.hear_beat(ts)
                self.heartbeat(ts)
                
        t2 = pd.Timestamp.now()
        elapsed_time = (t2-t1).total_seconds()*1000
        print("run complete in {} milliseconds".format(elapsed_time))
    
    @api_method
    def symbol(self,symbol_str:str):
        check_input(self.symbol, locals())
        return self.context.asset_finder.lookup_symbol(symbol_str)
    
    @api_method
    def symbols(self, symbol_list):
        return self.context.asset_finder.lookup_symbols(symbol_list)

