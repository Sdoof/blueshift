# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 17:28:53 2018

@author: academy
"""

from sys import getsizeof as sys_getsizeof
from collections import OrderedDict
from os import path as os_path
from blueshift.utils.ctx_mgr import AddPythonPath

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys_getsizeof(obj)
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
    
class OnetoOne(object):
    '''
        A data structure to enable a one-to-one mapping. This
        stores two dict objects, so not mighty useful for large
        dicts. Use with cautions.
    '''
    
    def __init__(self, input_dict):
        '''
            Store a reverse of the dict. If there are repeated
            keys when reverse, it will automatically be truncated.
            Be careful.
        '''
        self.__dict = input_dict
        self.__reversed_dict = dict((v,k) for k, v in \
                                   self.__dict.items())
        
    def get(self,key,default=None):
        return self.__dict.get(key,default)
    
    def teg(self, key, default=None):
        return self.__reversed_dict.get(key, default)



def import_user_module(source_file, module_name, path):
    '''
        function to load multi-file user code in to Blueshift. This
        execs the source_file, which may contain full (NOT relative)
        import of other resources from the module `module_name`. The
        path is usually the local source dir under the Blueshift 
        root which contains the `module_name`, which in turn contains
        the `source_file`.
    '''
    module_path = os_path.expanduser(path)
    
    with AddPythonPath(module_path):
        namespace = {}
        path = os_path.join(module_path, module_name,source_file)
        with open(path) as fp:
            algo_text = fp.read()
        
        code = compile(algo_text,source_file,'exec')
        exec(code, namespace)
    
    return namespace
    
    
def list_to_args_kwargs(opt_list):
    '''
        Utility to convert extra arguments passed from command 
        processors (click) in to args and kwargs
    '''
    args = []
    kwargs = {}
    processed = False
    
    extract_param = lambda s:s.strip('-').replace('-','_')
    
    for idx, opt in enumerate(opt_list):
        if processed:
            processed = False
            continue
        if not opt.startswith('-'):
            args.append(extract_param(opt))
        elif idx+1 < len(opt_list) and opt_list[idx+1].startswith('-'):
            args.append(extract_param(opt))
        elif idx+1 < len(opt_list):
            kwargs[extract_param(opt)] = extract_param(
                    opt_list[idx+1])
            processed = True
        else:
            args.append(extract_param(opt))
            
    return args, kwargs
    