# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython

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