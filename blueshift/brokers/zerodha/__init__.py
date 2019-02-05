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
Created on Mon Oct 29 16:36:06 2018

@author: prodipta
"""

from .kiteauth import KiteAuth
from .kiteassets import KiteAssetFinder
from .kitedata import KiteRestData
from .kitebroker import KiteBroker
from blueshift.utils.types import Broker
from blueshift.execution.clock import RealtimeClock

def make_broker_pack(*args, **kwargs):
    name = kwargs.pop("name","zerodha")
    frequency = kwargs.get("frequency",1)
    auth = KiteAuth(name = name, *args, **kwargs)
    auth.login(*args, **kwargs)
    asset_finder = KiteAssetFinder(auth=auth, *args, **kwargs)
    data_portal = KiteRestData(name=name, auth=auth, *args, **kwargs)
    broker = KiteBroker(name=name, auth = auth, asset_finder=asset_finder)
    clock = RealtimeClock(auth._trading_calendar,frequency)
    
    return auth, asset_finder, data_portal, broker, clock

def Zerodha(*args, **kwargs):
    auth, asset_finder, data_portal, broker, clock =\
            make_broker_pack(*args, **kwargs)
    modes = broker._mode_supports
    zerodha = Broker(auth, asset_finder, data_portal, broker, clock, modes)
    
    return zerodha

__all__ = [KiteAuth,
           KiteAssetFinder,
           KiteRestData,
           KiteBroker,
           Zerodha,
           RealtimeClock]