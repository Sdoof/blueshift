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
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython
from blueshift.assets._assets cimport Asset

cdef class Trade:
    # class declaration for cimport
    cdef readonly int tid
    cdef readonly int hashed_tid
    cdef readonly object oid
    cdef readonly object broker_order_id
    cdef readonly object exchange_order_id
    cdef readonly int instrument_id
    cdef readonly object side
    cdef readonly int product_type
    cdef readonly float average_price
    cdef readonly float cash_flow
    cdef readonly float margin
    cdef readonly float commission
    cdef readonly object exchange_timestamp
    cdef readonly object timestamp
    cdef readonly Asset asset
    cdef readonly int quantity
    cpdef to_dict(self)
    cpdef __reduce__(self)