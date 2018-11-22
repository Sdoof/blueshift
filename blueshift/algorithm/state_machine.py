# -*- coding: utf-8 -*-
"""
Created on Tue Nov 20 15:04:35 2018

@author: prodipta
"""
from enum import Enum, unique
from transitions import Machine
from blueshift.utils.decorators import blueprint

@unique
class MODE(Enum):
    '''
        Track the current running mode - live or backtest.
    '''
    BACKTEST = 0
    LIVE = 1
    
@unique
class STATE(Enum):
    '''
        Track the current state of the machine.
    '''
    STARTUP = 0
    INITIALIZED = 1
    BEFORE_TRADING_START = 2
    TRADING_BAR = 3
    AFTER_TRADING_HOURS = 4
    HEARTBEAT = 5
    PAUSED = 6
    STOPPED = 7
    DORMANT = 8
    
@unique
class COMMAND(Enum):
    '''
        Set of acceptable commands for state transitions. Will only be
        processed for a live mode (ignored for backtest mode).
    '''
    RESUME = 0      # start user func processing, reschedule functions
    PAUSE = 1       # cancel open orders and stop user func processing
                    # also cancel any scheduled functions
    SQUAREOFF = 2   # cancel open orders and all close positions, then pause
    STOP = 4        # cancel open orders and shut down in orderly manner

@blueprint
class AlgoStateMachine():
    '''
        An implementation of state machine rules for an algorithm. States
        changes are triggered by two sets of events. One is the clock tick.
        The second is any command from channel (only for live algos).
    '''
    
    states = [s for s, v in STATE.__members__.items()]
    
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name","myalgo")
        self.mode = kwargs.pop("mode", MODE.BACKTEST)
        self._paused = False
        
        '''
            Clock transitions:
            Ignoring state altering commands, any backtest can move like:
            dormant -> startup -> before trading start -> trading bar ->
            after trading hours -> dromant. For a live algo, if started on 
            a trading hour, it will be dormant -> startup -> 
            before trading start -> trading bar -> after trading hours -> 
            heartbeat -> before trading -> trading bar -> after trading hours
            -> heartbeat and so on. If started on a non-trading hour, it can
            jump from initialize to heartbeat. So dormant -> initialize ->
            hearbeat -> before start -> hear beat -> trading bars -> after
            trading -> hearbeat and so on. On stop from any signal it goes
            to `stopped` state.
        '''
        transitions = [
        {'trigger':'fsm_initialize','source':'STARTUP','dest':'INITIALIZED'},
        {'trigger':'fsm_before_trading_start','source':'HEARTBEAT','dest':'BEFORE_TRADING_START'},
        {'trigger':'fsm_before_trading_start','source':'INITIALIZED','dest':'BEFORE_TRADING_START'},
        {'trigger':'fsm_before_trading_start','source':'AFTER_TRADING_HOURS','dest':'BEFORE_TRADING_START'},
        {'trigger':'fsm_handle_data','source':'BEFORE_TRADING_START','dest':'TRADING_BAR'},
        {'trigger':'fsm_handle_data','source':'HEARTBEAT','dest':'TRADING_BAR'},
        {'trigger':'fsm_handle_data','source':'TRADING_BAR','dest':'TRADING_BAR'},
        {'trigger':'fsm_after_trading_hours','source':'TRADING_BAR','dest':'AFTER_TRADING_HOURS'},
        {'trigger':'fsm_after_trading_hours','source':'HEARTBEAT','dest':'AFTER_TRADING_HOURS'},
        {'trigger':'fsm_heartbeat','source':'AFTER_TRADING_HOURS','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'BEFORE_TRADING_START','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'INITIALIZED','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'HEARTBEAT','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'TRADING_BAR','dest':'HEARTBEAT'},
        {'trigger':'fsm_analyze','source':'*','dest':'STOPPED'},
        {'trigger':'fsm_pause','source':'*','dest':'PAUSED'}]
        
        self.machine = Machine(model=self,
                               states=AlgoStateMachine.states,
                               transitions=transitions,
                               initial="STARTUP")
        
        self.machine.add_transition('fsm_pause','*','PAUSED',
                                     conditions  = 'is_running',
                                     after='set_pause')
        self.machine.add_transition('fsm_resume','PAUSED','STARTUP',
                                     before='reset_pause')
        
    
    def is_running(self):
        return not self._paused
    
    def set_pause(self):
        self._paused = True
        
    def reset_pause(self):
        self._paused = False
    
    