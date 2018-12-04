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
Created on Mon Sep 24 11:51:36 2018

@author: prodipta
"""
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, time
import json

from blueshift.utils.exceptions import SessionOutofRange
from blueshift.utils.cutils import check_input
from blueshift.utils.decorators import blueprint

# constat values
NANO = 1000000000

# defaults for calendar creations
START_DATE = pd.Timestamp('1990-01-01 00:00:00')
END_DATE = pd.Timestamp(datetime.now().date()) + \
                pd.Timedelta(weeks=52)
OPEN_TIME = (10,0,0)
CLOSE_TIME = (16,0,0)

def np_search(array, value):
    '''
        return index position if a match if found, else -1
    '''
    idx = np.where(array==value)[0]
    if idx:
        return idx[0]
    return -1

def valid_timezone(tz):
    '''
        check if a timezone string is valid
    '''
    return (str(tz) in pytz.all_timezones)

def make_consistent_tz(dt, tz):
    '''
        Given a datetime and a timezone, ensure the datetime in the 
        same timezone.
    '''
    if dt.tz is None:
        dt = pd.Timestamp(dt, tz=tz)
    else:
        dt = dt.tz_convert(tz=tz)
    return dt

def days_to_nano(dts, tz, weekends):
    '''
        convert a list of bizdays to a list of sessions in nanos
    '''
    dtsn = []
    # TODO: optimize this function
    if dts is None:
        start = make_consistent_tz(START_DATE, tz)
        end = make_consistent_tz(END_DATE, tz)
        n_days = (end - start).days + 1
        dts = [start + pd.Timedelta(days=i) for i
               in range(n_days)
               if (start + pd.Timedelta(days=i)).weekday() not in weekends]
    else:
        dts = [pd.Timestamp(dt.date()) for dt in dts
               if dt.weekday() not in weekends]
    try:
        dts = pd.DatetimeIndex(dts)
        if dts.tz is None:
            dts = dts.tz_localize(tz)
        else:
            dts = dts.tz_convert(tz)
        dtsn = [dt.value for dt in dts]
    except Exception as e:
        raise(e)
        
    return np.asarray(dtsn)

def date_to_nano(dt, tz):
    '''
        Convert the datetime to the given timezone and returns the
        nanosecond since the epoch
    '''
    dt = make_consistent_tz(dt, tz)
    return dt.value

def date_to_nano_midnight(dt, tz):
    '''
        Convert the datetime to the given timezone =, normalize and 
        returns the nanosecond since the epoch
    '''
    dt = make_consistent_tz(dt, tz)
    dt = dt.normalize()
    return dt.value

@blueprint
class TradingCalendar(object):
    '''
        Base trading calendar. Takes in a list of bizdays and standard
        weekends and create a list of valid trading sessions between
        dates.
    '''
    def __init__(self, name=None, tz='Etc/UTC', opens=OPEN_TIME,
                 closes=CLOSE_TIME, bizdays = None, weekends=[5,6]):
        self._name = name
        assert valid_timezone(tz), 'Timezone is not valid'
        self._tz = tz
        self._saved_bizdays = bizdays
        self._saved_weekends = weekends
        self._bizdays = days_to_nano(bizdays, tz, weekends)
        open_time = time(*opens)
        self._open_nano = (open_time.hour*60 + open_time.minute)*60*NANO
        close_time = time(*closes)
        self._close_nano = (close_time.hour*60 + close_time.minute)*60*NANO
    
    @property
    def name(self):
        return self._name
    
    @property
    def tz(self):
        return self._tz
        
    @property
    def open_time(self):
        t = pd.Timestamp(self._bizdays[0] + self._open_nano,
                         tz=self._tz).time()
        return t
        
    @property
    def close_time(self):
        t = pd.Timestamp(self._bizdays[0] + self._close_nano,
                         tz=self._tz).time()
        return t
        
    def __str__(self):
        return "Blueshift Trading Calendar [name:%s, timezone:%s]" % (self.name,
                                                       self.tz)
        
    def to_json(self):
        d = {}
        d['name'] = self._name
        d['tz'] = self._tz
        open_secs = int(self._open_nano/1E9)
        d['opens'] = (int(open_secs/3600), 
                         int(open_secs/60) % 60, 
                         open_secs % 60)
        close_secs = int(self._close_nano/1E9)
        d['closes'] = (int(close_secs/3600), 
                         int(close_secs/60) % 60, 
                         close_secs % 60)
        d['bizdays'] = self._saved_bizdays
        d['weekends'] = self._saved_weekends
        return json.dumps(d)
    
    @classmethod
    def from_json(cls, jsonstr:str):
        check_input(cls.from_json,locals())
        d = json.loads(jsonstr)
        
        return cls(d['name'],d['tz'],d['opens'],d['closes'],
                   d['bizdays'],d['weekends'])
    
    def __reduce__(self):
        open_secs = int(self._open_nano/1E9)
        opens = (int(open_secs/3600), 
                         int(open_secs/60) % 60, 
                         open_secs % 60)
        close_secs = int(self._close_nano/1E9)
        closes = (int(close_secs/3600), 
                         int(close_secs/60) % 60, 
                         close_secs % 60)
        
        return (self.__class__,(self._name,
                                self._tz,
                                opens,
                                closes,
                                self._saved_bizdays,
                                self._saved_weekends))
    
    def __repr__(self):
        return self.__str__()
    
    def is_holiday(self, dt):
        '''
            check for holiday
        '''
        return not self.is_session(dt)
    
    def is_session(self, dt):
        '''
            check if it is a valid session
        '''
        dtm = date_to_nano_midnight(dt,self._tz)
        if np_search(self._bizdays,dtm) > 0:
            return True
        return False
        
    def is_open(self, dt):
        '''
            check for a open session
        '''
        dtn = date_to_nano(dt,self._tz)
        dtnm = date_to_nano_midnight(dt, self._tz)
        if self.is_session(dt):
            nanos = dtn - dtnm
            if nanos >= self._open_nano and nanos <= self._close_nano:
                return True
        return False
        
    def next_open(self, dt):
        '''
            returns next open session time
        '''
        dtn = date_to_nano_midnight(dt,self._tz)
        idx = np.searchsorted(self._bizdays,dtn)
        if self._bizdays[idx] == dtn:
            idx = idx+1
        if idx < len(self._bizdays):
            return pd.Timestamp(self._bizdays[idx] + self._open_nano,
                                tz=self._tz)
        else:
            raise SessionOutofRange
        
    def previous_open(self, dt):
        '''
            returns previous open session time
        '''
        dtn = date_to_nano_midnight(dt,self._tz)
        idx = np.searchsorted(self._bizdays,dtn) - 1
        if idx >= 0:
            return pd.Timestamp(self._bizdays[idx] + self._open_nano,
                                tz=self._tz)
        else:
            raise SessionOutofRange
        
    def next_close(self, dt):
        '''
            returns next close session time
        '''
        dtn = date_to_nano_midnight(dt,self._tz)
        idx = np.searchsorted(self._bizdays,dtn)
        if self._bizdays[idx] == dtn:
            idx = idx+1
        if idx < len(self._bizdays):
            return pd.Timestamp(self._bizdays[idx] + self._close_nano,
                                tz=self._tz)
        else:
            raise SessionOutofRange(dt=dt)
        
    def previous_close(self, dt):
        '''
            returns previous close session time
        '''
        dtn = date_to_nano_midnight(dt,self._tz)
        idx = np.searchsorted(self._bizdays,dtn) - 1
        if idx >= 0:
            return pd.Timestamp(self._bizdays[idx] + self._close_nano,
                                tz=self._tz)
        else:
            raise SessionOutofRange(dt=dt)
        
    def sessions(self, start_dt, end_dt):
        '''
            list all valid sessions between dates, inclusive
        '''
        dt1 = date_to_nano_midnight(start_dt,self._tz)
        dt2 = date_to_nano_midnight(end_dt,self._tz)
        idx1 = np.searchsorted(self._bizdays,dt1)
        idx2 = np.searchsorted(self._bizdays,dt2)
        if self._bizdays[idx2] ==  dt2:
            idx2 = idx2 + 1
        idx2 = max(idx2, idx1+1)
        
        return pd.to_datetime(self._bizdays[idx1:idx2]).\
                tz_localize('Etc/UTC').tz_convert(self._tz)
                
    def minutes(self, start_dt, end_dt):
        '''
            list all valid minutes between dates, inclusive
        '''
        raise NotImplementedError()
        
    def add_bizdays(self, dts):
        '''
            manually add business days. Expect Timestamp list.
        '''
        dtsn = days_to_nano(dts, self._tz, [])
        self._bizdays = np.unique(np.append(self._bizdays, dtsn))
        self._bizdays = np.sort(self._bizdays)
    
    def add_holidays(self, dts):
        '''
            manually add holiddays. Should be Timestamp list.
        '''
        dtsn = days_to_nano(dts, self._tz, [])
        sort_idx = self._bizdays.argsort()
        idx = sort_idx[np.searchsorted(self._bizdays,dtsn,sorter = sort_idx)]
        if idx.size > 0:
            self._bizdays = np.delete(self._bizdays,idx)
        
        