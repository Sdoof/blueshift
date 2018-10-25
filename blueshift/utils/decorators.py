# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 15:24:19 2018

@author: prodipta
"""
import pandas as pd
from functools import wraps
import math

import blueshift.algorithm.api
from blueshift.utils.exceptions import APIRateLimitCoolOff


def api_method(f):
    '''
        decorator to map bound API functions to unbound user 
        functions. First add to the function to the list of available 
        API functions in the api module. Then set the api attribute to 
        scan during init for late binding.
    '''
    setattr(blueshift.algorithm.api, f.__name__, f)
    blueshift.algorithm.api.__all__.append(f.__name__)
    f.is_api = True
    return f

def api_rate_limit(f):
    '''
        decorator to enforce rate limits on API calls. This assumes a member
        variable `_rate_limit_count` to keep track of limit consumption and
        a variable ``
    '''
    @wraps(f)
    def decorated(self, *args, **kwargs):
        
        if self._rate_limit_since is None:
            self._rate_limit_since = pd.Timestamp.now(self.tz)
            self._rate_limit_count == self._rate_limit
        else:
            t = pd.Timestamp.now(self.tz)
            sec_elapsed = (t - self._rate_limit_since).total_seconds()
            if math.floor(sec_elapsed) > (self._rate_period-1):
                self.reset_rate_limits()

        if self._rate_limit_count == 0:
            raise APIRateLimitCoolOff(msg="Exceeded API rate limit")
        
        self._rate_limit_count = self._rate_limit_count - 1
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
    def __init__(self,cls):
        self.cls = cls
        self.instance = None
    def __call__(self,*args,**kwds):
        if self.instance == None:
            self.instance = self.cls(*args,**kwds)
        return self.instance
