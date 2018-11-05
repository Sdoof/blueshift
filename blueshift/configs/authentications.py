# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 09:22:12 2018

@author: prodipta
"""
import pandas as pd

from abc import ABC, abstractmethod
from enum import Enum

class AuthType(Enum):
    '''
        Auth types. It can be either token based (where the token is
        obtained by means outside the scope of this package). For 
        every subsequent request, this token is passed for 
        validation of the API access. The other method (IB) is using
        a dedicated external app that mediates communication - this
        is the TWS mode.
    '''
    TOKEN = 0
    TWS = 1

class AbstractAuth(ABC):
    '''
        Absract base class for authentication. Implements basic
        token set and get functions as well as timeouts.
    '''
    def __init__(self, *args, **kwargs):
        '''
            init method can pass a `timeout` and a `tz` arg. The tz
            arg is necessary for proper management, but missing this
            is not deemed to be catastrophic. If the API call raises
            invalid token, another handshake can be triggered.
        '''
        self._name = kwargs.get("name","")
        self._type = None
        self._timeout = kwargs.get("timeout",None)
        self._tz = kwargs.get("tz",None)
        self._last_login = None
        self._valid_till = None
    
    @property
    def name(self):
        '''
            Name of the platform/ broker.
        '''
        return self._name
    
    @property
    def auth_type(self):
        '''
            Name of the platform/ broker.
        '''
        return self._type
    
    @property
    def last_login(self):
        '''
            Last login time in timestamp format.
        '''
        return self._last_login
    
    @property
    def valid_till(self):
        '''
            Timestamp after which the auth token may be invalidated
            by the platform.
        '''
        return self._valid_till
    
    @property
    def tz(self):
        '''
            Timezone info. This is used for timezone-aware check
            for token validation.
        '''
        return self._tz
    
    @property
    def timeout(self):
        '''
            timeout in number of seconds. Or in hours, minutes,
            seconds int tuple.
        '''
        return self._timeout
    
    def __str__(self):
        return "Authentication:%s" % self.name
    
    def __repr__(self):
        return self.__str__()
    
    @abstractmethod
    def logout(self):
        raise NotImplementedError
        
    @abstractmethod
    def login(self, *args, **kwargs):
        raise NotImplementedError
        
    def is_logged(self):
        raise NotImplementedError
    
class TokenAuth(AbstractAuth):
    '''
        Absract base class for authentication. Implements basic
        token set and get functions as well as timeouts.
    '''
    def __init__(self, *args, **kwargs):
        '''
            init method can pass a `timeout` and a `tz` arg. The tz
            arg is necessary for proper management, but missing this
            is not deemed to be catastrophic. If the API call raises
            invalid token, another handshake can be triggered.
        '''
        super(TokenAuth, self).__init__(*args, **kwargs)
        self._type = AuthType.TOKEN
        self._auth_token = kwargs.get("auth_token",None)
        
    @property
    def auth_token(self):
        '''
            The auth token to be passed for every API call
        '''
        return self._auth_token
    
    def logout(self):
        '''
            This simply sets the token to None. For actually inform
            the platform, there may be other things to do.
        '''
        self._auth_token = None
        
    def login(self, *args, **kwargs):
        '''
            This simply calls the set_token method. Login may or
            may not be manual. In case of automated login, add the
            logic before setting the token.
        '''
        self.set_token(kwargs.get("auth_token",None))
        
    def set_token(self, auth_token, *args, **kwargs):
        '''
            Set the token and associated timeout/ validation 
            parameters.
        '''
        self._auth_token = auth_token
        self._last_login = kwargs.get("timestamp",
                                      pd.Timestamp.now(tz=self._tz))
        
        timeout = kwargs.get("timeout",self._timeout)
        self.update_timeout(timeout)
                
    def update_timeout(self, timeout):
        '''
            Update timeout as well as the valid_till field.
        '''
        self._timeout = timeout
        
        if not self._timeout:
            return

        if isinstance(self._timeout,int):
            self._valid_till = self._last_login + \
                            pd.Timedelta(seconds=self._timeout)
        
        elif isinstance(self._timeout, tuple):
            hh = int(self._timeout[0]) if len(self._timeout)> 0\
                        else 0
            mm = int(self._timeout[1]) if len(self._timeout)> 1\
                        else 0
            ss = int(self._timeout[2]) if len(self._timeout)> 2\
                        else 0
            self._valid_till = self._last_login.normalize() + \
                pd.Timedelta(days=1, hours=hh, minutes=mm,
                             seconds=ss)
        
        elif isinstance(self._timeout, pd.Timestamp):
            self._valid_till = self._timeout
                    
    def is_logged(self):
        '''
            If the token is not None, and the valid_till time is
            not expired, we assume our login is valid.
        '''
        if not self._auth_token:
            return False
        
        t = pd.Timestamp.now(tz=self._tz)
        if self._valid_till and self._valid_till < t:
            return False
        
        return True
        
        