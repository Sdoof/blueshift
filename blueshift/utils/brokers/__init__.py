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
Created on Mon Oct 29 16:36:33 2018

@author: prodipta
"""

from blueshift.utils.brokers.backtest import BackTest
from blueshift.utils.brokers.zerodha import Zerodha
from blueshift.utils.brokers.core import BrokerDispatch
from blueshift.utils.types import Broker

_default_broker_factories = {
        'zerodha': Zerodha,
        'backtest': BackTest
        }

global_broker_dispatch = BrokerDispatch({},
                                        _default_broker_factories,
                                        {})


get_broker = global_broker_dispatch.get_broker
register_broker = global_broker_dispatch.register_broker
deregister_broker = global_broker_dispatch.deregister_broker
register_broker_alias = global_broker_dispatch.register_alias
deregister_broker_alias = global_broker_dispatch.deregister_alias
                            

__all__ = [get_broker,
           register_broker,
           deregister_broker,
           register_broker_alias,
           deregister_broker_alias,
           Broker]