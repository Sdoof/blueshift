# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 14:15:18 2018

@author: prodipta
"""
from collections import namedtuple

from blueshift.utils.exceptions import NotValidBroker

Broker = namedtuple("Broker",('auth', 'asset_finder', 'data_portal', 
                              'broker', 'clock'))

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
        
        raise NotValidBroker(msg="failed to resolve alias")
        
    def get_broker(self, name, *args, **kwargs):
        '''
            Get an instance if already there, else get the factory
            constructor and arguments to create one.
        '''
        name = self.resolve_alias(name)
        has_arg = (args is not None) or (kwargs is not None)
        
        try:
            if not has_arg:
                return self._brokers[name]
        except KeyError:
            pass
        
        if not has_arg:
            raise NotValidBroker(msg="missing data to create broker")
        
        try:
            factory = self._factories[name]
        except KeyError:
            raise NotValidBroker(msg="failed to fetch broker factory")
        
        broker = self._brokers[name] = factory(*args, **kwargs)
        return broker
    
    def register_broker(self, name, factory_method, forced = False):
        '''
            Register a constructor factory, overwrite if "forced".
        '''
        if name in self._factories and not forced:
            return
        
        self._factories[name] = factory_method
        
    def unregister_broker(self, name):
        '''
            Remove a constructor from the factory.
        '''
        if name in self._factories:
            self._factories.pop(name)
        
        
