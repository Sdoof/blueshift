# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

# compile with <cythonize -i _assets.pyx>

cimport cython

cdef class MarketData:
    cdef readonly int sid
    cdef readonly hashed_id
    cdef readonly int mktdata_type
    cdef readonly object symbol
    cdef readonly object name
    cdef readonly object start_date
    cdef readonly object end_date
    cdef readonly object ccy
    cpdef to_dict(self)
    cpdef __reduce__(self)
    
cdef class Asset(MarketData):
    cdef readonly int asset_class
    cdef readonly int instrument_type
    cdef readonly float mult
    cdef readonly float tick_size
    cdef readonly object auto_close_date
    cdef readonly object exchange_name
    cdef readonly object calendar_name
    cpdef to_dict(self)
    cpdef __reduce__(self)
    
cpdef enum AssetClass:
    EQUITY = 0,
    FOREX = 1,
    COMMODITY = 2,
    RATES = 3,
    CASH = 4,
    CRYPTO = 5,
    VOL = 6
    
cpdef enum InstrumentType:
    SPOT = 0,
    FUTURES = 1,
    OPT = 2,
    FUNDS = 3,
    CFD = 4,
    STRATEGY = 6
    
cpdef enum MktDataType:
    OHLCV = 0,       # full OHLCV price data tied to a sym
    SERIES = 1,      # single point series data tied to a sym
    GENERAL = 2,     # general purpose multi-column data for a sym