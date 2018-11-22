# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython

cpdef enum ProductType:
    INTRADAY = 0,
    DELIVERY = 1
    
cpdef enum OrderFlag:
    NORMAL = 0,
    AMO = 1             # after markets order, schedule next day
    
cpdef enum OrderType:
    MARKET = 0,         # market order
    LIMIT = 1,          # limit order
    STOPLOSS = 2,       # stop-limit order
    STOPLOSS_MARKET = 3 # stoploss order
    
cpdef enum OrderValidity:
    DAY = 0,
    IOC = 1,            # Immedeate or Cancel
    GTC = 2             # Good till cencelled
    
cpdef enum OrderSide:
    BUY = 0,
    SELL = 1
    
cpdef enum OrderStatus:
    COMPLETE = 0,
    OPEN = 1,
    REJECTED = 2,
    CANCELLED = 3
    
cpdef enum OrderUpdateType:
    EXECUTION = 0       # full or partial execution
    CANCEL = 1          # cancelled - full or remaining - by user
    MODIFICATION = 2    # user posted modification request
    REJECT = 3          # rejected by the execution platform
    

    
    