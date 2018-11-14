# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 15:24:20 2018

@author: prodipta
"""

from blueshift.utils.exceptions import NotValidCalendar
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.utils.decorators import singleton, blueprint

@singleton
@blueprint
class CalendarDispatch(object):
    '''
        The global calendar registry and dispatch. Instantiate a calendar
        on the fly. Calendar factories is effectively a mapping of
        calendar object to name to enable gettng a calendar by name.
        (get_calendar). Registering is adding an entry and an object
        to this dict.
    '''
    
    def __init__(self, calendars, cal_factoris, aliases):
        self._calendars = calendars
        self._factories = cal_factoris  # default avaliable cals
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
        
    def get_calendar(self, name):
        '''
            Get an instance if already there, else get the factory
            constructor and arguments to create one.
        '''
        name = self.resolve_alias(name)
        
        try:
            return self._calendars[name]
        except KeyError:
            pass
        # if it is not registered, automatically search the default
        # calendars to fetch.
        try:
            cal_obj = self._calendars[name] = self._factories[name]
        except KeyError:
            raise NotValidCalendar(msg="failed to fetch calendar")
        
        return cal_obj
    
    def register_alias(self, name, alias):
        '''
            Register a calendar name alias.
        '''
        if alias in self._aliases:
            return
        
        if name not in self._calendars:
            raise NotValidCalendar(msg="not a registered calendar")
        
        self._aliases[alias] = name
        
    def deregister_alias(self, name, alias):
        '''
            Register a calendar name alias.
        '''        
        if alias in self._aliases:
            self._aliases.pop(alias)
        
    def register_calendar(self, name, cal_obj):
        '''
            Register a constructor factory, overwrite if "forced".
        '''        
        if not isinstance(cal_obj, TradingCalendar):
            raise NotValidCalendar(msg="object is not a calendar")
        
        self._calendars[name] = cal_obj
        
    def deregister_calendar(self, name):
        '''
            Remove a constructor from the factory.
        '''
        if name in self._calendars:
            self._calendars.pop(name)