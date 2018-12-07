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
Created on Fri Dec  7 08:46:16 2018

@author: prodipta
"""

from abc import ABC, abstractmethod

class DataWriter(ABC):
    '''
        Common interface to persist time-series data on disk. Expected input 
        is dataframe indexed by a pandas datetime index.
    '''
    
    def __init__(self, *args, **kwargs):
        self._type = None
    
    @abstractmethod
    def write_dataframe(self, sid, df):
        raise NotImplementedError
        
    def __str__(self):
        return f"Blueshift {self._type} Writer"
    
    def __repr__(self):
        return self.__str__()
    
class DataReader(ABC):
    '''
        Common interface to persist time-series data on disk. Expected input 
        is dataframe indexed by a pandas datetime index.
    '''
    
    def __init__(self, *args, **kwargs):
        self._type = None
    
    @abstractmethod
    def read_dataframe(self, sid, df):
        raise NotImplementedError
        
    def __str__(self):
        return f"Blueshift {self._type} Writer"
    
    def __repr__(self):
        return self.__str__()