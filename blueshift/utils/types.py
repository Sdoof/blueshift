# -*- coding: utf-8 -*-
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
                              'broker', 'clock'))

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
        
