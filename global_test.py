# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 18:39:25 2018

@author: prodipta
"""
import sys

algo_file = "malicious_code.py"
namespace = {}
blank_namespace = {}

with open(algo_file) as fp:
    algo_text = fp.read()
    
code = compile(algo_text, '<String>', 'exec')
exec(code, namespace)

blank_code = compile('', '<String>', 'exec')
exec(blank_code, blank_namespace)
exclude_list = [*[k for k in blank_namespace],'__doc__']


for k in namespace:
    if k not in exclude_list:
        try:
            namespace[k].trusted = False
            for attrib in dir(namespace[k]):
                if callable(attrib):
                    attrib.trusted = False
        except:
            pass
        
for k in namespace:
    try:
        print(f"object:{k}, type:{type(namespace[k])}, trusted:{namespace[k].trusted}")
        for attrib in dir(namespace[k]):
            print(f"{attrib}:{attrib.trusted}")
    except:
        pass

def get_calling_function():
    """finds the calling function in many decent cases."""
    fr = sys._getframe(2)   # inspect.stack()[1][0]
    co = fr.f_code
    for get in (
        lambda:fr.f_globals[co.co_name],
        lambda:getattr(fr.f_locals['self'], co.co_name),
        lambda:getattr(fr.f_locals['cls'], co.co_name),
        lambda:fr.f_back.f_locals[co.co_name], # nested
        lambda:fr.f_back.f_locals['func'],  # decorators
        lambda:fr.f_back.f_locals['meth'],
        lambda:fr.f_back.f_locals['f'],
        ):
        try:
            func = get()
        except (KeyError, AttributeError):
            pass
        else:
            if func.__code__ == co:
                return func
    raise AttributeError("func not found")
    
def restricted_access(cls):
    class wrapper(object):
        def __init__(self, *args, **kwargs):
            self.wrapped = cls(*args, **kwargs)
            
        def __getattr__(self, name):
            trusted = True
            try:
                f = get_calling_function()
                print(type(f))
                print(f'access {name} of {cls} from {f.__name__}')
                if hasattr(f,'__self__'):
                    trusted = f.__self__.trusted
                else:
                    trusted = self.f.trusted
            except:
                pass
            if trusted:
                return getattr(self.wrapped, name)
            else:
                print("illegal access")
        
    return wrapper

@restricted_access
class A():
    
    def __init__(self):
        self.a = "a"
        
    def get_a(self):
        return self.a
    
def access_a(cls):
    return cls.a

access_a.trusted = False

class B():
    def access_b(self, cls):
        return cls.a
    
def f2():
    var2 = 10
    f1()
    
def f1():
    var1 = 20
    f0()
    
def f0():
    var0 = 30
    print(sys._getframe(2).f_locals)