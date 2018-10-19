# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 23:24:18 2018

@author: prodipta
"""

def positive_int(x):
    if isinstance(x, int) and x > 0:
        return True, ""
    return False, "Invalid argument {} in function {}, expected"  \
                    "positive integer"

def positive_num(x):
    if isinstance(x, (int, float)) and x > 0:
        return True, ""
    return False, "Invalid argument {} in function {}, expected" \
                    "positive number"