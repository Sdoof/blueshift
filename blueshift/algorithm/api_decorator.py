# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 14:50:03 2018

@author: prodipta
"""

import blueshift.api


def api_method(f):
    '''
        decorator to map bound API functions to unbound user 
        functions. First add to the function to the list of available 
        API functions in the api module. Then set the api attribute to 
        scan during init for late binding.
    '''
    setattr(blueshift.api, f.__name__, f)
    blueshift.api.__all__.append(f.__name__)
    f.is_api = True
    return f

def command_method(f):
    '''
        decorator flag a method is a command method in the algorithm.
    '''
    f.is_command = True
    return f