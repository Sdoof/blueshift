# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 20:34:19 2018

@author: prodipta
"""
import pandas as pd
import numpy as np
from datetime import time
import unittest
from blueshift.utils.calendars.trading_calendar import TradingCalendar

start_dt = pd.Timestamp('2018-01-01')
end_dt = pd.Timestamp('2018-12-31')
time_delta = end_dt - start_dt
dts = [start_dt + pd.Timedelta(days=i) for i in range(time_delta.days+1)]
utc_cal = TradingCalendar('UTC')
ist_cal = TradingCalendar('IST',tz='Asia/Calcutta',closes=(15,30,0))
dts_cal = TradingCalendar('DATES', tz='Asia/Calcutta', bizdays=dts)

class TestTradingCalendar(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_names(self):
        self.assertEqual(utc_cal.name, 'UTC')
        self.assertEqual(ist_cal.name, 'IST')
        self.assertEqual(dts_cal.name, 'DATES')
        
    def test_tz(self):
        self.assertEqual(utc_cal.tz, 'Etc/UTC')
        self.assertEqual(ist_cal.tz, 'Asia/Calcutta')
        self.assertEqual(dts_cal.tz, 'Asia/Calcutta')
        
    def test_times(self):
        self.assertEqual(utc_cal.close_time, time(16,0,0))
        self.assertEqual(ist_cal.close_time, time(15,30,0))
        
    def test_bizdays(self):
        self.assertTrue(utc_cal.is_session(pd.Timestamp('2018-09-24',tz=utc_cal.tz)))
        self.assertTrue(ist_cal.is_session(pd.Timestamp('2018-09-25',tz=ist_cal.tz)))
        self.assertTrue(dts_cal.is_session(pd.Timestamp('2018-09-26',tz=dts_cal.tz)))
        
    def test_holidays(self):
        self.assertTrue(utc_cal.is_holiday(pd.Timestamp('2018-09-23',tz=utc_cal.tz)))
        self.assertTrue(ist_cal.is_holiday(pd.Timestamp('2018-09-22',tz=ist_cal.tz)))
        self.assertTrue(dts_cal.is_holiday(pd.Timestamp('2018-07-07',tz=dts_cal.tz)))
        
    def test_is_open(self):
        self.assertTrue(utc_cal.is_open(pd.Timestamp('2018-09-24 10:30:00',tz=utc_cal.tz)))
        self.assertFalse(ist_cal.is_open(pd.Timestamp('2018-09-24 15:45:00',tz=ist_cal.tz)))
        self.assertTrue(dts_cal.is_open(pd.Timestamp('2018-09-24 16:00:00',tz=dts_cal.tz)))
        
    def test_next_open(self):
        self.assertEqual(utc_cal.next_open(pd.Timestamp('2018-09-24 10:30:00',tz=utc_cal.tz)),
                         pd.Timestamp('2018-09-25 10:00:00',tz=utc_cal.tz))
        self.assertEqual(ist_cal.next_open(pd.Timestamp('2018-09-23 10:30:00',tz=ist_cal.tz)),
                         pd.Timestamp('2018-09-24 10:00:00',tz=ist_cal.tz))
        self.assertEqual(dts_cal.next_close(pd.Timestamp('2018-09-22 10:30:00',tz=dts_cal.tz)),
                         pd.Timestamp('2018-09-24 16:00:00',tz=dts_cal.tz))
        
    def test_previous_open(self):
        self.assertEqual(utc_cal.previous_open(pd.Timestamp('2018-09-24 10:30:00',tz=utc_cal.tz)),
                         pd.Timestamp('2018-09-21 10:00:00',tz=utc_cal.tz))
        self.assertEqual(ist_cal.previous_close(pd.Timestamp('2018-09-23 10:30:00',tz=ist_cal.tz)),
                         pd.Timestamp('2018-09-21 15:30:00',tz=ist_cal.tz))
        self.assertEqual(dts_cal.previous_close(pd.Timestamp('2018-09-25 10:30:00',tz=dts_cal.tz)),
                         pd.Timestamp('2018-09-24 16:00:00',tz=dts_cal.tz))
        
    def test_sessions(self):
        dt1 = pd.Timestamp('2018-09-22',tz=utc_cal.tz)
        dt2 = pd.Timestamp('2018-09-24',tz=utc_cal.tz)
        dt3 = pd.Timestamp('2018-09-29',tz=utc_cal.tz)
        dtss = pd.to_datetime([dt2+pd.Timedelta(days=i) for i in range(5)])
        self.assertTrue(np.all(utc_cal.sessions(dt1,dt3)==dtss))
        
    def test_add_holidays(self):
        dt1 = pd.Timestamp('2018-01-26',tz=ist_cal.tz)
        dt2 = pd.Timestamp('2018-08-15',tz=ist_cal.tz)
        dtss = [dt1,dt2]
        ist_cal.add_holidays(dtss)
        self.assertTrue(ist_cal.is_holiday(dt1))
        self.assertTrue(ist_cal.is_holiday(dt2))
        ist_cal.add_bizdays(dtss)
        self.assertFalse(ist_cal.is_holiday(dt1))
        self.assertFalse(ist_cal.is_holiday(dt2))
        
if __name__ == '__main__':
    unittest.main()