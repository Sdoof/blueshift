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
Created on Thu Nov 15 18:34:08 2018

@author: prodipta
"""

from sys import path as sys_path
from os import path as os_path
from click._termui_impl import ProgressBar

from blueshift.utils.types import noop

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
            
class CtxMgrWithHooks():
    '''
        A context manager with entry and exit hooks.
    '''
    def __init__(self, preop=None, postop=None, *args, **kwargs):
        self.preop = preop if preop else noop
        self.postop = postop if postop else noop
        self.args = args
        self.kwargs=kwargs
    
    def __enter__(self):
        return self.preop(*(self.args), **(self.kwargs))
    
    def __exit__(self, *args):
        return self.postop(*(self.args), **(self.kwargs))
    
    
class ShowProgressBar():
    '''
        An optional progress bar context manager.
    '''
    def __init__(self, iterable, show_progress=False, *args, **kwargs):
        self.show_progress = show_progress
        self.args = args
        self.kwargs = kwargs
        self.iter = iterable
        
    def __enter__(self):
        if self.show_progress:
            pg = ProgressBar(self.iter,**(self.kwargs), empty_char='-',
                             bar_template='%(label)s  [%(bar)s]  %(info)s',
                             width=36)
            pg.__enter__()
            return pg
        return self.iter
    
    def __exit__(self, *args):
        pass
    
class MessageBrokerCtxManager():
    '''
        A context manager for handling ZMQ sockets creation and 
        clean-up.
    '''
    
    def __init__(self, message_broker, enabled=False):
        self._message_broker = message_broker
        self._enabled = enabled
    
    def __enter__(self):
        if not self._enabled:
            return None
        
        self._message_broker.connect()
        return self._message_broker
    
    def __exit__(self, *args):
        if self._enabled:
            self._message_broker.close()
    
