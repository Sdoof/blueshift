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
Created on Thu Oct  4 08:54:16 2018

@author: prodipta
"""

import pandas as pd
cimport numpy as np
import numpy as np
from blueshift.utils.calendars.trading_calendar import TradingCalendar

cpdef enum BARS:
    ALGO_START = 0
    BEFORE_TRADING_START = 1
    TRADING_BAR = 2
    AFTER_TRADING_HOURS = 3
    ALGO_END = 4
    HEAR_BEAT = 5
    
NANO_SECOND = 1000000000
    
cdef class TradingClock(object):
    
    def __init__(self, object trading_calendar, 
                 int emit_frequency):
        self.trading_calendar = trading_calendar
        self.emit_frequency = emit_frequency
        
        open_time = self.trading_calendar.open_time
        close_time = self.trading_calendar.close_time
        
        self.open_nano = (((open_time.hour*60 + open_time.minute)*60\
                  + open_time.second)*1000000 + 
                    open_time.microsecond)*1000
        self.close_nano = (((close_time.hour*60 + close_time.minute)*60\
                      + close_time.second)*1000000 + 
                        close_time.microsecond)*1000
        
        self.before_trading_start_nano = self.open_nano \
                                            - 3600*NANO_SECOND
        self.after_trading_hours_nano = self.close_nano \
                                            + 3600*NANO_SECOND
        self.generate_intraday_nanos()
    
    def __iter__(self):
        raise StopIteration
        
    cdef generate_intraday_nanos(self):
        cdef int n
        cdef np.int64_t period
        
        n= int((self.close_nano - self.open_nano)/NANO_SECOND/60/self.emit_frequency)
        
        period = self.emit_frequency*60*NANO_SECOND
        self.intraday_nanos = np.asarray([self.open_nano + 
                                          i*period for i in range(n+1)])
        if self.intraday_nanos[-1] >= self.close_nano:
            self.intraday_nanos = self.intraday_nanos[:-1]
        
cdef class SimulationClock(TradingClock):
    
    def __init__(self, object trading_calendar,
                           int emit_frequency,
                           object start_dt,
                           object end_dt):
        super(SimulationClock,self).__init__(trading_calendar,
             emit_frequency)
        self.start_nano = start_dt.value
        self.end_nano = end_dt.value
        sessions = trading_calendar.sessions(start_dt, end_dt)
        self.session_nanos = np.asarray([s.value for s in sessions])
        
    def __iter__(self):
        yield self.session_nanos[0], ALGO_START
        for session_nano in self.session_nanos:
            t = session_nano+self.before_trading_start_nano
            yield t, BEFORE_TRADING_START
        
            for intraday_nano in self.intraday_nanos:
                yield session_nano+intraday_nano, TRADING_BAR
            
            t = session_nano+self.after_trading_hours_nano
            yield t, AFTER_TRADING_HOURS
        
        yield t, ALGO_END
        
        
    def __str__(self):
        tz = self.trading_calendar.tz
        return f"Blueshift Simulation Clock [tick:{self.emit_frequency},tz:{tz}]"
                    
    def __repr__(self):
        return self.__str__()
        
        
        
        
        
        
        
        