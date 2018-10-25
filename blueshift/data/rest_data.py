# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 14:20:31 2018

@author: prodipta
"""

from abc import ABC, abstractmethod

class RESTData(ABC):
    
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name","")
        self._trading_calendar = kwargs.get("trading_calendar",None)
        self._api = kwargs.get("api",None)
        self._auth = kwargs.get("auth",None)
        self._rate_limit = kwargs.get("rate_limit",None) # calls per minute
        self._rate_limit_count = self._rate_limit # running count
        # max instruments that can be queried at one call
        self._max_instruments = kwargs.get("max_instruments",None)
        self._asset_finder = kwargs.get("asset_finder",None)
        
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
    def tz(self):
        return self._trading_calendar.tz
    
    @abstractmethod
    def current(assets, fields):
        raise NotImplementedError
        
    @abstractmethod
    def history(assets, fields):
        raise NotImplementedError
        