# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 19:11:39 2018

@author: prodi
"""

import pandas as pd

EPOCH = 0
NANOSECOND = 1000000000

def schedule(ts, freq="monthly",day_offset=0):
    if freq=="monthly":
        next_month = 1
        day_offset = day_offset
    elif freq=="weekly":
        next_month = 0
        day_offset = 7 + day_offset
        
    return ts + pd.DateOffset(months=next_month, days=day_offset)

ts = pd.Timestamp('2018-10-01 09:50:00+0530', tz='Asia/Calcutta')

for i in range(5):
    ts = schedule(ts, "weekly")
    print(ts)
    
    
### algo testing
import pandas as pd
start_dt = pd.Timestamp('2010-01-04',tz='Asia/Calcutta')
end_dt = pd.Timestamp('2018-01-04',tz='Asia/Calcutta')
ist_cal = TradingCalendar('IST',tz='Asia/Calcutta',opens=(9,15,0), 
                          closes=(15,30,0))
clock = SimulationClock(ist_cal,1,start_dt,end_dt)
broker = BackTesterAPI('blueshift',BrokerType.BACKTESTER,ist_cal)

asset_db_config = AssetDBConfiguration()
asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
asset_finder = AssetFinder(asset_db_query_engine)

algo = Algorithm(clock=clock, calendar = ist_cal, broker=broker,
                 asset_finder=asset_finder)
algo.run()


### api validation test
from functools import wraps
from blueshift.utils.cutils import check_input, check_input2

            
def positive_int(x):
    if type(x) != int or x < 0:
        return False, "Invalid argument {} in function {}:expected positive integer"
    return True, ""
        

def order(x: str,y = 0):
    check_input(order, locals())
    
def order3(x: str,y = 0):
    check_input2(order.__annotations__,order.__name__, locals())
    
def input_validation(narg, check):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            val = list(args)[narg]
            if type(check)==type:
                msg = "Invalid argument in {}: expected type {}".format(f.__name__,check)
                if not isinstance(val, check):
                    raise ValueError(msg)
            elif callable(check):
                truth, msg = check(val)
                if not truth:
                    raise ValueError(msg.format(f.__name__))
            
        return decorated
    return decorator
             
@input_validation(0,str)
def order2(x,y = 0):
    return
            

t1 = pd.Timestamp.now()
for i in range(10*480*3650):
    order("test",10)
t2 = pd.Timestamp.now()
elapsed_time = (t2-t1).total_seconds()*1000
print("run complete in {} milliseconds".format(elapsed_time))