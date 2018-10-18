# -*- coding: utf-8 -*-
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