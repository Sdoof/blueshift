import pandas as pd

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.utils.scheduler import (TimeRule, TimeEvent, Scheduler,
                                       date_rules, time_rules)

start_dt = pd.Timestamp('2017-01-01')
end_dt = pd.Timestamp('2017-01-28')
trading_calendar = TradingCalendar('NSE_EQ',tz="Asia/Calcutta",
                                   opens=(9,15,0), closes=(15,30,0),
                                   weekends=[5,6])

rule1 = TimeRule(date_rules.month_start(1), 
                time_rules.market_open(minutes=10), 
                start_dt= start_dt, end_dt = end_dt, 
                trading_calendar = trading_calendar)

rule2 = TimeRule(date_rules.every_day(), 
                time_rules.every_nth_hour(hours=2), 
                start_dt= start_dt, end_dt = end_dt, 
                trading_calendar = trading_calendar)

rule3 = TimeRule(date_rules.month_end(3), 
                time_rules.BeforeClose(minutes=10), 
                start_dt= start_dt, end_dt = end_dt, 
                trading_calendar = trading_calendar)

def f1(context, data):
    pass
    
def f2(context, data):
    pass
    
def f3(context, data):
    pass

def clock():
    start = start_dt.value
    end = end_dt.value
    val = start
    while val < end:
        yield val 
        val = val + 60000000000

e1 = TimeEvent(rule1, f1)
e2 = TimeEvent(rule2, f2)
e3 = TimeEvent(rule3, f3)
scheduler = Scheduler()
scheduler.add_event(e1)
scheduler.add_event(e2)
scheduler.add_event(e3)


for dt in clock():
    scheduler.trigger_events(None, None, dt)