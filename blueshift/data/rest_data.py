# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 14:20:31 2018

@author: prodipta
"""
import pandas as pd
from abc import ABC, abstractmethod
import time

class RESTData(ABC):
    
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name","")
        self._trading_calendar = kwargs.get("trading_calendar",None)
        self._api = kwargs.get("api",None)
        self._auth = kwargs.get("auth",None)
        # calls per period
        self._rate_limit = kwargs.get("rate_limit",None)
        # limit period in sec
        self._rate_period = kwargs.get("rate_period",1) 
        # running count
        self._rate_limit_count = self._rate_limit
        # time since last limit reset
        self._rate_limit_since = None
        # max instruments that can be queried at one call
        self._max_instruments = kwargs.get("max_instruments",None)
        self._asset_finder = kwargs.get("asset_finder",None)
        
        
        
    @property
    def name(self):
        return self._name
    
    @property
    def api(self):
        return self._api
    
    @property
    def auth(self):
        return self._auth
    
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
    
    @property
    def tz(self):
        return self._trading_calendar.tz
    
    @property
    def asset_finder(self):
        return self._asset_finder
    
    @abstractmethod
    def current(assets, fields):
        raise NotImplementedError
        
    @abstractmethod
    def history(assets, fields):
        raise NotImplementedError
        
    def __str__(self):
        return "REST Data:%s" % self.name
    
    def __repr__(self):
        return self.__str__()
    
    def reset_rate_limits(self):
        '''
            Reset limit consumption and timing
        '''
        self._rate_limit_count = self._rate_limit
        self._rate_limit_since = pd.Timestamp.now(self.tz)
        
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
        time.sleep(self._rate_period*mult)
        