# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 09:25:15 2018

@author: prodipta
"""

import re
import pytz
import click
import pandas as pd

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
    name = 'api-key'
    def convert(self, value, param, ctx):
        valid = str(value) in pytz.all_timezones
        if not valid:
            self.fail(f'{value} is not a valid time zone', param, ctx)
        return value
    
class DateType(click.DateTime):
    
    def __init__(self):
        strformats = ['%Y-%m-%d', '%d-%b-%Y', '%Y-%b-%d']
        super(DateType, self).__init__(strformats)
        
    def convert(self, value, param, ctx):
        for format in self.formats:
            dt = self._try_to_convert_date(value, format)
            if dt:
                return pd.Timestamp(dt)
            
        self.fail(
            'invalid datetime format: {}. (choose from {})'.format(
                value, ', '.join(self.formats)))
        
        