# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython

cdef enum ProductType:
    INTRADAY = 0,
    DELIVERY = 1
    
cdef enum OrderFlag:
    NORMAL = 0,
    AMO = 1             # after markets order, schedule next day
    
cdef enum OrderType:
    MARKET = 0,
    LIMIT = 1,
    STOPLOSS = 2,
    STOPLOSS_MARKET = 3
    
cdef enum OrderValidity:
    DAY = 0,
    IOC = 1,            # Immedeate or Cancel
    GTC = 2             # Good till cencelled
    
cdef enum OrderSide:
    BUY = 0,
    SELL = 1
    
cdef enum OrderStatus:
    COMPLETE = 0,
    OPEN = 1,
    REJECTED = 2,
    CANCELLED = 3
    
cdef enum OrderUpdateType:
    EXECUTION = 0       # full or partial execution
    CANCEL = 1          # cancelled - full or remaining - by user
    MODIFICATION = 2    # user posted modification request
    REJECT = 3          # rejected by the execution platform
    

    
    