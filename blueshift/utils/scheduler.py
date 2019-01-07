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

import bisect
import pandas as pd
from datetime import time
from pandas.tseries.offsets import MonthBegin, MonthEnd

from blueshift.utils.calendars.trading_calendar import make_consistent_tz
from blueshift.utils.general_helpers import datetime_time_to_nanos
from blueshift.utils.exceptions import ScheduleFunctionError
from blueshift.utils.types import noop, NANO_SECOND

MAX_DAYS_AHEAD = 252
MAX_MONTH_DAY_OFFSET = 15
MAX_WEEK_DAY_OFFSET = 2
MAX_MINUTE_OFFSET = 59
MAX_HOUR_OFFSET = 3

class date_rules(object):
    '''
        Wrapper class to expose different date scheduling rules.
    '''
    
    def __init__(self):
        self.trigger_dates = None
        
    def __str__(self):
        return "Blueshift date_rules"
    
    def __repr__(self):
        return self.__str__()
        
    @classmethod
    def every_day(cls):
        def func(sessions):
            return [dt.normalize().value for dt in sessions]
        
        func.date_rule = True
        return func
    
    @classmethod
    def week_start(cls, days_offset=0):
        days_offset = abs(int(days_offset))
        if days_offset > MAX_WEEK_DAY_OFFSET:
            raise ScheduleFunctionError(msg="invalid days offset supplied.")
            
        def func(sessions):
            dts = pd.Series(sessions).groupby([sessions.year, 
                           sessions.weekofyear]).nth(days_offset)
            return [dt.normalize().value for dt in dts]
        
        func.date_rule = True
        return func
    
    @classmethod
    def week_end(cls, days_offset=0):
        days_offset = abs(int(days_offset))
        if days_offset > MAX_WEEK_DAY_OFFSET:
            raise ScheduleFunctionError(msg="invalid days offset supplied.")
        days_offset = -days_offset -1
        
        def func(sessions):
            dts = pd.Series(sessions).groupby([sessions.year, 
                           sessions.month]).nth(days_offset)
            return [dt.normalize().value for dt in dts]
        
        func.date_rule = True
        return func
    
    @classmethod
    def month_start(cls, days_offset=0):
        days_offset = abs(int(days_offset))
        if days_offset > MAX_MONTH_DAY_OFFSET:
            raise ScheduleFunctionError(msg="invalid days offset supplied.")
        
        def func(sessions):
            dts = pd.Series(sessions).groupby([sessions.year, 
                           sessions.month]).nth(days_offset)
            return [dt.normalize().value for dt in dts]
        
        func.date_rule = True
        return func
    
    @classmethod
    def month_end(cls, days_offset=0):
        days_offset = abs(int(days_offset))
        if days_offset > MAX_MONTH_DAY_OFFSET:
            raise ScheduleFunctionError(msg="invalid days offset supplied.")
        days_offset = -days_offset -1
        def func(sessions):
            dts = pd.Series(sessions).groupby([sessions.year, 
                           sessions.month]).nth(days_offset)
            return [dt.normalize().value for dt in dts]
        
        func.date_rule = True
        return func
    
