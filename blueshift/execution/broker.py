# -*- coding: utf-8 -*-
"""
Created on Sat Oct  6 11:51:35 2018

@author: prodipta
"""

from abc import ABC, abstractmethod, abstractproperty
from enum import Enum

class BrokerType(Enum):
    BACKTESTER = 0
    PAPERTRADER = 1
    RESTBROKER = 2
    TWSBROKER = 3


class AbstractBrokerAPI(ABC):
    
    def __init__(self, name, broker_type, calendar):
        self.broker_name = name
        self.authentication_token = None
        self.type = broker_type
        self.calendar = calendar
        
    def __str__(self):
        return "Broker: name:%s" % (self.broker_name)
    
    def __repr__(self):
        return self.__str__()
        
    @abstractmethod
    def login(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def logout(self, *args, **kwargs):
        pass
    
    @abstractproperty
    def profile(self):
        pass
    
    @abstractproperty
    def account(self):
        pass
    
    @abstractproperty
    def positions(self):
        pass
    
    @abstractproperty
    def order(self, order_id):
        pass
    
    @abstractproperty
    def open_orders(self):
        pass
    
    @abstractproperty
    def orders(self):
        pass
    
    @abstractproperty
    def timezone(self):
        pass
    
    @abstractmethod
    def place_order(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def update_order(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def cancel_order(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def fund_transfer(self, *args, **kwargs):
        pass
    