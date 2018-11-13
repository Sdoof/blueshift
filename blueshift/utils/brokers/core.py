# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 14:15:18 2018

@author: prodipta
"""
from collections import namedtuple

from blueshift.utils.exceptions import NotValidBroker
from blueshift.utils.decorators import singleton

Broker = namedtuple("Broker",('auth', 'asset_finder', 'data_portal', 
                              'broker', 'clock'))

@singleton
class BrokerDispatch(object):
    '''
        The global broker registry and dispatch. Instantiate a broker
        on the fly.
    '''
    
    def __init__(self, brokers, broker_factoris, aliases):
        self._brokers = brokers
        self._factories = broker_factoris
        self._aliases = aliases
        
    def resolve_alias(self, name):
        '''
            Resolve aliases
        '''
        if name in self._factories:
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
            raise NotValidBroker(msg="not a registered broker")
    
    def register_broker(self, name, *args, **kwargs):
        '''
            Register a constructor factory, overwrite if "forced".
        '''
        name = self.resolve_alias(name)
        if name not in self._factories:
            raise NotValidBroker(msg="failed to fetch broker factory")
        
        factory = self._factories[name]
        self._brokers[name] = factory(*args, **kwargs)
        
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
