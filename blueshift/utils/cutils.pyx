# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 22:26:24 2018

@author: prodipta
"""

from blueshift.utils.exceptions import ValidationError

cpdef check_input(object f, dict env):
    cdef str var
    cdef object check

    for var, check in f.__annotations__.items():
        val = env[var]
        if check.__class__ == type:
            if isinstance(val, check):
                return
            msg = "Invalid argument {} in function {}: expected" \
                    "type {}".format(var,f.__name__,check)
            raise ValidationError(msg)
        elif callable(check):
            truth, msg = check(val)
            if truth:
                return
            raise ValidationError(msg.format(var,f.__name__))
