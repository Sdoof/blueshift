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
Created on Tue Dec 11 15:19:00 2018

@author: prodipta
"""
import json

from fxcmpy import fxcmpy as fxcmpyapi
import fxcmpy
from fxcmpy.fxcmpy import ServerError

from blueshift.execution.authentications import TokenAuth
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        ValidationError)
from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.mixins import APIRateLimitMixin
from blueshift.alerts import get_logger

_api_version_ = fxcmpy.__version__

@singleton
@blueprint
class FXCMPy(APIRateLimitMixin, fxcmpyapi):
    '''
        kiteconnect modified to force a singleton (and to print pretty).
    '''
    def __init__(self, *args, **kwargs):
        self._create(*args, **kwargs)
        
    def _create(self, *args, **kwargs):
        # pylint: disable=bad-super-call
        access_token = kwargs.pop('access_token',None)
        server = kwargs.pop('server','real')
        proxy_url = kwargs.pop('proxy_url',None)
        proxy_port = kwargs.pop('proxy_port',None)
        proxy_type = kwargs.pop('proxy_type',None)
        log_file = kwargs.pop('log_file',None)
        log_level = kwargs.pop('log_level','')
        config_file = kwargs.pop('config_file','')
        
        try:
            fxcmpyapi.__init__(self, access_token, config_file,
                                 log_file, log_level, server,
                                 proxy_url, proxy_port, proxy_type)
        except ServerError:
            msg = "access token missing"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        logger = get_logger()
        if logger:
            self.logger = logger
        
        APIRateLimitMixin.__init__(self, *args, **kwargs)
        
        # max instruments that can be queried at one call
        self._max_instruments = kwargs.pop("max_instruments",None)
        self._trading_calendar = kwargs.get("trading_calendar",None)
        
        if not self._rate_limit:
            # TODO: check FXCM rate limits
            self._rate_limit = 2
            self._rate_limit_count = self._rate_limit
            
        if not self._rate_period:
            self._rate_period = 1
        
        if not self._max_instruments:
            # 50 covers all currency pairs (at present 38)
            self._max_instruments = 50
            
        # we reset this value on first call
        self._rate_limit_since = None 
        
        if not self._trading_calendar:
            raise ValidationError(msg="missing calendar")
    
    def __str__(self):
        return f"FXCMPy [{_api_version_}]"
    
    def __repr__(self):
        return self.__str__()
    
@singleton
@blueprint
class FXCMAuth(TokenAuth):
    '''
        The authentication class handles the user login/ logout and 
        managing of the sessions validity etc. It creates and validate
        the underlying API object which shall be passed around for any
        subsequent interaction.
    '''
    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        self._create(*args, **kwargs)
    
    def _create(self, *args, **kwargs):
        config = None
        config_file = kwargs.pop('config',None)
        if config_file:
            try:
                with open(config_file) as fp:
                    config = json.load(fp)
            except FileNotFoundError:
                pass
        
        if config:
            kwargs = {**config, **kwargs}
        
        if not kwargs.get('name',None):
            kwargs['name'] = 'fxcm'
        
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(*args, **kwargs)
        self._access_token = kwargs.pop('access_token',None)
        self._server = kwargs.pop('server','real')
        
        # auth token and access token means the same thing.
        if not self._auth_token:
            self._auth_token = self._access_token
        if not self._access_token:
            self._access_token = self._auth_token
        
        self._api = FXCMPy(access_token=self._access_token,
                           server=self._server,
                           rate_period=kwargs.pop("rate_period",None),
                           rate_limit=kwargs.pop("rate_limit",None),
                           **kwargs)
        
        self._trading_calendar = self._api._trading_calendar
    
    @property
    def access_token(self):
        return self._access_token
    
    @property
    def default_account(self):
        return self._api.default_account
    
    def login(self, *args, **kwargs):
        '''
            Set access token if available. Else do an API call to obtain
            an access token. If it fails, it is catastrophic. We cannot
            continue and raise TERMINATE level error.
        '''
        auth_token = kwargs.pop("auth_token",None)
        if not auth_token:
            return
        
        # we got a new auth_token, recreate the api
        self._access_token = self._auth_token = auth_token
        self._server = kwargs.pop('server',self._server)
        rate_period=kwargs.pop("rate_period", self._api._rate_period)
        rate_limit=kwargs.pop("rate_limit", self._api._rate_limit)
        trading_calendar = kwargs.pop("trading_calendar", 
                                      self._api._trading_calendar)
        max_instruments = kwargs.pop("max_instruments",
                                     self._max_instruments)
        self._api._create(access_token=auth_token, 
                          server=self._server, 
                          rate_period=rate_period,
                          rate_limit = rate_limit,
                          trading_calendar = trading_calendar,
                          max_instruments=max_instruments,
                          **kwargs)
        
    def logout(self):
        '''
            API call to logout. If it fails, it is not catastrophic. We
            just warn about it.
        '''
        self._api = self._auth_token = self._access_token = None