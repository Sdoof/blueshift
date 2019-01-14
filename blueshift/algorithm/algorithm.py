# Copyright 2018 QuantInsti Quantitative Learnings Pvt Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Mon Oct  8 11:49:54 2018

@author: prodipta
"""
from os import path as os_path
import pandas as pd
from functools import partial
import asyncio
from collections.abc import Iterable
import json

from transitions import MachineError

from blueshift.algorithm.context import AlgoContext
from blueshift.utils.cutils import check_input
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.execution._clock import (SimulationClock, 
                                        BARS)
from blueshift.execution.clock import RealtimeClock, ClockQueue
from blueshift.assets import AssetFinder
from blueshift.data.dataportal import DataPortal
from blueshift.execution.authentications import AbstractAuth
from blueshift.trades._order import Order
from blueshift.trades._order_types import OrderSide
from blueshift.algorithm.api_decorator import api_method, command_method
from blueshift.api import get_broker
from blueshift.utils.types import noop, MODE, listlike
from blueshift.algorithm.state_machine import AlgoStateMachine

from blueshift.alerts import get_logger
from blueshift.utils.calendars.trading_calendar import make_consistent_tz

from blueshift.utils.exceptions import (
        StateMachineError,
        InitializationError,
        ValidationError,
        CommandShutdownException,
        ScheduleFunctionError,
        TradingControlError,
        BlueShiftException)

from blueshift.utils.decorators import blueprint
from blueshift.utils.ctx_mgr import (ShowProgressBar,
                                     MessageBrokerCtxManager)
from blueshift.utils.scheduler import (TimeRule, TimeEvent, Scheduler,
                                       date_rules)

from blueshift.execution.controls import (TradingControl,
                                          TCOrderQtyPerTrade,
                                          TCOrderValuePerTrade,
                                          TCOrderQtyPerDay,
                                          TCOrderValuePerDay,
                                          TCOrderNumPerDay,
                                          TCLongOnly,
                                          TCPositionQty,
                                          TCPositionValue,
                                          TCGrossLeverage,
                                          TCGrossExposure,
                                          TCBlackList, TCWhiteList)

from blueshift.blotter.blotter import Blotter

@blueprint
class TradingAlgorithm(AlgoStateMachine):
    '''
        The trading algorithm is responsible for 1. reading the input
        program, 2. collecting and running user functions in appropriate
        event functions, 3. handling commands and publishing performance
        packets as well as defining the API functions. The main loops in
        backtest and live runs are different. Backtest in implemented as
        generator. Live loop is an async generator to make use of the 
        sleep time of the real clock.
    '''
    
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
            Get the arguments and resolve them to a consistent 
            context object. Then read the user algo and extract the 
            API functions and create the dispatcher.
        '''
        super(self.__class__, self).__init__(*args, **kwargs)
        
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
                      " passed in algo {} init".format(self.name))
            # else selectively add the components to context
            else:
                self.context.reset(*args, **kwargs)
        
        else:
            self.context = AlgoContext(*args, **kwargs)
        # we should have a proper algo context by this time
        # but this may not be initialized and ready to run.
        # we must check initialization before running the algo.
        # Most of it done in context, here we check run mode compatibility.
        if self.mode not in self.context.broker._mode_supports:
            raise InitializationError(msg="incompatible run mode and broker.")
        
        # extract the user algo
        self.algo = kwargs.get("algo", None)
        if self.algo is None:
            raise InitializationError(msg="algo file missing.")
        
        if os_path.isfile(self.algo):
            algo_file = os_path.basename(self.algo)
            with open(self.algo) as algofile:
                self.algo = algofile.read()
        elif isinstance(self.algo, str):
            algo_file = "<string>"
        else:
            raise InitializationError(msg="algo file not found.")
        
        code = compile(self.algo, algo_file, 'exec')
        exec(code, self.namespace)
        
        # bind the API methods to this instance. This is one time
        # binding, rather than fetching the instance at every call
        for k in self.namespace:
            if callable(self.namespace[k]):
                is_api = getattr(self.namespace[k],"is_api",None)
                if is_api:
                    self.namespace[k] = partial(self.namespace[k],
                                  self)
        
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
        self._USER_FUNC_DISPATCH = {}
        self._BROKER_FUNC_DISPATCH = {}
        
        self._make_bars_dispatch()
        
        # setup the default logger
        self._logger = None
        self._set_logger()
        
        # set up the scheduler
        self._scheduler = Scheduler()
        
        # set up the trading controllers list and blotter
        self._trading_controls = []
        self.__freeze_trading = False
        self._blotter = Blotter(
                self.mode, self.context.asset_finder,
                self.context.data_portal, self.context.broker)

    def __str__(self):
        return "Blueshift Algorithm [name:%s, broker:%s]" % (self.name,
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
            Called at the start of the algo. Or at every resume command.
        '''
        try:
            self.fsm_initialize()
        except MachineError:
            msg = f"State Machine Error ({self.state}): in initialize"
            raise StateMachineError(msg=msg)
        
        self._blotter.reset(timestamp, self.context.account["net"])
        self._initialize(self.context)
    
    def before_trading_start(self,timestamp):
        '''
            Called at the start of the session.
        '''
        try:
            self.fsm_before_trading_start()
        except MachineError:
            msg = f"State Machine Error ({self.state}): in before_trading_start"
            raise StateMachineError(msg=msg)
        
        self._before_trading_start(self.context, 
                                   self.context.data_portal)
        
        # call the handle data state update here.
        if self.mode != MODE.LIVE:
            try:
                self.fsm_handle_data()
            except MachineError:
                msg = f"State Machine Error ({self.state}): in handle_data"
                raise StateMachineError(msg=msg)
    
    def handle_data(self,timestamp):
        '''
            Called at the start of each trading bar. We call the state
            machine function only for live mode here, and club with 
            before trading start for backtest mode. This a bit hacky but
            speeds things up.
        '''
        if self.mode == MODE.LIVE:
            try:
                self.fsm_handle_data()
            except MachineError:
                msg = f"State Machine Error ({self.state}): in handle_data"
                raise StateMachineError(msg=msg)
                
        # run scheduled tasks first
        self._scheduler.trigger_events(self.context, 
                                       self.context.data_portal, 
                                       timestamp.value)
        
        # followed by user defined handle_data
        self._handle_data(self.context, self.context.data_portal)
    
    def after_trading_hours(self,timestamp):
        '''
            Called at the end of the session.
        '''
        try:
            self.fsm_after_trading_hours()
        except MachineError:
            msg = f"State Machine Error ({self.state}): in after_trading_hours"
            raise StateMachineError(msg=msg)
        
        self._blotter.save()
        self._after_trading_hours(self.context, 
                                  self.context.data_portal)
    
    def analyze(self,timestamp):
        '''
            Called at the end of the algo run.
        '''
        try:
            self.fsm_analyze()
        except MachineError:
            msg=f"State Machine Error ({self.state}): in analyze"
            raise StateMachineError(msg=msg)
        
        self._analyze(self.context)
        
    def heartbeat(self, timestamp):
        '''
            Called when we are not in a session.
        '''
        try:
            self.fsm_heartbeat()
        except MachineError:
            msg=f"State Machine Error ({self.state}): in heartbeat"
            raise StateMachineError(msg=msg)
        
        self._heartbeat(self.context)
        
    
    def _back_test_generator(self, alert_manager=None):
        '''
            The entry point for backtest run. This generator yields
            the current day performance.
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
            try:
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
                    perf = self.context.performance
                    perf['timestamp'] = str(self.context.timestamp)
                    yield perf
                    
                self._USER_FUNC_DISPATCH.get(bar,self._bar_noop)(ts)
        
            except BlueShiftException as e:
                if not alert_manager:
                    raise e
                else:
                    timestamp = self.context.timestamp
                    alert_manager.handle_error(e,'algorithm',
                                               mode=self.mode,
                                               timestamp=timestamp)
                    continue
    
    def back_test_run(self, alert_manager=None, publish_packets=False,
                      show_progress=False):
        
        runner = self._back_test_generator(alert_manager=alert_manager)
        length = len(self.context.clock.session_nanos)
        perfs = []
        
        if not alert_manager:
            publish_packets = False
            publisher_handle = None
        else:
            publisher_handle = alert_manager.publisher
        
        with ShowProgressBar(runner, show_progress=show_progress,
                             label=self.name,
                             length=length) as performance,\
            MessageBrokerCtxManager(publisher_handle,
                                    enabled=publish_packets) as\
                                publisher:
            for packet in performance:
                perfs.append(packet)
                if publish_packets:
                    publisher.send(json.dumps(packet))
                    
        idx = pd.to_datetime([p['timestamp'] for p in perfs])
        perfs = pd.DataFrame(perfs, idx)
        return perfs
    
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
        
    async def _process_tick(self, alert_manager=None):
        '''
            Process ticks from real clock asynchronously. This generator 
            receives a command from the channel, and if it is `continue`,
            continues normal algo loop. Else either pause or stop the algo.
            It can also invoke any member function based on command.
        '''
            
        while True:
            '''
                start from the beginning, process all ticks except
                TRADING_BAR or HEAR_BEAT. For these we skip to the last
                TODO: implement this logic in ClockQueue.
            '''
            try:
                cmd = yield         # get the command if any.
                if cmd:
                    self._process_command(cmd)
                
                t, bar = await self._queue.get_last()
                ts = pd.Timestamp.now(
                        tz=self.context.trading_calendar.tz)
                print(f"{t}:{bar}")
                
                if self.is_STOPPED():
                    self.log_info("algorithm stopped, will exit.",t)
                    raise CommandShutdownException(msg="shutting down.")
                elif self.is_PAUSED():
                    continue
                
                if bar == BARS.ALGO_START:
                    self.context.set_up(timestamp=ts)
                self.context.set_timestamp(ts)
                
                if bar == BARS.TRADING_BAR:    
                    self.context.BAR_update(ts)
                    yield {'bar':self.context.pnls}
                
                if bar == BARS.AFTER_TRADING_HOURS:
                    self.context.BAR_update(ts)
                    self.context.EOD_update(ts)
                    yield {'daily':self.context.performance}
                    
                if self.is_running():       # NOT PAUSED!!
                    self._USER_FUNC_DISPATCH.get(bar,self._bar_noop)(ts)
            
            except BlueShiftException as e:
                if not alert_manager:
                    raise e
                else:
                    alert_manager.handle_error(e,'algorithm')
                    continue
            
    async def _run_live(self, alert_manager=None, publish_packets=False):
        '''
            Function to run the main algo loop generator and also
            handle incoming commands from the command channel.
        '''
        g = self._process_tick(alert_manager)
        command_enabled = True
        
        if not alert_manager:
            command_enabled=False
            publish_packets=False
            publisher_handle = None
            commander_handle = None
        else:
            publisher_handle = alert_manager.publisher
            commander_handle = alert_manager.cmd_listener
        
        with MessageBrokerCtxManager(commander_handle, 
                                     enabled=command_enabled) as commander,\
            MessageBrokerCtxManager(publisher_handle,
                                    enabled=publish_packets) as\
                                        publisher:
            async for msg in g:
                cmd = commander.get_next_command()  # no wait.
                packet = await g.asend(cmd)         # None if no command.
                if publish_packets:
                    publisher.send(json.dumps(packet))
    
    def live_run(self, alert_manager=None, publish_packets=False):
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
        algo_coro = self._run_live(alert_manager, publish_packets)
        
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
        
    def run(self, alert_manager=None, publish=False, show_progress=False):
        if self.mode == MODE.LIVE:
            self.live_run(alert_manager, publish) # no progress bar for live
        elif self.mode == MODE.BACKTEST:
            self.back_test_run(alert_manager, publish, show_progress)
        else:
            raise StateMachineError(msg="undefined mode")
            
    def _set_logger(self):
        self._logger = get_logger()
        if self._logger:
            self._logger.tz = self.context.trading_calendar.tz
        
    def log_info(self, msg, timestamp=None):
        if self._logger:
            if timestamp:
                self._logger.info(msg,"algorithm", timestamp=timestamp,
                                  mode=self.mode)
            else:
                self._logger.info(msg,"algorithm")
            
    def log_warning(self, msg, timestamp=None):
        if self._logger:
            if timestamp:
                self._logger.warning(msg,"algorithm", timestamp=timestamp,
                                     mode=self.mode)
            else:
                self._logger.warning(msg,"algorithm")
            
    def log_error(self, msg, timestamp=None):
        if self._logger:
            if timestamp:
                self._logger.error(msg,"algorithm", timestamp=timestamp,
                                   mode=self.mode)
            else:
                self._logger.error(msg,"algorithm")
    
    '''
        A list of methods for processing commands received on the command
        channel during a live run.
    '''
    def _process_command(self, cmd):
        print(cmd)
        fn = getattr(self, cmd.cmd, None)
        if fn:
            is_cmd_fn = getattr(fn, "is_command", False)
            if is_cmd_fn:
                fn(*cmd.args, **cmd.kwargs)
            else:
                msg = f"{fn} is not a recognized command, will be ignored."
                self.log_warning(msg)
        else:
            msg = f"unknown command {cmd.cmd}, will be ignored."
            self.log_warning(msg)
        
    @command_method
    def current_state(self):
        print(self.state)
    
    @command_method
    def pause(self, *args, **kwargs):
        try:
            self.fsm_pause()
            msg = "algorithm paused. No further processing till resumed."
            self.log_warning(msg)
        except MachineError:
            msg=f"State Machine Error ({self.state}): attempt to pause."
            raise StateMachineError(msg=msg)
        
    @command_method
    def resume(self, *args, **kwargs):
        '''
            Resuming an algo trigger state changes starting with a call
            to initialize.
        '''
        try:
            self.fsm_resume()       # PAUSED ==> STARTUP
            # TODO: this is risky, there is a change that the queue
            # may be None within the tick coroutine in clock possibly?
            self._reset_clock(self.context.clock.emit_frequency)
            self.log_warning("algorithm resumed.")
        except MachineError:
            msg=f"State Machine Error ({self.state}): attempt to resume."
            raise StateMachineError(msg=msg)
        
    @command_method
    def shutdown(self, *args, **kwargs):
        try:
            self.fsm_stop()
            self.log_warning("algorithm stopped.")
        except MachineError:
            # this should never fail.
            msg=f"State Machine Error ({self.state}): attempt to stop."
            raise StateMachineError(msg=msg)
    
    @command_method
    def login(self, *args, **kwargs):
        auth = self.context.auth
        if auth:
            auth.login(*args, **kwargs)
        self.log_warning("executed login with authenticator.")
        
    @command_method
    def refresh_asset_db(self, *args, **kwargs):
        asset_finder = self.context.asset_finder
        if asset_finder:
            asset_finder.refresh_data(*args, **kwargs)
        self.log_warning("Relaoded asset database.")
        
    @command_method
    def stop_trading(self, *args, **kwargs):
        self._freeze_trading()
        self.log_warning("All trading stopped. All orders will be ignored.")
    
    @command_method
    def resume_trading(self, *args, **kwargs):
        self._unfreeze_trading()
        self.log_warning("Trading resumed. Orders will be sent to broker.")
    
    '''
        All API functions related to algorithm objects should go in this
        space. These are accessible from the user code directly.
    '''
    @api_method
    def get_datetime(self):
        '''
            Get the current date-time of the algorithm context.
        '''
        if self.mode == MODE.BACKTEST:
            dt = self.context.timestamp
        else:
            dt = pd.Timestamp.now(tz=self.context.trading_calendar.tz)
        return dt
    
    @api_method
    def register_trading_controls(self, control):
        '''
            Register a trading control instance to check before each
            order is created.
        '''
        if not isinstance(control, TradingControl):
            raise TradingControlError(msg="invalid control type.")
        
        self._trading_controls.append(control)
    
    @api_method
    def record(self, *args, **kwargs):
        '''
            Record a list of var-name, value pairs for each day.
        '''
        args_iter = iter(args)
        var_dict = dict(zip(args_iter,args_iter))
        var_dict = {**var_dict, **kwargs}
        
        for varname, value in var_dict.items():
            self.context.record_var(varname, value)
    
    @api_method
    def schedule_function(self, callback, date_rule=None, time_rule=None):
        '''
            Schedule a callable to executed by a set of date and time based
            rules.
        '''
        if not date_rule and not time_rule:
            return
        
        date_rule = date_rule or date_rules.every_day()
        if not time_rule:
            ScheduleFunctionError(msg="must specify a time rule.")
            
        if not hasattr(date_rule, 'date_rule'):
            ScheduleFunctionError(msg="not a valid date rule.")
            
        if not hasattr(time_rule, 'time_rule'):
            ScheduleFunctionError(msg="not a valid time rule.")
        
        if not callable(callback):
            ScheduleFunctionError(msg="callback must be a callable.")
        
        if self.mode == MODE.BACKTEST:
            start_dt = pd.Timestamp(self.context.clock.start_nano, 
                                    tz=self.context.trading_calendar.tz)
            end_dt = pd.Timestamp(self.context.clock.end_nano, 
                                    tz=self.context.trading_calendar.tz)
            rule = TimeRule(date_rule, time_rule, start_dt=start_dt,
                            end_dt=end_dt,
                            trading_calendar = self.context.trading_calendar)
        else:
            rule = TimeRule(date_rule, time_rule, 
                            trading_calendar = self.context.trading_calendar)
        
        e = TimeEvent(rule, callback)
        self._scheduler.add_event(e)
        
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
        return self.context.asset_finder.lookup_symbols(
                symbol_list,self.context.timestamp)
    
    @api_method
    def sid(self, sec_id:int):
        '''
            API function to resolve an asset ID (int) to an asset.
        '''
        check_input(self.sid, locals())
        return self.context.asset_finder.fetch_asset(sec_id)
    
    @api_method
    def can_trade(self, assets):
        '''
            API function to check if asset can be traded at current dt.
        '''
        if not self.is_TRADING_BAR():
            return False
        
        if not isinstance(assets, Iterable):
            assets = [assets]
            
        _can_trade = []
        for asset in assets:
            if asset.auto_close_date:
                exp_dt = asset.auto_close_date
                dt = self.get_datetime()
                exp_dt = make_consistent_tz(exp_dt, 
                                            self.context.tradng_calendar.tz)
                _can_trade.append(exp_dt > dt)
                
        return all(_can_trade)
    
    def _control_fail_handler(self, control, asset, dt, amount, context):
        '''
            Default control validation fail handler, logs a warning.
        '''
        msg = control.get_error_msg(asset, dt)
        self.log_warning(msg, timestamp=self.context.timestamp)
    
    def _validate_trading_controls(self, order):
        '''
            Validate all controls. Return false with the first fail.
        '''
        for control in self._trading_controls:
            if not control.validate(order, self.context.timestamp, 
                                    self.context, 
                                    self._control_fail_handler):
                return False
        return True
    

    def _freeze_trading(self):
        self.__freeze_trading = True
        
    def _unfreeze_trading(self):
        self.__freeze_trading = False
        
    # list of trading control APIs affecting order functions
    @api_method
    def set_max_order_size(self, assets=None, max_quantity=None, 
                           max_notional=None, on_fail=None):
        if not max_quantity and not max_notional:
            msg = "must specify either max quantity or "
            msg = msg + "max notional"
            raise TradingControlError(msg=msg)
        elif max_quantity and max_notional:
            msg = "cannot have both controls:"
            msg = msg + " max quantity and max notional"
            raise TradingControlError(msg=msg)
        elif max_quantity:
            ctrl = 0
            value = max_quantity
        else:
            ctrl = 1
            value = max_notional
        
        limit_dict = {}
        if isinstance(assets, dict):
            limit_dict = assets
            default = None
        elif listlike(assets):
            limit_dict = dict(zip(assets,[value]*len(assets)))
            default = None
        else:
            default = value
            
        if ctrl == 0:
            control = TCOrderQtyPerTrade(default, limit_dict, on_fail)
        else:
            control = TCOrderValuePerTrade(default, limit_dict, on_fail)
            
        self.register_trading_controls(control)
        
    @api_method
    def set_max_daily_size(self, assets=None, max_quantity=None, 
                           max_notional=None, on_fail=None):
        if not max_quantity and not max_notional:
            msg = "must specify either max quantity or "
            msg = msg + "max notional"
            raise TradingControlError(msg=msg)
        elif max_quantity and max_notional:
            msg = "cannot have both controls:"
            msg = msg + " max quantity and max notional"
            raise TradingControlError(msg=msg)
        elif max_quantity:
            ctrl = 0
            limit = max_quantity
        else:
            ctrl = 1
            limit = max_notional
        
        limit_dict = {}
        if isinstance(assets, dict):
            limit_dict = assets
            default = None
        elif listlike(assets):
            limit_dict = dict(zip(assets,[limit]*len(assets)))
            default = None
        else:
            default = limit
            
        if ctrl == 0:
            control = TCOrderQtyPerDay(default, limit_dict, on_fail)
        else:
            control = TCOrderValuePerDay(default, limit_dict, on_fail)
            
        self.register_trading_controls(control)
        
    @api_method
    def set_max_position_size(self, assets=None, max_quantity=None, 
                              max_notional=None, on_fail=None):
        if not max_quantity and not max_notional:
            msg = "must specify either max quantity or "
            msg = msg + "max notional"
            raise TradingControlError(msg=msg)
        elif max_quantity and max_notional:
            msg = "cannot have both controls:"
            msg = msg + " max quantity and max notional"
            raise TradingControlError(msg=msg)
        elif max_quantity:
            ctrl = 0
            limit = max_quantity
        else:
            ctrl = 1
            limit = max_notional
        
        limit_dict = {}
        if isinstance(assets, dict):
            limit_dict = assets
            default = None
        elif listlike(assets):
            limit_dict = dict(zip(assets,[limit]*len(assets)))
            default = None
        else:
            default = limit
            
        if ctrl == 0:
            control = TCPositionQty(default, limit_dict, on_fail)
        else:
            control = TCPositionValue(default, limit_dict, on_fail)
            
        self.register_trading_controls(control)
        
    @api_method
    def set_max_order_count(self, max_count, on_fail=None):
        control = TCOrderNumPerDay(max_count, on_fail)
        self.register_trading_controls(control)
        
    @api_method
    def set_long_only(self, on_fail=None):
        control = TCLongOnly(on_fail)
        self.register_trading_controls(control)
        
    @api_method
    def set_max_leverage(self, max_leverage, on_fail=None):
        control = TCGrossLeverage(max_leverage, on_fail)
        self.register_trading_controls(control)
        
    @api_method
    def set_max_exposure(self, max_exposure, on_fail=None):
        control = TCGrossExposure(max_exposure, on_fail)
        self.register_trading_controls(control)
        
    @api_method
    def set_do_not_order_list(self, assets, on_fail=None):
        if not listlike(assets):
            assets = [assets]
        control = TCBlackList(assets, on_fail)
        self.register_trading_controls(control)
        
    @api_method
    def set_allowed_list(self, assets, on_fail=None):
        if not listlike(assets):
            assets = [assets]
        control = TCWhiteList(assets, on_fail)
        self.register_trading_controls(control)
    
    # TODO: cythonize the creation of order
    @api_method
    def order(self, asset, quantity, 
              limit_price=0, stop_price=0, style=None):
        '''
            Place new order. This is the interface to underlying broker
            for ALL order related API functions.
        '''
        if self.__freeze_trading:
            return
        
        if not self.is_TRADING_BAR():
            msg = f"can't place order for {asset.symbol},"
            msg = msg + " market not open yet."
            self.log_warning(msg, timestamp=self.context.timestamp)
            return
        
        mult = asset.mult
        quantity = int(round(quantity/mult)*mult)
        if quantity == 0:
            return
        
        side = OrderSide.BUY if quantity > 0 else OrderSide.SELL
        
        order_type = 0
        if style:
            order_type = style
        else:
            if limit_price > 0:
                order_type = 1
            if stop_price > 0:
                order_type = order_type|2
        
        o = Order(abs(quantity),side,asset,order_type = order_type,
                  price=limit_price, stoploss_price=stop_price)
        
        checks_ok = self._validate_trading_controls(o)
        if not checks_ok:
            return
        
        order_id = self.context.broker.place_order(o)
        
        if self.mode == MODE.LIVE:
            msg = f"sent order {order_id}:{o.to_json()}"
            self.log_info(msg, self.context.timestamp)
            
        self._blotter.add_transactions(order_id, o, 0, 0)
        
        return order_id

    @api_method
    def order_value(self, asset, value, 
              limit_price=0, stop_price=0, style=None):
        '''
            API function to order an asset worth a specified value.
        '''
        last_price = self.context.data_portal.current(asset, "close")
        qty = int(value/last_price)
        return self.order(asset,qty,limit_price,stop_price,style)
    
    @api_method
    def order_percent(self, asset, percent, 
              limit_price=0, stop_price=0, style=None):
        '''
            API function to order an asset worth a defined percentage 
            of account net value.
        '''
        net = self.context.account["net"]
        value = net*percent
        return self.order_value(asset,value,limit_price,stop_price,style)
    
    @api_method
    def order_target(self, asset, target, 
              limit_price=0, stop_price=0, style=None):
        '''
            API function to order an asset to achieve a specified 
            quantity value in the portfolio.
        '''
        pos = self.context.portfolio.get(asset, None)
        pos = pos.quantity if pos else 0
        qty = target - pos
        return self.order(asset,qty,limit_price,stop_price,style)
    
    @api_method
    def order_target_value(self, asset, target, 
              limit_price=0, stop_price=0, style=None):
        '''
            API function to order an asset to achieve a specified 
            target value in the portfolio.
        '''
        last_price = self.context.data_portal.current(asset, "close")
        target = target/last_price
        return self.order_target(asset,target,limit_price,stop_price,style)
    
    @api_method
    def order_target_percent(self, asset, percent, 
              limit_price=0, stop_price=0, style=None):
        '''
            API function to order an asset to achieve a specified 
            percent of account net worth.
        '''
        net = self.context.account["net"]
        target = net*percent
        return self.order_target_value(asset,target,limit_price,stop_price,style)
    
    @api_method
    def square_off(self, assets=None):
        '''
            API function to square off ALL open positions and cancel 
            all open orders. Typically useful for end-of-day closure for
            intraday strategies or for orderly shut-down.
        '''
        open_orders = self.get_open_orders()
        if assets is None:
            for order_id in open_orders:
                self.cancel_order(order_id)
        else:
            symbols = []
            if not listlike(assets):
                assets = [assets]
            for order_id in open_orders:
                if open_orders[order_id].asset in assets:
                    self.cancel_order(order_id)
                    symbols.append(assets.symbol)
        
        if getattr(self.context.broker,"square_off", None):
            self.context.broker.square_off(symbols)
            return
        
        open_positions = self.get_open_positions()
        for asset in open_positions:
            self.order_target(asset,0)
            
        return
    
    @api_method
    def cancel_order(self, order_param):
        '''
            Cancel existing order if not already executed.
        '''
        if not self.is_TRADING_BAR():
            msg = f"can't cancel order, market not open."
            raise ValidationError(msg=msg)
        
        order_id = order_param.oid if isinstance(order_param, Order)\
                        else order_param
        
        order_id = self.context.broker.cancel_order(order_id)
    
        if self.mode == MODE.LIVE:
            msg = f"sent cancel order for {order_id}"
            self.log_info(msg, self.context.timestamp)
            
        return order_id
        
    @api_method
    def get_order(self, order_id):
        '''
            Get an order object by order_id.
        '''
        return self.context.broker.order(order_id)

    @api_method
    def get_open_orders(self):
        '''
            Get a dictionary of all open orders, keyed by their id.
        '''
        return self.context.broker.open_orders
    
    @api_method
    def get_open_positions(self):
        '''
            Get a dictionary of all open orders, keyed by their id.
        '''
        positions = self.context.broker.positions
        open_positions = {}
        for asset, pos in positions.items():
            if pos.quantity != 0:
                open_positions[asset] = pos
        
        return open_positions

    @api_method
    def set_broker(self, name, *args, **kwargs):
        '''
            Change the broker in run time. This is useful to modify
            the broker api (including execution logic if any) or the
            capital. This will NOT change the clock, and we do not 
            want that either.
        '''
        if not self.is_INITIALIZED() or not self.is_HEARTBEAT():
            msg = "cannot set broker in state ({self.state})"
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
            
        