# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:27:45 2018

@author: prodipta
"""

import pandas as pd
from enum import Enum

from kiteconnect.exceptions import KiteException

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import AbstractBrokerAPI, BrokerType
from blueshift.utils.brokers.zerodha.kiteauth import (KiteAuth,
                                                      KiteConnect3,
                                                      kite_calendar)
from blueshift.utils.cutils import check_input
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        BrokerAPIError)
from blueshift.blotter._accounts import EquityAccount

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"

class KiteBroker(AbstractBrokerAPI):
    
    def __init__(self, 
                 name:str="kite", 
                 broker_type:BrokerType=BrokerType.RESTBROKER, 
                 calendar:TradingCalendar=kite_calendar,
                 **kwargs):
        
        check_input(KiteBroker.__init__, locals())
        super(self.__class__, self).__init__(name, broker_type, calendar,
                                             **kwargs)
        self._auth = kwargs.get("auth",None)
        self._api = None
        
        if not self._auth:
            msg = "authentication and API missing"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
        
        if self._auth.__class__ != KiteAuth.cls:
            msg = "invalid authentication object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        self._api = self._auth._api
            
        if self._api.__class__ != KiteConnect3.cls:
            msg = "invalid kite API object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
    def __str__(self):
        return 'Broker:name:%s, type:%s'%(self._name, self._type)
    
    def __repr__(self):
        return self.__str__()
    
    def process_response(self, response):
        if response['status'] == ResponseType.SUCCESS.value:
            return response['data']
        else:
            msg = response['data']
            raise BrokerAPIError(msg=msg)
            
    def login(self, *args, **kwargs):
        self._auth.login(*args, **kwargs)
        
    def logout(self, *args, **kwargs):
        self._auth.logout()
        
    def profile(self, *args, **kwargs):
        try:
            return self._api.profile()
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.LOG
            raise BrokerAPIError(msg=msg, handling=handling)
        
    def account(self, *args, **kwargs):
        try:
            margins = self._api.margins()
            account = EquityAccount()
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    def positions(self, *args, **kwargs):
        pass
    
    def open_orders(self, *args, **kwargs):
        pass
    
    def order(self, order_id):
        pass
    
    def orders(self, *args, **kwargs):
        pass
    
    def tz(self, *args, **kwargs):
        pass
    
    def place_order(self, order):
        pass
    
    def update_order(self, order_id, *args, **kwargs):
        pass
    
    def cancel_order(self, order_id):
        pass
    
    def fund_transfer(self, amount):
        pass
    
    
    
    
        