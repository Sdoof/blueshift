# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 22:26:24 2018

@author: prodipta
"""

import cython

cpdef check_input(object f, dict env):
    cdef str var
    cdef object check
    
    for var, check in f.__annotations__.items():
        val = env[var]
        if type(check)==type:
            msg = "Invalid argument {} in function {}: expected type {}".format(var,f.__name__,check)
            if not isinstance(val, check):
                raise ValueError(msg)
        elif callable(check):
            truth, msg = check(val)
            if not truth:
                raise ValueError(msg.format(var,f.__name__)) 
                
cpdef check_input2(dict annotations, str name, dict env):
    cdef str var
    cdef object check
    
    for var, check in annotations.items():
        val = env[var]
        if type(check)==type:
            msg = "Invalid argument {} in function {}: expected type {}".format(var,name,check)
            if not isinstance(val, check):
                raise ValueError(msg)
        elif callable(check):
            truth, msg = check(val)
            if not truth:
                raise ValueError(msg.format(var,name)) 