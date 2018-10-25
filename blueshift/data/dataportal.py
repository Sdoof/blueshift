# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 01:28:32 2018

@author: prodi
"""
from abc import ABC, abstractmethod
from enum import Enum

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
        
        