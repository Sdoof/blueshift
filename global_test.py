# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 18:39:25 2018

@author: prodipta
"""
import types

class A():
    
    def __init__(self):
        self.a = 5
        
def func(val):
    return 2*val

a = A()
d = {'key':'value'}
x = 12
y = [1,2,3]

primitives = [int, float, complex, bool, str, set, list, tuple,
              range, frozenset, dict, bytes, types.ModuleType]

objs = globals().copy()

for o in objs:
    if type(objs[o]) not in primitives and objs[o] is not None:
        print(f"name {objs[o]}, type {type(objs[o])}")
        objs[o].trusted = False
        
print(a.trusted)