# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

# compile with <cythonize -i _assets.pyx>

cimport cython

cdef class MarketData:
    cdef readonly int sid
    cdef readonly int hashed_sid
    cdef readonly int mktdata_type
    cdef readonly object symbol
    cdef readonly object name
    cdef readonly object start_date
    cdef readonly object end_date
    cpdef to_dict(self)
    cpdef __reduce__(self)
    
cdef class Asset(MarketData):
    cdef readonly int asset_class
    cdef readonly int instrument_types
    cdef readonly float mult
    cdef readonly float tick_size
    cdef readonly object auto_close_date
    cdef readonly object exchange_name
    cdef readonly object calendar_name
    cpdef to_dict(self)
    cpdef __reduce__(self)