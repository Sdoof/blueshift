# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 18:34:08 2018

@author: prodipta
"""

from sys import path as sys_path
from os import path as os_path

class AddPythonPath():
    '''
        A context manager to modify sys path with a clean up after
        we are done with the work.
    '''
    def __init__(self, path):
        self.path = os_path.expanduser(path)
        
    def __enter__(self):
        '''
            Add the path to SYS PATH.
        '''
        sys_path.append(self.path)
        return self
    
    def __exit__(self, *args):
        '''
            Some code may already have removed the thing we added.
        '''
        path = sys_path.pop()
        if self.path != path:
            sys_path.append(path)