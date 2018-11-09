# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 10:42:06 2018

@author: prodipta
"""

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.utils.calendars.calendar_dispatch import CalendarDispatch

nse_calendar = TradingCalendar('NSE',tz='Asia/Calcutta',
                               opens=(9,15,0), closes=(15,30,0))
nyse_calendar = TradingCalendar('NYSE',tz='US/Eastern',
                               opens=(9,30,0), closes=(16,0,0))

_default_cal_factories = {
        'NSE': nse_calendar,
        'NYSE': nyse_calendar
        }

_default_cal_aliases = {
        'IST': 'NSE',
        'US': 'NYSE'
        }


global_cal_dispatch = CalendarDispatch({},
                                       _default_cal_factories,
                                       _default_cal_aliases)

get_calendar = global_cal_dispatch.get_calendar
register_calendar = global_cal_dispatch.register_calendar
unregister_calendar = global_cal_dispatch.unregister_calendar
                            

__all__ = [get_calendar,
           register_calendar,
           unregister_calendar]

