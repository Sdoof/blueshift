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
            min_elapsed = (t - self._rate_limit_since).total_seconds()
            print(min_elapsed)
            if math.floor(min_elapsed) > 0:
                self._rate_limit_count == self._rate_limit
                self._rate_limit_since = pd.Timestamp.now(self.tz)
        
        if self._rate_limit_count == 0:
            raise APIRateLimitCoolOff(msg="Exceeded API rate limit")
        
        self._rate_limit_count = self._rate_limit_count - 1
        return f(*args, **kwargs)
    return decorated