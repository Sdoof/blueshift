# -*- coding: utf-8 -*-
"""
Created on Sat Oct  6 11:31:53 2018

@author: prodipta
"""

import pandas as pd
from blueshift.utils.calendars.trading_calendar import TradingCalendar
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