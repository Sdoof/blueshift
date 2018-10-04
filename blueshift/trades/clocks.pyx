# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 08:54:16 2018

@author: prodipta
"""

import pandas as pd
cimport numpy as np
import numpy as np
from blueshift.utils.calendars.trading_calendar import TradingCalendar

cpdef enum BARS:
    ALGO_START = 0
    BEFORE_TRADING_START = 1
    TRADING_BAR = 2
    AFTER_TRADING_HOURS = 3
    ALGO_END = 4
    HEAR_BEAT = 5
    
cdef class TradingClock(object):
    cdef object trading_calendar
    cdef object start_dt
    cdef object end_dt
    cdef int emit_frequency
    
    def __init__(self):