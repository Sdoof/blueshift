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
Created on Fri Nov  9 14:50:03 2018

@author: prodipta
"""

import blueshift.api


def api_method(f):
    '''
        decorator to map bound API functions to unbound user 
        functions. First add to the function to the list of available 
        API functions in the api module. Then set the api attribute to 
        scan during init for late binding.
    '''
    setattr(blueshift.api, f.__name__, f)
    blueshift.api.__all__.append(f.__name__)
    f.is_api = True
    return f

def command_method(f):
    '''
        decorator to flag a method as a command method in the algorithm.
    '''
    f.is_command = True
    return f