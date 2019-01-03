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
Created on Wed Jan  2 14:44:46 2019

@author: prodipta
"""

'''
see:
    https://code.activestate.com/recipes/577197-sortedcollection/
    https://docs.python.org/3/library/bisect.html
    https://docs.python.org/3/library/heapq.html
'''

import pandas as pd
from datetime import time
import heapq
from itertools import count

from blueshift.utils.calendars.trading_calendar import make_consistent_tz
from blueshift.utils.general_helpers import datetime_time_to_nanos
from blueshift.utils.exceptions import (InitializationError,
                                        ValidationError)

MAX_DAYS_AHEAD = 252

class date_rules(object):
    '''
        Wrapper class to expose different date scheduling rules.
    '''
    
    def __init__(self):
        self.trigger_dates = None
    
    @classmethod
    def month_start(cls, days_offset=0):
        def func(sessions):
            dts = pd.Series(sessions).groupby([sessions.year, 
                           sessions.month]).nth(days_offset)
            return [dt.normalize().value for dt in dts]
        return func
    
class time_rules(object):
    '''
        Wrapper class to expose different time scheduling rules.
    '''
    
    def __init__(self):
        self.trigger_dates = None
    
    @classmethod
    def market_open(cls, minutes=0, hours=0):
        def func(session_open):
            dt = datetime_time_to_nanos(session_open) + \
                datetime_time_to_nanos(time(hour=hours, minute=minutes))
            return [dt]
        return func

class TimeRule(object):
    '''
        Rule object that defines the trigger date and time. It takes inputs
        of date_rule and time_rule, apply the respective functions and 
        combine them by simple arithmetic. It maintains a pre-computed buffer
        of task schedule times and re-compute if necessary. It implements 
        next method to supply the next scheduled time for its task.
    '''
    def __init__(self, dt_func, time_func, start_dt, end_dt=None,
                 trading_calendar = None):
        self._dt_func = dt_func
        self._time_func = time_func
        
        self._trading_calendar = trading_calendar
        if not self._trading_calendar:
            raise InitializationError(msg="rule must be supplied calendar")
        
        self._start_dt = start_dt
        if self._start_dt:
            self._start_dt = make_consistent_tz(self._start_dt,
                                                self._trading_calendar.tz)
        self._end_dt = end_dt
        if self._end_dt:
            self._end_dt = make_consistent_tz(self._end_dt, 
                                              self._trading_calendar.tz)
        
        self._trigger_dts = None
        self._trigger_idx = -1
        
        self._calc_dts()
        
    def _calc_dts(self):
        if not self._start_dt:
            raise ValidationError(msg="rule start_date cannot be None")
        
        if not self._end_dt:
            self._end_dt = self._start_dt + pd.Timedelta(days=MAX_DAYS_AHEAD)
        
        sessions = self._trading_calendar.sessions(self._start_dt, 
                                                   self._end_dt)
        mkt_open = self._trading_calendar.open_time
        dt_dates = self._dt_func(sessions)
        dt_times = self._time_func(mkt_open)
        
        self._trigger_dts = [dt1 + dt2 for dt1 in dt_dates \
                             for dt2 in dt_times]
        if len(self._trigger_dts) < 1:
            raise ValidationError(msg="failed to create task schedules")
    
    def __next__(self):
        self._trigger_idx = self._trigger_idx + 1
        if self._trigger_idx < len(self._trigger_dts):
            return self._trigger_dts[self._trigger_idx]
        
        self._start_dt = self._end_dt
        self._calc_dts()
        self._trigger_idx = 0
        return self._trigger_dts[self._trigger_idx]
    
    def __iter__(self):
        return self
    
class Event(object):
    '''
        Time-based event class - associates a callable with a rule and a time.
        The rule object, when called, returns the next call dt. The callable
        always has the signature of function(context, data).
    '''
    
    def __init__(self, rule, fn):
        self._rule = rule
        self._fn = fn
        self._dt = next(self._rule)
        self._order = None
    
    @property
    def dt(self):
        return self._dt
    
    @property
    def order(self):
        return self._order
    
    @order.setter
    def order(self, order):
        self._order = order
    
    def __iter__(self):
        return self
    
    def __next__(self):
        self._dt = next(self._rule)
        return self

class Scheduler(object):
    '''
        Class to manage scheduled events (events based on time-stamp). The 
        core parts are a queue and a method to check the queue on request.
    '''
    def __init__(self):
        self._events = []
        self._next_dt = None
        self.counter = count()
        
    def add_event(self, event):
        event.order = next(self.counter)
        heapq.heappush(self._events, event)
        
    def trigger_events(self, context, data, dt):
        if dt < self._evensts[0]:
            pass
        
        
def schedule_function(fn, date_rule=None, time_rule=None):
    '''
        function exposing the scheduling machinery.
    '''
    if not date_rule and not time_rule:
        return
    
    pass
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    