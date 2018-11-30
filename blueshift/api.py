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
Created on Sat Nov 24 13:51:04 2018

@author: prodi

Defines the complete set of blueshift APIs. Note the algorithm APIs are
injected at run-time.
"""

from blueshift.utils.brokers import (get_broker, 
                                     register_broker, 
                                     deregister_broker,
                                     register_broker_alias,
                                     deregister_broker_alias)

from blueshift.utils.calendars import (get_calendar, 
                                       register_calendar, 
                                       deregister_calendar,
                                       register_calendar_alias,
                                       deregister_calendar_alias)

__all__ = [get_broker,
           register_broker,
           deregister_broker,
           register_broker_alias,
           deregister_broker_alias,
           get_calendar,
           register_calendar,
           deregister_calendar,
           register_calendar_alias,
           deregister_calendar_alias]