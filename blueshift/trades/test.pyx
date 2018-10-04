
cimport cython
import random
import pandas as pd
from blueshift.utils.calendars.trading_calendar import TradingCalendar

cdef int execute(object order):
    return int(random.random()*10)

def clock_fn():
    cdef int bar = 0
    for i in range(1752000):
        yield bar

def execution():
    cdef int run = True
    cdef int order

    while run:
        order = yield
        if order == -1:
            run = False
            continue
        #print("execute order {}".format(order))
        order =  execute(order)
        yield order
        
cpdef algo2():
    cdef int i
    cdef int order
    
    broker = execution()
    clock = clock_fn()
    for bar in clock:
        order = int(random.random()*10)
        if order < 0.1:
            #print("stop order triggered {}".format(order))
            #order = "stop"
            order = 1
        #print("sending order {}".format(order))
        try:
            next(broker)
            x = broker.send(order)
            #print("got back from execution {}".format(x))
        except StopIteration:
            #print("algo run finished")
            break
        
from blueshift.utils.calendars.trading_calendar import TradingCalendar
import pandas as pd
cimport numpy as np
import numpy as np

cpdef enum BARS:
    ALGO_START = 0
    BEFORE_TRADING_START = 1
    TRADING_BAR = 2
    AFTER_TRADING_HOURS = 3
    ALGO_END = 4
    

NANO_SECOND = 1000000000

ist_cal = TradingCalendar('IST',tz='Asia/Calcutta',
                          opens=(9,15,0), closes=(15,30,0))
start_dt = pd.Timestamp('2010-01-01')
end_dt = pd.Timestamp('2018-10-04')
sessions = ist_cal.sessions(start_dt, end_dt)

cdef np.int64_t start_nano = start_dt.value
cdef np.int64_t end_nano = end_dt.value
cdef np.int64_t[:] session_nanos = np.asarray([s.value for s in sessions])

cdef np.int64_t open_nano = (((ist_cal.open_time.hour*60 + ist_cal.open_time.minute)*60 \
                  + ist_cal.open_time.second)*1000000 + 
                    ist_cal.open_time.microsecond)*1000

cdef np.int64_t close_nano = (((ist_cal.close_time.hour*60 + ist_cal.close_time.minute)*60 \
                      + ist_cal.close_time.second)*1000000 + 
                        ist_cal.close_time.microsecond)*1000
cdef np.int64_t before_trading_start_nano = open_nano - 3600*NANO_SECOND
cdef np.int64_t after_trading_hours_nano = close_nano + 3600*NANO_SECOND

cdef int emit_frequency = 1
cdef int n= int((close_nano - open_nano)/NANO_SECOND/60/emit_frequency)
cdef np.int64_t period = emit_frequency*60*NANO_SECOND
cdef np.int64_t[:] intraday_nanos = np.asarray([open_nano + i*period for i in range(n+1)])

cdef dict dt_by_session = {}

def emit_datetime2(int emit_frequency=1):    
    yield 0, ALGO_START
    for session_nano in session_nanos:
        yield session_nano+before_trading_start_nano, BEFORE_TRADING_START
        
        for intraday_nano in intraday_nanos:
            yield session_nano+intraday_nano, TRADING_BAR
            
        yield session_nano+after_trading_hours_nano, AFTER_TRADING_HOURS
        
    yield 0, ALGO_END