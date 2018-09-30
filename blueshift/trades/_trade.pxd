# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython

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