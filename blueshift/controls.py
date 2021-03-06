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
Created on Tue Feb  5 15:48:12 2019

@author: prodipta
"""

from blueshift.brokers import (get_broker, 
                               register_broker, 
                               deregister_broker,
                               register_broker_alias,
                               deregister_broker_alias)

from blueshift.utils.calendars import (get_calendar, 
                                       register_calendar, 
                                       deregister_calendar,
                                       register_calendar_alias,
                                       deregister_calendar_alias)

from blueshift.configs.runtime import (register_env, 
                                       get_env, 
                                       blueshift_run_get_name)

from blueshift.alerts import (register_alert_manager,
                              get_alert_manager,
                              register_logger,
                              get_logger)

__all__ = [get_broker,
           register_broker,
           deregister_broker,
           register_broker_alias,
           deregister_broker_alias,
           get_calendar,
           register_calendar,
           deregister_calendar,
           register_calendar_alias,
           deregister_calendar_alias,
           register_env,
           get_env,
           blueshift_run_get_name,
           register_alert_manager,
           get_alert_manager,
           register_logger,
           get_logger,
           ]