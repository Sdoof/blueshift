# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython
cimport _order_types
from blueshift.trades._order_types import (
        ProductType,
        OrderFlag,
        OrderType,
        OrderValidity,
        OrderSide,
        OrderStatus,
        OrderUpdateType)
from blueshift.trades._trade cimport Trade
from blueshift.assets._assets cimport Asset

cdef class Position:
    cdef readonly object pid
    cdef readonly object instrument_id
    cdef readonly Asset asset
    cdef readonly int quantity
    cdef readonly int buy_quantity
    cdef readonly float buy_price
    cdef readonly int sell_quantity
    cdef readonly float sell_price
    cdef readonly float pnl
    cdef readonly float realized_pnl
    cdef readonly float unrealized_pnl
    cdef readonly float last_price
    cdef readonly object timestamp
    cdef readonly float value
    cdef readonly float margin
    cdef readonly int product_type
    cpdef to_dict(self)
    cpdef __reduce__(self)
    cpdef update(self, Trade trade, float margin)
    cpdef if_closed(self)