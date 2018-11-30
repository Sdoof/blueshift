# Copyright 2018 QuantInsti Quantitative Learnings Pvt Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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



def exec_user_module(source, module, path):
    '''
        function to load multi-file user code in to Blueshift. This
        execs the source_file, which may contain full (NOT relative)
        import of other resources from the module `module_name`. The
        path is usually the local source dir under the Blueshift
        root which contains the `module_name`, which in turn contains
        the `source_file`.
    '''
    namespace = {}
    
    if os_path.isfile(source):
        source_file = os_path.basename(source)
        if module==None:
            with open(source) as algofile:
                algo_text = algofile.read()
            code = compile(algo_text,source_file,'exec')
            exec(code, namespace)
        else:
            module_path = os_path.expanduser(path)
            with AddPythonPath(module_path):
                path = os_path.join(module_path, module, source)
                with open(path) as fp:
                    algo_text = fp.read()
                code = compile(algo_text,source_file,'exec')
                exec(code, namespace)
    elif isinstance(source, str):
            source_file = "<string>"
            algo_text = source
            code = compile(algo_text,source_file,'exec')
            exec(code, namespace)
    else:
        raise 
    
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
    
def generate_args(strargs):
    if not strargs:
        return []
    
    strargs = strargs.replace('-','_')
    return strargs.split(',')


def generate_kwargs(strkwargs):
    kwargs = {}
    if not strkwargs:
        return kwargs
    
    strkwargs = strkwargs.replace('-','_')
    pairs = strkwargs.split(',')
    for pair in pairs:
        pair = pair.split('=')
        if len(pair)<2:
            key, value = pair[0], None
        else:
            key, value = tuple(pair[:2])
        kwargs[key] = value
        
    return kwargs
        
    
    
    