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
Created on Fri Nov  9 14:15:18 2018

@author: prodipta
"""

from blueshift.utils.exceptions import NotValidBroker
from blueshift.utils.decorators import singleton, blueprint



@singleton
@blueprint
class BrokerDispatch(object):
    '''
        The global broker registry and dispatch. Instantiate a broker
        on the fly.
    '''
    
    def __init__(self, brokers, broker_factoris, aliases):
        self._create(brokers, broker_factoris, aliases)
        
    def _create(self, brokers, broker_factoris, aliases):
        self._brokers = brokers
        self._factories = broker_factoris
        self._aliases = aliases
    
    def resolve_alias(self, name):
        '''
            Resolve aliases
        '''
        if name in self._brokers:
            return name
        
        if name in self._aliases:
            return self._aliases[name]
        
        return name
        
    def get_broker(self, name):
        '''
            Get an instance of a registered broker.
        '''
        name = self.resolve_alias(name)
        
        try:
            return self._brokers[name]
        except KeyError:
            raise NotValidBroker(msg=f"{name} not a registered broker")
    
    def register_broker(self, broker_name, factory_name, *args, **kwargs):
        '''
            Register a constructor factory, overwrite if "forced".
        '''
        name = self.resolve_alias(factory_name)
        if name not in self._factories:
            raise NotValidBroker(msg="failed to fetch broker factory")
        
        factory = self._factories[name]
        self._brokers[broker_name] = factory(*args, **kwargs)
        
    def deregister_broker(self, name):
        '''
            Remove a constructor from the factory.
        '''
        if name in self._brokers:
            self._brokers.pop(name)
            
    def register_alias(self, broker_name, alias):
        '''
            Register a name alias.
        '''
        if alias in self._aliases:
            return
        
        if broker_name not in self._brokers:
            raise NotValidBroker(msg="not a registered broker")
        
        self._aliases[alias] = broker_name
        
    def deregister_alias(self, alias):
        '''
            Register a name alias.
        '''
        if alias in self._aliases:
            self._aliases.pop(alias)
