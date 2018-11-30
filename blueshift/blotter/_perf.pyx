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
Created on Mon Oct  8 09:28:57 2018

@author: prodipta
"""

cimport cython
cimport numpy as np
import numpy as np
import blueshift.blotter._perf

cdef int CHUNK_SIZE = 4096
BASE_METRICS = ['net','cash']
DAILY_METRICS = ['net',
                 'cash',
                 'margin',
                 'gross_leverage',
                 'net_leverage',
                 'gross_exposure',
                 'net_exposure',
                 'mtm',
                 'liquid_value',
                 'commissions'
                 ]

cdef class Performance:
    def __init__(self, dict account, np.int64_t timestamp):
        self.last_updated = timestamp
        self.currency = account["currency"]
        
        self.pnls = np.zeros((CHUNK_SIZE, len(BASE_METRICS)))
        self.perfs = np.zeros((CHUNK_SIZE, len(DAILY_METRICS)))
        self.index_pnls = np.zeros(CHUNK_SIZE)
        self.index_perfs = np.zeros(CHUNK_SIZE)
        self.pos_pnls = 0
        self.pos_perfs = 0
        
        self.pnls[self.pos_pnls,] = [account.get(k,0) for k in BASE_METRICS]
        self.perfs[self.pos_perfs,] = [account.get(k,0) for k in DAILY_METRICS]
        self.index_pnls[self.pos_pnls] = timestamp
        self.index_perfs[self.pos_perfs] = timestamp
        
        self.pos_pnls = self.pos_pnls + 1
        self.pos_perfs = self.pos_perfs + 1
                   
    
    cpdef update_perfs(self, dict account, np.int64_t timestamp):
        if self.pos_perfs >= len(self.index_perfs):
            # resize the array
            perfs = np.zeros((CHUNK_SIZE, len(DAILY_METRICS)))
            index_perfs = np.zeros(CHUNK_SIZE)
            self.perfs = np.concatenate((self.perfs,perfs))
            self.index_perfs = np.concatenate((self.index_perfs,index_perfs))
        
        self.perfs[self.pos_perfs,] = [account.get(k,0) for k in DAILY_METRICS]
        self.index_perfs[self.pos_perfs] = timestamp
        self.pos_perfs = self.pos_perfs + 1
    
    cpdef update_pnls(self, dict account, np.int64_t timestamp):
        if self.pos_pnls >= len(self.index_pnls):
            # resize the array
            pnls = np.zeros((CHUNK_SIZE, len(BASE_METRICS)))
            index_pnls = np.zeros(CHUNK_SIZE)
            self.pnls = np.concatenate((self.pnls,pnls))
            self.index_pnls = np.concatenate((self.index_pnls,index_pnls))
        
        self.pnls[self.pos_pnls,] = [account.get(k,0) for k in BASE_METRICS]
        self.index_pnls[self.pos_pnls] = timestamp
        self.pos_pnls = self.pos_pnls + 1
    
    cpdef get_last_perf(self):
        return self.perfs[(self.pos_perfs - 1),]
    
    cpdef get_last_pnl(self):
        return self.pnls[(self.pos_pnls - 1),]
    
    cpdef get_past_perfs(self, long count):
        cdef long start_idx = 0
        if count > self.pos_perfs:
            count = self.pos_perfs
        start_idx = self.pos_perfs - count
        return self.index_perfs[start_idx:self.pos_perfs],self.perfs[start_idx:self.pos_perfs,]
    
    cpdef get_past_pnls(self, long count):
        cdef long start_idx = 0
        if count > self.pos_pnls:
            count = self.pos_pnls
        
        start_idx = self.pos_pnls - count
        return self.index_pnls[start_idx:self.pos_pnls],self.pnls[start_idx:self.pos_pnls,]
    
    
    
    
    
    
    
    