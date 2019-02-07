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
Created on Tue Feb  5 14:23:19 2019

@author: prodipta
"""
from blueshift.utils.decorators import blueprint

@blueprint
class BlueShiftEnvWrapper():
    '''
        A wrapper object for Blueshift environment object to make 
        access to it global.
    '''
    def __init__(self, env=None):
        self.instance = env
        
    def get_env(self):
        return self.instance
    
    def register_env(self, env):
        self.instance = env
        
global_env_wrapper = BlueShiftEnvWrapper()
register_env = global_env_wrapper.register_env
get_env = global_env_wrapper.get_env

def blueshit_run_set_name(name):
    env = get_env()
    if env:
        env.name = name
    else:
        print("no environment found to rename.")

def blueshift_run_get_name():
    env = get_env()
    if env:
        return env.name
    
    return "blueshift"