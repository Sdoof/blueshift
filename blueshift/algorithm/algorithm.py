# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 11:49:54 2018

@author: prodipta
"""
from enum import Enum
import os
import pandas as pd
from functools import partial
import asyncio

#from tqdm import tqdm 

from blueshift.algorithm.context import AlgoContext
from blueshift.utils.cutils import check_input 
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.execution._clock import (SimulationClock, 
                                        BARS)
from blueshift.execution.clock import RealtimeClock, ClockQueue
from blueshift.assets.assets import AssetFinder
from blueshift.data.dataportal import DataPortal
from blueshift.execution.authentications import AbstractAuth
from blueshift.trades._order import Order
from blueshift.trades._order_types import OrderSide
from blueshift.algorithm.api_decorator import api_method
from blueshift.algorithm.api import get_broker

from blueshift.utils.exceptions import (
        StateMachineError,
        InitializationError,
        ValidationError,
        BrokerAPIError)

class MODE(Enum):
    '''
        Track the current running mode - live or backtest.
    '''
    BACKTEST = 0
    LIVE = 1
    
class STATE(Enum):
    '''
        Track the current state of the machine.
    '''
    STARTUP = 0
    BEFORE_TRADING_START = 1
    TRADING_BAR = 2
    AFTER_TRADING_HOURS = 3
    SHUTDOWN = 4
    HEARTBEAT = 5
    DORMANT = 6
    

class TradingAlgorithm(object):
    
    def _make_bars_dispatch(self):
        '''
            Dispatch dictionary for user defined functions.
        '''
        self._USER_FUNC_DISPATCH = {
            BARS.ALGO_START:self.initialize,
            BARS.BEFORE_TRADING_START:self.before_trading_start,
            BARS.TRADING_BAR:self.handle_data,
            BARS.AFTER_TRADING_HOURS:self.after_trading_hours,
            BARS.HEAR_BEAT:self.heartbeat,
            BARS.ALGO_END:self.analyze
        }
        
    def _make_broker_dispatch(self):
        '''
            Dispatch dictionary for backtest broker processing.
        '''
        self._BROKER_FUNC_DISPATCH = {
            BARS.ALGO_START:self.context.broker.algo_start,
            BARS.BEFORE_TRADING_START:self.context.broker.\
                                            before_trading_start,
            BARS.TRADING_BAR:self.context.broker.trading_bar,
            BARS.AFTER_TRADING_HOURS:self.context.broker.\
                                            after_trading_hours,
            BARS.HEAR_BEAT:self.context.broker.heart_beat,
            BARS.ALGO_END:self.context.broker.algo_end
        }

    def __init__(self, *args, **kwargs):
        '''
            Get the arguments and resolve them to a consistent context
            object. Then read the user algo and extract the API 
            functions and create the dispatcher.
        '''
        self.name = kwargs.get("name","")
        self.mode = kwargs.get("mode",MODE.BACKTEST)
        self.state = STATE.DORMANT
        self.namespace = {}
        
        # two ways to kickstart, specify the components...
        param_test = 0
        broker_api = kwargs.get("api",None)
        if isinstance(broker_api, AbstractBrokerAPI):
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
        auth = kwargs.get("auth", None)
        if isinstance(auth, AbstractAuth):
            param_test = param_test|16
        
        # or specify the context. Both not acceptable
        self.context = kwargs.get("context", None)
        if self.context:
            if param_test >= 15:
                raise InitializationError(msg="too many parameters"
                                    " passed in algo {} init".format(
                                                  self.name))
            # else selectively add the components to context
            else:
                self.context.reset(*args, **kwargs)
        
        else:
            self.context = AlgoContext(*args, **kwargs)
        # we should have a proper algo context by this time
        # but this may not be initialized and ready to run.
        # we must check initialization before running the algo.
        
        # extract the user algo
        def noop(*args, **kwargs):
            # pylint: disable=unused-argument
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
        
        # the async loop and message queue for the realtime clock
        self._loop = None
        self._queue = None
        
        # create the bars dispatch dictionaries
        self.USER_FUNC_DISPATCH = {}
        self._BROKER_FUNC_DISPATCH = {}
        
        self._make_bars_dispatch()

    def __str__(self):
        return "Algorithm: name:%s, broker:%s" % (self.name,
                                                  self.context.broker)
    
    def __repr__(self):
        return self.__str__()
    
    def _bar_noop(self, timestamp):
        '''
            null operation for a bar function.
        '''
        pass
    
    def initialize(self, timestamp):
        '''
            Called at the start of the algo.
        '''
        if self.state != STATE.DORMANT:
            raise StateMachineError(msg="Initialize called from wrong" 
                                    " state")
        self._initialize(self.context)
        # ready to go to the next state
        self.state = STATE.STARTUP
    
    def before_trading_start(self,timestamp):
        '''
            Called at the start of the session.
        '''
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
        '''
            Called at the start of each trading bar.
        '''
        # we take a risk not checking the state maching state at 
        # handle_data, primarily to speed up things
        self._handle_data(self.context, self.context.data_portal)
    
    def after_trading_hours(self,timestamp):
        '''
            Called at the end of the session.
        '''
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
        '''
            Called at the end of the algo run.
        '''
        if self.state not in [STATE.HEARTBEAT, \
                              STATE.AFTER_TRADING_HOURS]:
            raise StateMachineError(msg="Analyze called from wrong"
                                    " state")
        self._analyze(self.context)
        
    def heartbeat(self, timestamp):
        '''
            Called when we are not in a session.
        '''
        if self.state not in [STATE.BEFORE_TRADING_START, \
                              STATE.AFTER_TRADING_HOURS, \
                              STATE.TRADING_BAR,\
                              STATE.STARTUP,\
                              STATE.HEARTBEAT]:
            raise StateMachineError(msg="Heartbeat called from wrong"
                                    " state")
        self._heartbeat(self.context)
        self.state = STATE.HEARTBEAT
    
    def _back_test_run(self):
        '''
            The entry point for backtest run.
        '''
        if self.mode != MODE.BACKTEST:
            raise StateMachineError(msg="mode must be back-test")
        
        if not self.context.is_initialized():
            raise InitializationError(msg="context is not "
                                      "properly initialized")
        
        if not isinstance(self.context.clock, SimulationClock):
            raise ValidationError(msg="clock must be simulation clock")
            
        self._make_broker_dispatch() # only useful for backtest
        
        for t, bar in self.context.clock:
            ts = pd.Timestamp(t,unit='ns',
                              tz=self.context.trading_calendar.tz)
            
            if bar == BARS.ALGO_START:
                self.context.set_up(timestamp=ts)
                
            self.context.set_timestamp(ts)
            self._BROKER_FUNC_DISPATCH.get(bar,self._bar_noop)(ts)
            
            if bar == BARS.TRADING_BAR:
                #self.context.BAR_update(ts)
                pass
            
            if bar == BARS.AFTER_TRADING_HOURS:
                #self.context.BAR_update(ts)
                self.context.EOD_update(ts)
                
            self._USER_FUNC_DISPATCH.get(bar,self._bar_noop)(ts)
    
    def _get_event_loop(self):
        '''
            Obtain the current event loop or create one.
        '''
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        if self._loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
            self._loop = asyncio.get_event_loop()
    
    def _reset_clock(self, delay=1):
        '''
            Reset the realtime clock
        '''
        self._get_event_loop()
        self._queue = ClockQueue(loop=self._loop)
        self.context.clock.reset(self._queue, delay)
        
    async def _process_tick(self):
        '''
            Process ticks from real clock asynchronously.
        '''
        while True:
            # start from the beginning, process all ticks except
            # TRADING_BAR or HEAR_BEAT. For these we skip to the last
            # TODO: implement this logic in ClockQueue
            t, bar = await self._queue.get_last()
            ts = pd.Timestamp.now(tz=self.context.trading_calendar.tz)
            print("{}: got {}".format(ts, bar))
            
            if bar == BARS.ALGO_START:
                self.context.set_up(timestamp=ts)
            self.context.set_timestamp(ts)
            
            if bar == BARS.TRADING_BAR:    
                self.context.BAR_update(ts)
            
            if bar == BARS.AFTER_TRADING_HOURS:
                self.context.BAR_update(ts)
                self.context.EOD_update(ts)
                
            self._USER_FUNC_DISPATCH.get(bar,self._bar_noop)(ts)
            
    
    def _live_run(self):
        '''
            The entry point for a live run.
        '''
        if self.mode != MODE.LIVE:
            raise StateMachineError(msg="mode must be live")
        
        if not self.context.is_initialized():
            raise InitializationError(msg="context is not "
                                      "properly initialized")
        
        if not isinstance(self.context.clock, RealtimeClock):
            raise ValidationError(msg="clock must be real-time clock")
        
        # reset the clock at the start of the run, this also aligns
        # ticks to the nearest rounded bar depending on the frequency
        self._reset_clock(self.context.clock.emit_frequency)
        
        # initialize the coroutines
        clock_coro = self.context.clock.tick()
        algo_coro = self._process_tick()
        
        try:
            tasks = asyncio.gather(clock_coro,algo_coro,
                                   return_exceptions=False)
            self._loop.run_until_complete(tasks)
        except BaseException as e:
            # TODO: do a proper exception handling here
            print("exception {}".format(e))
            tasks.cancel()
            raise e
        finally:
            self._loop.close()
        
    def run(self):
        if self.mode == MODE.LIVE:
            self._live_run()
        elif self.mode == MODE.BACKTEST:
            self._back_test_run()
        else:
            raise StateMachineError(msg="undefined mode")
    
    @api_method
    def symbol(self,symbol_str:str):
        '''
            API function to resolve a symbol string to an asset.
        '''
        check_input(self.symbol, locals())
        return self.context.asset_finder.lookup_symbol(symbol_str)
    
    @api_method
    def symbols(self, symbol_list):
        '''
            API function to resolve a list of symbols to a list of 
            asset.
        '''
        return self.context.asset_finder.lookup_symbols(symbol_list)
    
    @api_method
    def order(self, asset, quantity):
        '''
            Place new order.
        '''
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
        '''
            Cancel existing order if not already executed.
        '''
        if order_id is None:
            return
        try:
            order_id = self.context.broker.cancel_order(order_id)
            return order_id
        except BrokerAPIError:
            pass

    @api_method
    def set_broker(self, name, *args, **kwargs):
        '''
            Change the broker in run time. This is useful to modify
            the broker api (including execution logic if any) or the
            capital. This will NOT change the clock, and we do not want
            that either.
        '''
        if self.state not in [STATE.STARTUP, STATE.DORMANT,\
                              BARS.HEAR_BEAT]:
            msg = "cannot set broker in current state"
            raise StateMachineError(msg=msg)
        
        broker = get_broker(name, *args, **kwargs)
        
        # we cannot switch from backtest to live or reverse
        if type(self.context.clock) != type(broker.clock):
            msg = "cannot switch from backtest to live or reverse"
            raise StateMachineError(msg=msg)
        
        # we should not attempt to change the clock!
        self.context.reset(api=broker.broker, auth=broker.auth,
                           asset_finder=broker.asset_finder,
                           data_portal=broker.data_portal)
            
        