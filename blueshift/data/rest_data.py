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
        