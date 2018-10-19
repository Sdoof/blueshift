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
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.execution._clock import (SimulationClock, 
                                        BARS,
                                        RealtimeClock)
from blueshift.assets.assets import AssetFinder
from blueshift.data.dataportal import DataPortal
from blueshift.execution.broker import BrokerType
from blueshift.trades._order import Order
from blueshift.trades._order_types import OrderSide

from blueshift.utils.exceptions import (
        StateMachineError,
        APIValidationError,
        InitializationError,
        ValidationError,
        BrokerAPIError)

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

class TradingAlgorithm(object):
    
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name","")
        self.mode = kwargs.get("mode",MODE.BACKTEST)
        self.state = STATE.DORMANT
        self.namespace = {}
        
        # two ways to kickstart, specify the components...
        param_test = 0
        broker = kwargs.get("broker",None)
        if isinstance(broker, AbstractBrokerAPI):
            param_test = 1
        clock = kwargs.get("clock", None)
        if isinstance(clock, (SimulationClock,RealtimeClock)):
            param_test = param_test|2
        asset_finder = kwargs.get("asset_finder", None)
        if isinstance(asset_finder, AssetFinder):
            param_test = param_test|4
        data_portal = kwargs.get("data_portal", None)
        if isinstance(data_portal, DataPortal):
            param_test = param_test|8
        
        # or specify the context. Both not acceptable
        self.context = kwargs.get("context", None)
        if self.context:
            if param_test == 15:
                raise InitializationError(msg="too many parameters"
                                    " passed in algo {} init".format(
                                                  self.name))
            # else selectively add the components to context
            else:
                self.context.update(*args, **kwargs)
        elif param_test == 15:
            self.context = AlgoContext(*args, **kwargs)
        else:
            self.context = AlgoContext(*args, **kwargs)
        # we should have a proper algo context by this time
        
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
        self._before_trading_start = self.namespace.\
                                    get('before_trading_start', noop)
        self._after_trading_hours = self.namespace.\
                                    get('after_trading_hours', noop)
        self._heartbeat = self.namespace.get('heartbeat', noop)
        self._analyze = self.namespace.get('analyze', noop)

    def __str__(self):
        return "Algorithm: name:%s, broker:%s" % (self.name,
                                                  self.context.broker)
    
    def __repr__(self):
        return self.__str__()
    
    def initialize(self, timestamp):
        if self.state != STATE.DORMANT:
            raise StateMachineError(msg="Initialize called from wrong" 
                                    " state")
        self._initialize(self.context)
        # ready to go to the next state
        self.state = STATE.STARTUP
    
    def before_trading_start(self,timestamp):
        if self.state not in [STATE.STARTUP, \
                              STATE.AFTER_TRADING_HOURS,\
                              STATE.HEARTBEAT]:
            raise StateMachineError(msg="Before trading start called"
                                    " from wrong state")
        self._before_trading_start(self.context, 
                                   self.context.data_portal)
        # ready to go to the next state
        self.state = STATE.BEFORE_TRADING_START
    
    def handle_data(self,timestamp):
        # we take a risk not checking the state maching state at 
        # handle_data, primarily to speed up things
        self._handle_data(self.context, self.context.data_portal)
    
    def after_trading_hours(self,timestamp):
        # we can jump from before trading to after trading hours!
        if self.state not in [STATE.BEFORE_TRADING_START, \
                              STATE.TRADING_BAR]:
            raise StateMachineError(msg="After trading hours called"
                                    " from wrong state")
        self._after_trading_hours(self.context, 
                                  self.context.data_portal)
        # ready to go to the next state
        self.state = STATE.AFTER_TRADING_HOURS
    
    def analyze(self,timestamp):
        if self.state not in [STATE.HEARTBEAT, \
                              STATE.AFTER_TRADING_HOURS]:
            raise StateMachineError(msg="Analyze called from wrong"
                                    " state")
        self._analyze(self.context)
        
    def heartbeat(self, timestamp):
        if self.state not in [STATE.BEFORE_TRADING_START, \
                              STATE.AFTER_TRADING_HOURS, \
                              STATE.TRADING_BAR]:
            raise StateMachineError(msg="Heartbeat called from wrong"
                                    " state")
        self._heartbeat(self.context)
        self.state = STATE.HEARTBEAT
    
    def back_test_run(self):
        if self.mode != MODE.BACKTEST:
            raise StateMachineError(msg="mode must be back-test")
        if not isinstance(self.context.clock, SimulationClock):
            raise ValidationError(msg="mode must be back-test")
        
        for t, bar in self.context.clock:
            if bar == BARS.TRADING_BAR:
                ts = pd.Timestamp(t,unit='ns',
                                  tz=self.context.trading_calendar.tz)
                self.context.broker.trading_bar(ts)
                self.context.set_timestamp(ts)
                self.context.BAR_update(ts)
                self.handle_data(ts)
            elif bar == BARS.BEFORE_TRADING_START:
                ts = pd.Timestamp(t,unit='ns',
                                  tz=self.context.trading_calendar.tz)
                self.context.broker.before_trading_start(ts)
                self.context.set_timestamp(ts)
                self.before_trading_start(ts)
            elif bar == BARS.AFTER_TRADING_HOURS:
                ts = pd.Timestamp(t,unit='ns',
                                  tz=self.context.trading_calendar.tz)
                self.context.broker.after_trading_hours(ts)
                self.context.set_timestamp(ts)
                self.context.BAR_update(ts)
                self.context.EOD_update(ts)
                self.after_trading_hours(ts)
            elif bar == BARS.HEAR_BEAT:
                ts = pd.Timestamp(t,unit='ns',
                                  tz=self.context.trading_calendar.tz)
                self.context.broker.hear_beat(ts)
                self.context.set_timestamp(ts)
                self.heartbeat(ts)
            elif bar == BARS.ALGO_START:
                ts = pd.Timestamp(t,unit='ns',
                                  tz=self.context.trading_calendar.tz)
                self.context.broker.algo_start(ts)
                self.context.set_up(timestamp=ts)
                self.initialize(ts)
            elif bar == BARS.ALGO_END:
                ts = pd.Timestamp(t,unit='ns',
                                  tz=self.context.trading_calendar.tz)
                self.context.broker.algo_end(ts)
                self.context.set_timestamp(ts)
                self.analyze(t)
    
    @api_method
    def symbol(self,symbol_str:str):
        check_input(self.symbol, locals())
        return self.context.asset_finder.lookup_symbol(symbol_str)
    
    @api_method
    def symbols(self, symbol_list):
        return self.context.asset_finder.lookup_symbols(symbol_list)
    
    @api_method
    def order(self, asset, quantity):
        if quantity == 0:
            return
        side = OrderSide.BUY if quantity > 0 else OrderSide.SELL
        o = Order(abs(quantity),side,asset)
        try:
            order_id = self.context.broker.place_order(o)
            return order_id
        except BrokerAPIError:
            pass
        
    @api_method
    def cancel_order(self, order_id):
        if order_id is None:
            return
        try:
            order_id = self.context.broker.cancel_order(order_id)
            return order_id
        except BrokerAPIError:
            pass
