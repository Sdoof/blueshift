# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 08:54:16 2018

@author: academy
"""
import random

def execute(order):
    return int(random.random()*10)

def clock_fn():
    bar = 0
    for i in range(1752000):
        yield bar

def execution():
    run = True

    while run:
        order = yield
        if order == "stop":
            run = False
            continue
        #print("execute order {}".format(order))
        order =  execute(order)
        yield order

        

def algo1():
    broker = execution()
    clock = clock_fn()
    for bar in clock:
        order = round(random.random(),2)
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
        
import pandas as pd
from blueshift.trades.test import algo2

t1 = pd.Timestamp.now()
algo2()
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

from blueshift.utils.calendars.trading_calendar import TradingCalendar

def create_calendar():
    return TradingCalendar('IST',tz='Asia/Calcutta',
                          opens=(9,15,0), closes=(15,30,0))
    
def make_timestamp(date_nano, time_nano, cal):
    return pd.Timestamp(date_nano + time_nano, unit='ns',
                        tz=cal.tz)
    
def emit_datetime1():
    ist_cal = create_calendar()
    start_dt = pd.Timestamp('2010-01-01')
    end_dt = pd.Timestamp('2018-10-04')
    sessions = ist_cal.sessions(start_dt, end_dt)
    open_nano = (((ist_cal.open_time.hour*60 + ist_cal.open_time.minute)*60 \
                  + ist_cal.open_time.second)*1000000 + 
                    ist_cal.open_time.microsecond)*1000

    close_nano = (((ist_cal.close_time.hour*60 + ist_cal.close_time.minute)*60 \
                      + ist_cal.close_time.second)*1000000 + 
                        ist_cal.close_time.microsecond)*1000
    
    before_trading_start_nano = open_nano - 3600*1E9
    after_trading_hours_nano = close_nano + 3600*1E9
    emit_frequency = 1
    
    n = int((close_nano - open_nano)/1E9/60/emit_frequency)
    period = emit_frequency*60*1E9
    ts = [open_nano + i*period for i in range(n+1)]
    
    for session in sessions:
        session_nano = session.value
        yield make_timestamp(session_nano, before_trading_start_nano,
                             ist_cal)
        for t in ts:
            yield make_timestamp(session_nano, t, ist_cal)
            
        yield make_timestamp(session_nano, after_trading_hours_nano,
                             ist_cal)
        
    
clock = emit_datetime1()

t1 = pd.Timestamp.now()
for t in clock:
    pass
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

from blueshift.trades.clocks import SimulationClock, BARS
start_dt = pd.Timestamp('2010-01-01')
end_dt = pd.Timestamp('2018-10-04')
ist_cal = TradingCalendar('IST',tz='Asia/Calcutta',opens=(9,15,0), 
                          closes=(15,30,0))
clock = SimulationClock(ist_cal,1,start_dt,end_dt)


tz = ist_cal.tz
t1 = pd.Timestamp.now()
for t, bar in clock:
    if bar == BARS.ALGO_START:
        print("starting the algo")
    elif bar == BARS.ALGO_END:
        print("stopping the algo")
    else:
        ts = pd.Timestamp(t,unit='ns',tz=tz)
        #print("BAR:{}, timestamp: {}".format(bar, ts))
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)






