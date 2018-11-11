# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 15:24:20 2018

@author: prodipta
"""

from blueshift.utils.exceptions import NotValidCalendar
from blueshift.utils.decorators import singleton

@singleton
class CalendarDispatch(object):
    '''
        The global calendar registry and dispatch. Instantiate a calendar
        on the fly.
    '''
    
    def __init__(self, calendars, cal_factoris, aliases):
        self._calendars = calendars
        self._factories = cal_factoris
        self._aliases = aliases
        
    def resolve_alias(self, name):
        '''
            Resolve aliases
        '''
        if name in self._factories:
            return name
        
        if name in self._aliases:
            return self._aliases[name]
        
        raise NotValidCalendar(msg="failed to resolve alias")
        
    def get_calendar(self, name, *args, **kwargs):
        '''
            Get an instance if already there, else get the factory
            constructor and arguments to create one.
        '''
        name = self.resolve_alias(name)
        
        try:
            return self._calendars[name]
        except KeyError:
            pass
        
        try:
            factory = self._factories[name]
        except KeyError:
            raise NotValidCalendar(msg="failed to fetch calendar factory")
        
        cal = self._calendars[name] = factory(*args, **kwargs)
        return cal
    
    def register_calendar(self, name, factory_method, forced = False):
        '''
            Register a constructor factory, overwrite if "forced".
        '''
        if name in self._factories and not forced:
            return
        
        self._factories[name] = factory_method
        
    def unregister_calendar(self, name):
        '''
            Remove a constructor from the factory.
        '''
        if name in self._factories:
            self._factories.pop(name)