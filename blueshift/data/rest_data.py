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
Created on Thu Oct 25 14:20:31 2018

@author: prodipta
"""
from blueshift.data.dataportal import DataPortal
from blueshift.utils.decorators import blueprint
from blueshift.configs import blueshift_run_get_name

@blueprint
class RESTDataPortal(DataPortal):
    '''
        Abstract interface for RESTful data service.
    '''
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name",blueshift_run_get_name())
        self._trading_calendar = kwargs.get("trading_calendar",None)
        self._api = kwargs.get("api",None)
        self._auth = kwargs.get("auth",None)
        self._asset_finder = kwargs.get("asset_finder",None)
        
        
        
    @property
    def name(self):
        return self._name
    
    @property
    def api(self):
        return self._api
    
    @property
    def auth(self):
        return self._auth
    
    @property
    def tz(self):
        return self._trading_calendar.tz
    
    @property
    def asset_finder(self):
        return self._asset_finder
    
    def current(assets, fields):
        raise NotImplementedError
        
    def history(assets, fields):
        raise NotImplementedError
        
    def __str__(self):
        return "Blueshift REST Data [name:%s]" % self.name
    
    def __repr__(self):
        return self.__str__()
        
