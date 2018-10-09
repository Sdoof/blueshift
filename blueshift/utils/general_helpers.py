# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 17:28:53 2018

@author: academy
"""

import sys
from collections import OrderedDict

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


class MaxSizedOrderedDict(OrderedDict):
    '''
        Extends OrderedDict to force a limit. Delete in FIFO when
        this limit exceeds. Delete items in chunks to avoid keep 
        hitting the limits after a given number of insertions
    '''
    MAX_ENTRIES = 1000000
    CHUNK_SIZE = 1000
    
    def __init__(self, *args, **kwargs):
        self.max_size = kwargs.pop("max_size",self.MAX_ENTRIES)
        self.chunk_size = kwargs.pop("chunk_size",self.CHUNK_SIZE)
        print(args)
        print(kwargs)
        super(MaxSizedOrderedDict,self).__init__(*args, **kwargs)
        
    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._ensure_size()
        
    def _ensure_size(self):
        if self.max_size is None:
            return
        if self.max_size > len(self):
            return
        
        for i in range(self.chunk_size):
            self.popitem(last=False)
    
    
    
    
    
    
    
    
    
    