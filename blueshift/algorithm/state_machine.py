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
    STOPPED = 5
    HEARTBEAT = 6
    DORMANT = 7
    PAUSED = 8

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
        clock_transitions = [
        {'trigger':'fsm_start_up','source':'DORMANT','dest':'STARTUP'},
        {'trigger':'fsm_start_up','source':'STOPPED','dest':'STARTUP'},
        {'trigger':'fsm_initialize','source':'STARTUP','dest':'INITIALIZED'},
        {'trigger':'fsm_before_trading_start','source':'HEARTBEAT','dest':'BEFORE_TRADING_START'},
        {'trigger':'fsm_before_trading_start','source':'INITIALIZED','dest':'BEFORE_TRADING_START'},
        {'trigger':'fsm_handle_data','source':'BEFORE_TRADING_START','dest':'TRADING_BAR'},
        {'trigger':'fsm_handle_data','source':'HEARTBEAT','dest':'TRADING_BAR'},
        {'trigger':'fsm_handle_data','source':'TRADING_BAR','dest':'TRADING_BAR'},
        {'trigger':'fsm_after_trading_hours','source':'TRADING_BAR','dest':'AFTER_TRADING_HOURS'},
        {'trigger':'fsm_heartbeat','source':'AFTER_TRADING_HOURS','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'BEFORE_TRADING_START','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'INITIALIZED','dest':'HEARTBEAT'},
        {'trigger':'fsm_heartbeat','source':'HEARTBEAT','dest':'HEARTBEAT'},
        {'trigger':'fsm_analyze','source':'*','dest':'STOPPED'}]
        
        cmd_transitions = [
        {'trigger':'fsm_cmd_stop','source':'*','dest':'STOPPED'},
        {'trigger':'fsm_cmd_pause','source':'*','dest':'STOPPED'},
        {'trigger':'fsm_cmd_stop','source':'*','dest':'STOPPED'},
        {'trigger':'fsm_cmd_stop','source':'*','dest':'STOPPED'}
        ]
        
        transitions = clock_transitions
        
        self.machine = Machine(model=self,
                               states=AlgoStateMachine.states,
                               transitions=transitions,
                               initial="DORMANT")
        
        self.fsm_start_up()
    
    
    
    