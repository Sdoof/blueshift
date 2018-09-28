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
    
cdef class Trade:
    # class declaration for cimport
    cdef readonly int tid
    cdef readonly int hashed_tid
    cdef readonly object oid
    cdef readonly object broker_order_id
    cdef readonly object exchange_order_id
    cdef readonly int instrument_id
    cdef readonly int sid
    cdef readonly object symbol
    cdef readonly object exchange_name
    cdef readonly object side
    cdef readonly int product_type
    cdef readonly float average_price
    cdef readonly object exchange_timestamp
    cdef readonly object timestamp
    cdef readonly int quantity
    
    cpdef to_dict(self)
    cpdef __reduce__(self)