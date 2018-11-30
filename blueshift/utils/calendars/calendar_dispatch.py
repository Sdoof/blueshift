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
        on the fly. Registering is adding an entry and an object
        to a global dict.
    '''
    
    def __init__(self, calendars):
        self._create(calendars)
        
    def _create(self, calendars):
        self._calendars = calendars
        self._aliases = {}
        
    def resolve_alias(self, name):
        '''
            Resolve aliases
        '''
        if name in self._calendars:
            return name
        
        if name in self._aliases:
            return self._aliases[name]
        
        return name
        
    def get_calendar(self, name):
        '''
            Get an instance if already there, else raise error.
        '''
        name = self.resolve_alias(name)
        
        try:
            return self._calendars[name]
        except KeyError:
            raise NotValidCalendar(msg=f"calendar {name} not registered.")
    
    def register_alias(self, name, alias):
        '''
            Register a calendar name alias.
        '''
        if alias in self._aliases:
            return
        
        if name not in self._calendars:
            raise NotValidCalendar(msg=f"{name} not a registered calendar")
        
        self._aliases[alias] = name
        
    def deregister_alias(self, name, alias):
        '''
            Register a calendar name alias.
        '''        
        if alias in self._aliases:
            self._aliases.pop(alias)
        
    def register_calendar(self, name, *args, **kwargs):
        '''
            Register a calendar.
        '''
        self._calendars[name] = TradingCalendar(name, *args, **kwargs)
        
    def deregister_calendar(self, name):
        '''
            Remove a constructor from the dict.
        '''
        if name in self._calendars:
            self._calendars.pop(name)