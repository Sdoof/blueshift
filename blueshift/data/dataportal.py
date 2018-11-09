# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 01:28:32 2018

@author: prodi
"""
from abc import ABC, abstractmethod, abstractproperty
from enum import Enum

OHLCV_FIELDS = ['open', 'high', 'low', 'close', 'volume']

class DataPortalFlag(Enum):
    FILEBASE = 1
    DATABASE = 2
    REST = 4
    WEBSOCKETS = 8

class DataPortal(ABC):
    '''
        Abstract class for handling all the data needs for an algo. This
        encapsulates database reader for backtester portal and db + 
        broker RESTful API + websockets for live trading
    '''
    def __init__(self, *args, **kwargs):
        pass
        
    @abstractproperty
    def name(self):
        raise NotImplementedError
    
    @abstractproperty
    def tz(self):
        raise NotImplementedError
    
    @abstractproperty
    def asset_finder(self):
        raise NotImplementedError
    
    @abstractmethod
    def current(assets, fields):
        raise NotImplementedError
        
    @abstractmethod
    def history(assets, fields):
        raise NotImplementedError
        
class DBDataPortal(DataPortal):
    '''
        Abstract class for handling all the data needs for an algo. This
        encapsulates database reader for backtester portal and db + 
        broker RESTful API + websockets for live trading
    '''
    
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name","blueshift")
    
    @property
    def name(self):
        return self._name
    
    @property
    def tz(self):
        pass
    
    @property
    def asset_finder(self):
        pass
    
    @property
    def auth(self):
        return None
    
    def current(assets, fields):
        pass
        
    def history(assets, fields):
        pass
    
    def __str__(self):
        return "DB Data:%s" % self.name
    
    def __repr__(self):
        return self.__str__()