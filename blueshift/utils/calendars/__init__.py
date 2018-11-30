# Copyright 2018 QuantInsti Quantitative Learnings Pvt Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Mon Sep 24 10:42:06 2018

@author: prodipta
"""

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.utils.calendars.calendar_dispatch import CalendarDispatch

global_cal_dispatch = CalendarDispatch({})

get_calendar = global_cal_dispatch.get_calendar
register_calendar = global_cal_dispatch.register_calendar
deregister_calendar = global_cal_dispatch.deregister_calendar
register_calendar_alias = global_cal_dispatch.register_alias
deregister_calendar_alias = global_cal_dispatch.deregister_alias
                            

__all__ = [TradingCalendar,
           get_calendar,
           register_calendar,
           deregister_calendar,
           register_calendar_alias,
           deregister_calendar_alias]

