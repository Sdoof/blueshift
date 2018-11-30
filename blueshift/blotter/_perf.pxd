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
    
cdef class Performance:
    cdef readonly np.int64_t last_updated      
    cdef readonly object currency         
    cdef readonly np.ndarray pnls
    cdef readonly np.ndarray perfs
    cdef readonly np.ndarray index_pnls
    cdef readonly np.ndarray index_perfs
    cdef readonly np.int64_t pos_pnls
    cdef readonly np.int64_t pos_perfs
    
    cpdef update_perfs(self, dict account, np.int64_t timestamp)
    cpdef update_pnls(self, dict account, np.int64_t timestamp)
    cpdef get_last_perf(self)
    cpdef get_last_pnl(self)
    cpdef get_past_perfs(self, long count)
    cpdef get_past_pnls(self, long count)