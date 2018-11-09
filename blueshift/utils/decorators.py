# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 15:24:19 2018

@author: prodipta
"""
import pandas as pd
from functools import wraps
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
        self.instance = None
    def __call__(self,*args,**kwargs):
        if self.instance == None:
            self.instance = self.cls(*args,**kwargs)
        return self.instance

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


