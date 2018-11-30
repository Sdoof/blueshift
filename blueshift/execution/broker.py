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
Created on Sat Oct  6 11:51:35 2018

@author: prodipta
"""

from abc import ABC, abstractmethod, abstractproperty

class AbstractBrokerAPI(ABC):
    '''
        Broker abstract interface.
    '''
    
    def __init__(self, name, broker_type, calendar, **kwargs):
        self._name = name
        self._type = broker_type
        self._mode_supports = []
        self._trading_calendar = calendar
        self._auth_token = None
        self._connected = False
        
    def __str__(self):
        return "Blueshift Broker [name:%s]" % (self._name)
    
    def __repr__(self):
        return self.__str__()
        
    @abstractmethod
    def login(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def logout(self, *args, **kwargs):
        pass
    
    @abstractproperty
    def calendar(self):
        pass
    
    @abstractproperty
    def profile(self):
        pass
    
    @abstractproperty
    def account(self):
        pass
    
    @abstractproperty
    def positions(self):
        pass
    
    @abstractproperty
    def open_orders(self):
        pass
    
    @abstractproperty
    def orders(self):
        pass
    
    @abstractproperty
    def tz(self):
        pass
    
    @abstractmethod
    def order(self, order_id):
        pass
    
    @abstractmethod
    def place_order(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def update_order(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def cancel_order(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def fund_transfer(self, *args, **kwargs):
        raise NotImplementedError
    