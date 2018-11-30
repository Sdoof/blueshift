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
Created on Fri Oct 19 01:28:32 2018

@author: prodi
"""
from abc import ABC, abstractmethod, abstractproperty

from blueshift.utils.decorators import blueprint
from blueshift.utils.types import DataPortalFlag, OHLCV_FIELDS
from blueshift.configs import blueshift_run_get_name


class DataPortal(ABC):
    '''
        Abstract class for handling all the data needs for an algo. This
        encapsulates database reader for backtester portal and db + 
        broker RESTful API + websockets for live trading
    '''
    def __init__(self, *args, **kwargs):
        pass
        
    @abstractproperty
    def name(self):
        raise NotImplementedError
    
    @abstractproperty
    def tz(self):
        raise NotImplementedError
    
    @abstractproperty
    def asset_finder(self):
        raise NotImplementedError
    
    @abstractmethod
    def current(assets, fields):
        raise NotImplementedError
        
    @abstractmethod
    def history(assets, fields):
        raise NotImplementedError
        
@blueprint
class DBDataPortal(DataPortal):
    '''
        Abstract class for handling all the data needs for an algo. This
        encapsulates database reader for backtester portal and db + 
        broker RESTful API + websockets for live trading
    '''
    
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name",blueshift_run_get_name())
    
    @property
    def name(self):
        return self._name
    
    @property
    def tz(self):
        raise NotImplementedError
    
    @property
    def asset_finder(self):
        raise NotImplementedError
    
    @property
    def auth(self):
        return None
    
    def current(self, assets, fields):
        return 50
        raise NotImplementedError
        
    def history(self, assets, fields, bars, frequency):
        raise NotImplementedError
    
    def __str__(self):
        return "Blueshift Data Portal [name:%s]" % self.name
    
    def __repr__(self):
        return self.__str__()