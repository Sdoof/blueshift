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

"""

from transitions import Machine
from blueshift.utils.decorators import blueprint
from blueshift.utils.types import MODE, STATE
from blueshift.configs.runtime import blueshift_run_get_name


@blueprint
class AlgoStateMachine():
    """ 
        An implementation of state machine rules for an algorithm. States
        changes are triggered by two sets of events. One is the clock tick.
        The second is any command from channel (i.e. user interaction, 
        only for live mode).
        
        Note:
            Clock transitions: ignoring state altering commands, any 
            backtest can move like dormant -> startup -> before trading 
            start -> trading bar -> after trading hours -> dromant. 
            For a live algo, if started on a trading hour, it will be 
            dormant -> startup -> before trading start -> trading bar -> 
            after trading hours -> heartbeat -> before trading -> trading 
            bar -> after trading hours -> heartbeat and so on. If started 
            on a non-trading hour, it can jump from initialize to heartbeat. 
            So dormant -> initialize -> hearbeat -> before start -> heart 
            beat -> trading bars -> after trading -> hearbeat and so on. 
            On stop from any signal it goes to `stopped` state.
            
        Args:
            ``name (str)``: A name for the state machine
            
            ``mode (int)``: Mode of the machine (live or backtest)
    """
    
    states = [s for s, v in STATE.__members__.items()]
    """ complete set of possible machine states. """
    
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name",blueshift_run_get_name())
        self.mode = kwargs.pop("mode", MODE.BACKTEST)
        self._paused = False

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
        self.machine.add_transition('fsm_stop','*','STOPPED')
        
    
    def is_running(self):
        """ returns True if we are in a running state """
        return not self._paused
    
    def set_pause(self):
        """ set the machine state to pause """
        self._paused = True
        
    def reset_pause(self):
        """ un-pause the state of the machine """
        self._paused = False
    
    