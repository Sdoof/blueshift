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
Created on Mon Nov  5 16:19:35 2018

@author: prodipta
"""
from pandas import Timestamp
from time import sleep

from blueshift.utils.exceptions import StateMachineError

class StateMachineMixin(object):
    '''
        A simple state machine
    '''
    def __init__(self, init_state, transition_dict):
        self._current_state = init_state
        self._transition_dict = transition_dict
        
    
    @property
    def state(self):
        return self._current_state
    
    @state.setter
    def state(self, to_state):
        if to_state not in self._transition_dict[self._current_state]:
            strmsg = f"Illegal state change from {self._current_state}\
                        to {to_state}"
            raise StateMachineError(msg=strmsg)
            
        self._current_state = to_state
        
class APIRateLimitMixin(object):
    
    def __init__(self, *args, **kwargs):
        # we need a trading calendar to compare timestamps
        self._trading_calendar = kwargs.get("trading_calendar",None)
        # calls per period
        self._rate_limit = kwargs.get("rate_limit",None)
        # limit period in sec
        self._rate_period = kwargs.get("rate_period",1) 
        # running count
        self._rate_limit_count = self._rate_limit
        # time since last limit reset
        self._rate_limit_since = None
    
    @property
    def tz(self):
        return self._trading_calendar.tz
    
    @property
    def rate_limit(self):
        return self._rate_limit
    
    @property
    def rate_period(self):
        return self._rate_period
    
    @property
    def rate_limit_since(self):
        return self._rate_limit_since
    
    @rate_limit_since.setter
    def rate_limit_since(self, value):
        self._rate_limit_since = value
    
    @property
    def rate_limit_count(self):
        return self._rate_limit_count
    
    @rate_limit_count.setter
    def rate_limit_count(self, value):
        self._rate_limit_count = max(0, value)
        
    def reset_rate_limits(self):
        '''
            Reset limit consumption and timing
        '''
        self._rate_limit_count = self._rate_limit
        self._rate_limit_since = Timestamp.now(self.tz)
        
    def update_rate_limits(self, rate_limit, rate_period=None):
        '''
            Update rate limits parameters on the fly
        '''
        self._rate_limit = rate_limit
        if rate_period:
            self._rate_period = rate_period
            
    def cool_off(self, mult=1):
        '''
            blocking sleep to cool off rate limit violation
        '''
        sleep(self._rate_period*mult)

        
    
    
    
    
    
    
    
    
    
    
    
    