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
Created on Tue Dec 11 09:33:50 2018

@author: prodipta
"""

from .fxcmauth import FXCMAuth
from .fxcmassets import FXCMAssetFinder
from .fxcmdata import FXCMRestData
from .fxcmbroker import FXCMBroker
from blueshift.utils.types import Broker
from blueshift.execution.clock import RealtimeClock

def make_broker_pack(*args, **kwargs):
    name = kwargs.pop("name","fxcm")
    frequency = kwargs.get("frequency",1)
    auth = FXCMAuth(name = name, *args, **kwargs)
    auth.login(*args, **kwargs)
    asset_finder = FXCMAssetFinder(auth=auth, *args, **kwargs)
    data_portal = FXCMRestData(name=name, auth=auth, *args, **kwargs)
    broker = FXCMBroker(name=name, auth = auth, asset_finder=asset_finder)
    clock = RealtimeClock(auth._trading_calendar,frequency)
    
    return auth, asset_finder, data_portal, broker, clock

def FXCM(*args, **kwargs):
    auth, asset_finder, data_portal, broker, clock =\
            make_broker_pack(*args, **kwargs)
    modes = broker._mode_supports
    FXCM = Broker(auth, asset_finder, data_portal, broker, clock, modes)
    
    return FXCM

__all__ = [FXCMAuth,
           FXCMAssetFinder,
           FXCMRestData,
           FXCMBroker,
           FXCM,
           RealtimeClock]