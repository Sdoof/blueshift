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
Created on Thu Nov 15 09:25:15 2018

@author: prodipta
"""
from collections import namedtuple
import re
from pytz import all_timezones as pytz_all_timezones
import click
import pandas as pd
from datetime import datetime
from enum import Enum, unique

NANO_SECOND = 1000000000

'''
    Sentinel for a generic function.
'''
def noop(*args, **kwargs):
    # pylint: disable=unused-argument
    pass

'''
    Data type for a broker tuples, that contains all information to 
    login, find assets, get data and execute orders for a broker.
'''
Broker = namedtuple("Broker",('auth', 'asset_finder', 'data_portal', 
                              'broker', 'clock', 'modes'))

'''
    Data type for passing command on the command channel to the running
    algorithm.
'''
Command = namedtuple("Command",("cmd","args","kwargs"))

class HashKeyType(click.ParamType):
    name = 'SHA or MD5 string type'
    def __init__(self, length=32):
        super(HashKeyType, self).__init__()
        self.length = length
        
    def convert(self, value, param, ctx):        
        pattern = "^[0-9a-zA-Z]{"+str(self.length)+"}$"
        matched = re.match(pattern, value)
        if not matched:
            self.fail(f'{value} is not a valid SHA/ MD5 key', param, ctx)
        return value
    
class TimezoneType(click.ParamType):
    name = 'Standard time zone names'
    def convert(self, value, param, ctx):
        valid = str(value) in pytz_all_timezones
        if not valid:
            self.fail(f'{value} is not a valid time zone', param, ctx)
        return value
    
class DateType(click.ParamType):
    name = 'Date input'
    def __init__(self):
        strformats = ['%Y-%m-%d', '%d-%b-%Y', '%Y-%b-%d']
        self.formats = strformats
        super(DateType, self).__init__()
        
    def _try_to_convert_date(self, value, format):
        try:
            return datetime.strptime(value, format)
        except ValueError:
            return None
        
    def convert(self, value, param, ctx):
        for format in self.formats:
            dt = self._try_to_convert_date(value, format)
            if dt:
                return pd.Timestamp(dt)
            
        self.fail(
            'invalid datetime format: {}. (choose from {})'.format(
                value, ', '.join(self.formats)))
        
@unique
class MODE(Enum):
    '''
        Track the current running mode of algo - live or backtest.
    '''
    BACKTEST = 0
    LIVE = 1
    
@unique
class STATE(Enum):
    '''
        Track the current state of the algo state machine.
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

class DataPortalFlag(Enum):
    '''
        A flag for different types of data sources
    '''
    FILEBASE = 1
    DATABASE = 2
    REST = 4
    WEBSOCKETS = 8
    
'''
    A list for the OHLCV fields.
'''
OHLCV_FIELDS = ['open', 'high', 'low', 'close', 'volume']

class AuthType(Enum):
    '''
        Auth types. It can be either token based (where the token is
        obtained by means outside the scope of this package). For 
        every subsequent request, this token is passed for 
        validation of the API access. The other method (IB) is using
        a dedicated external app that mediates communication - this
        is the TWS mode.
    '''
    TOKEN = 0
    TWS = 1
    
class BrokerType(Enum):
    '''
        Types of brokers. TWS broker is specific to IB only.
    '''
    BACKTESTER = 0
    PAPERTRADER = 1
    RESTBROKER = 2
    TWSBROKER = 3
    