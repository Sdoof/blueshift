# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 08:54:16 2018

@author: prodipta
"""

cimport cython
cimport numpy as np
import numpy as np

cdef class TradingClock(object):
    cdef readonly object trading_calendar
    cdef public int emit_frequency
    cdef readonly np.int64_t open_nano
    cdef readonly np.int64_t close_nano
    cdef readonly np.int64_t before_trading_start_nano
    cdef readonly np.int64_t after_trading_hours_nano
    cdef readonly np.int64_t[:] intraday_nanos
    cdef readonly generate_intraday_nanos(self)
    
cdef class SimulationClock(TradingClock):
    cdef readonly np.int64_t start_nano
    cdef readonly np.int64_t end_nano
    cdef readonly np.int64_t[:] session_nanos