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
Created on Thu Oct 25 15:24:19 2018

@author: prodipta
"""
import pandas as pd
from functools import wraps
from weakref import ref as weakref_ref
import math
import time

def api_rate_limit(f):
    '''
        decorator to enforce rate limits on API calls. This assumes a member
        variable `rate_limit_count` to keep track of limit consumption and
        a variable `rate_limit_since`.
    '''
    @wraps(f)
    def decorated(self, *args, **kwargs):
        
        if self._api.rate_limit_since is None:
            self._api.rate_limit_since = pd.Timestamp.now(self.tz)
            self._api.rate_limit_count == self._api.rate_limit
            sec_elapsed = 0
        else:
            t = pd.Timestamp.now(self.tz)
            sec_elapsed = (t - self._api.rate_limit_since).total_seconds()
            if math.floor(sec_elapsed) > (self._api._rate_period-1):
                self._api.reset_rate_limits()

        if self._api.rate_limit_count == 0:
            self._api.cool_off(mult=1.5)
            self._api.reset_rate_limits()
        
        self._api.rate_limit_count = self._api.rate_limit_count - 1
        return f(self, *args, **kwargs)
    return decorated

def blueprint(cls):
    '''
        A decorator to mark an instance of a type is blueshift
        native. This allows special treatments. The rule is to 
        decorate only the classes that can have an instance. Do
        not decorate ABCs or base classes that will never be 
        instantiated.
    '''
    cls._blueshift = True
    return cls

class singleton(object):
    '''
        Standard singleton class decorator. The side-effect is for
        any inherited class, the super call with class name will fail,
        as the class name is now a singleton callable, not a class. 
        Way around is to use self.__class__ directly, but there should
        be a cleaner way.
    '''
    def __init__(self,cls, *args, **kwargs):
        self.cls = cls
        self.__instance = None
    
    def __call__(self,*args,**kwargs):
        '''
            The temp reference holds the reference alive long enough
            for us to return the weak ref to the caller. Once it is
            done, this temp reference gets deleted automatically.
        '''
        tmp_ref = None
        # create the object if none, else call the _create method to refresh.
        if not self.__instance or self.__instance() == None:
            tmp_ref = self.cls(*args,**kwargs)
            self.__instance = weakref_ref(tmp_ref)
        else:
            self.__instance()._create(*args,**kwargs)
        
        return self.__instance()

def api_retry(delays=[0,5,30,90,180,300], exception=Exception):
    '''
        Decorator to try API for a given number of times, with sleeps in
        between. It should catch only the appropriate exceptions, passing
        on anything which may obviate the need for any retries.
    '''
    def decorator(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            for delay in [*delays,None]:
                try:
                    return f(self, *args, **kwargs)
                except exception as e:
                    if delay is None:
                        print("attempt failed permanently, quitting ")
                        raise e
                    else:
                        print(f"failed, sleeping {delay}s before retry")
                        time.sleep(delay)
        return decorated
    return decorator