class time_rules(object):
    '''
        Wrapper class to expose different time scheduling rules.
    '''
    
    def __init__(self):
        self.trigger_dates = None
        
    def __str__(self):
        return "Blueshift time_rules"
    
    def __repr__(self):
        return self.__str__()
    
    @classmethod
    def market_open(cls, minutes=0, hours=0):
        minutes = abs(int(minutes))
        hours = abs(int(hours))
        if minutes > MAX_MINUTE_OFFSET:
            raise ScheduleFunctionError(msg="invalid minute offset supplied.")
        if hours > MAX_HOUR_OFFSET:
            raise ScheduleFunctionError(msg="invalid hour offset supplied.")
        
        def func(session_open, session_close):
            dt = datetime_time_to_nanos(session_open) + \
                datetime_time_to_nanos(time(hour=hours, minute=minutes))
            return [dt]
        
        func.time_rule = True
        return func
    
    @classmethod
    def AfterOpen(cls, minutes=0, hours=0):
        return cls.market_open(minutes, hours)
    
    @classmethod
    def market_close(cls, minutes=0, hours=0):
        minutes = abs(int(minutes))
        hours = abs(int(hours))
        if minutes > MAX_MINUTE_OFFSET:
            raise ScheduleFunctionError(msg="invalid minute offset supplied.")
        if hours > MAX_HOUR_OFFSET:
            raise ScheduleFunctionError(msg="invalid hour offset supplied.")
        def func(session_open, session_close):
            dt = datetime_time_to_nanos(session_close) - \
                datetime_time_to_nanos(time(hour=hours, minute=minutes))
            return [dt]
        
        func.time_rule = True
        return func
    
    @classmethod
    def BeforeClose(cls, minutes=0, hours=0):
        return cls.market_close(minutes, hours)
    
    @classmethod
    def every_nth_minute(cls, minutes=1):
        minutes = abs(int(minutes))
        if minutes > MAX_MINUTE_OFFSET:
            raise ScheduleFunctionError(msg="invalid minute step supplied.")
        if not minutes > 0:
            raise ScheduleFunctionError(msg="invalid minute step supplied.")
        
        def func(session_open, session_close):
            start_val = datetime_time_to_nanos(session_open)
            end_val = datetime_time_to_nanos(session_close)
            step = NANO_SECOND*60*minutes
            dts = [dt for dt in range(start_val, end_val, step)]
            return dts
        
        func.time_rule = True
        return func
    
    @classmethod
    def every_minute(cls):
        return cls.every_nth_minute(1)
    
    @classmethod
    def every_nth_hour(cls, hours=1):
        hours = abs(int(hours))
        if hours > MAX_HOUR_OFFSET:
            raise ScheduleFunctionError(msg="invalid hour step supplied.")
        if not hours > 0:
            raise ScheduleFunctionError(msg="invalid hour step supplied.")
        
        def func(session_open, session_close):
            start_val = datetime_time_to_nanos(session_open)
            end_val = datetime_time_to_nanos(session_close)
            step = NANO_SECOND*60*60*hours
            dts = [dt for dt in range(start_val, end_val, step)]
            return dts
        
        func.time_rule = True
        return func
    
    @classmethod
    def every_hour(cls):
        return cls.every_nth_hour(1)

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
            raise ScheduleFunctionError(msg="rule must be supplied calendar")
        
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
            self._start_dt = make_consistent_tz(pd.Timestamp.now().\
                                                normalize(), 
                                                self._trading_calendar.tz)
        
        if not self._end_dt:
            self._end_dt = self._start_dt + pd.Timedelta(days=MAX_DAYS_AHEAD)

        self._trigger_dts = self._trigger_dts_calc(self._start_dt,
                                                   self._end_dt)
        if len(self._trigger_dts) < 1:
            # try again, resetting end_dates
            self._end_dt = self._start_dt + pd.Timedelta(days=MAX_DAYS_AHEAD)
            self._trigger_dts = self._trigger_dts_calc(self._start_dt, 
                                                       self._end_dt)
            # if still no trigger dates, raise exceptions
            if len(self._trigger_dts) < 1:
                raise ScheduleFunctionError(msg="failed to create task schedules")
            
    def _trigger_dts_calc(self, start_dt, end_dt):
        # bump the dates to ensure we capture month start and end
        start_dt_use = start_dt - MonthBegin()
        end_dt_use = end_dt + MonthEnd()
        sessions = self._trading_calendar.sessions(start_dt_use, end_dt_use)
        mkt_open = self._trading_calendar.open_time
        mkt_close = self._trading_calendar.close_time
        dt_dates = self._dt_func(sessions)
        # we make sure the date ranges does not fall outside the start 
        # and end dates.
        dt_dates = [dt for dt in dt_dates if dt >= start_dt.value and\
                    dt <= end_dt.value]
        # we cannot do the same for times, for e.g. for 24 hour calendar
        # it becomes meaningless. open may be > close.
        dt_times = self._time_func(mkt_open, mkt_close)
        
        return [dt1 + dt2 for dt1 in dt_dates for dt2 in dt_times]
    
    def __next__(self):
        self._trigger_idx = self._trigger_idx + 1
        if self._trigger_idx < len(self._trigger_dts):
            return self._trigger_dts[self._trigger_idx]
        
        self._start_dt = self._end_dt
        self._end_dt = self._start_dt + pd.Timedelta(days=MAX_DAYS_AHEAD)
        self._calc_dts()
        self._trigger_idx = 0
        return self._trigger_dts[self._trigger_idx]
    
    def __iter__(self):
        return self
    
    def __str__(self):
        return "Blueshift Rules"
    
    def __repr__(self):
        return self.__str__()


class TimeEvent(object):
    '''
        Time-based event class - associates a callable with a rule and a time.
        The rule object, when called, returns the next call dt. The callable
        always has the signature of function(context, data).
    '''
    def __init__(self, rule, callback=None):
        self._dt = next(rule)
        self._rule=rule
        self._callback=callback if callback else noop
        
    def __iter__(self):
        return self
        
    def __next__(self):
        self._dt = next(self._rule)
        return self
        
    @property
    def dt(self):
        return self._dt
        
    @property
    def rule(self):
        return self._rule
    
    @property
    def callback(self):
        return self._callback
    
    def __int__(self):
        return int(self._dt)
    
    def __eq__(self, obj):
        return self.dt == int(obj)
    
    def __ne__(self, obj):
        return self.dt != int(obj)
    
    def __gt__(self, obj):
        return self.dt > int(obj)
    
    def __lt__(self, obj):
        return self.dt < int(obj)
    
    def __ge__(self, obj):
        return self.dt >= int(obj)
    
    def __le__(self, obj):
        return self.dt <= int(obj)
    
    def __str__(self):
        return "Blueshift time-based event"
    
    def __repr__(self):
        return self.__str__()

class Scheduler(object):
    '''
        Class to manage scheduled events (events based on time-stamp). The 
        core parts are a queue and a method to check the queue on request. 
        The implementation uses bisect insort_left to insert an incoming 
        event to the first possible sorted position, and also uses bisect
        bisect_right to retrieve all pending tasks for a given nano. The
        event trigger method returns early in case the task queue is empty
        or the task with the nearest future nano is higher than the current
        nano. Else it removes and processes all hits and re-insert them 
        after updating the next call nano.
    '''
    def __init__(self):
        self._events = []
        self._next_dt = None
        
    def add_event(self, event):
        bisect.insort_left(self._events, event)
        self._next_dt = self._events[0].dt
        
    def trigger_events(self, context, data, dt):
        if not self._events:
            return
        
        if dt < self._next_dt:
            return
        
        pos = bisect.bisect_right(self._events, dt)
        if pos == 0:
            return
        
        callback_list = self._events[:pos]
        self._events = self._events[pos:]
        
        for e in callback_list:
            self.add_event(next(e))
            e.callback(context, data)
    
    def __str__(self):
        return "Blueshift tasks scheduler"
    
    def __repr__(self):
        return self.__str__()
    
    
    
    
    
    
    
    
    
    
    
    
    
    