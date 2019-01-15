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

# compile with <cythonize -i _order.pyx>
cimport cython
cimport _order_types
from blueshift.trades._order_types import (
        ProductType,
        OrderFlag,
        OrderType,
        OrderValidity,
        OrderSide,
        OrderStatus,
        OrderUpdateType)
from _trade cimport Trade
from _position cimport Position
from blueshift.assets._assets cimport Asset

cdef class Order:
    '''
        Order objects definition. This provisions for order group
        through parent order ID, as well as other standard fields.
        The `oid` is the field through which the platform tracks an 
        order (which can be different from broekr or exchange IDs).
    '''
    cdef readonly object oid
    cdef readonly int hashed_oid
    cdef readonly object broker_order_id
    cdef readonly object exchange_order_id
    cdef readonly object parent_order_id
    cdef readonly Asset asset
    cdef readonly object user
    cdef readonly object placed_by      # the algo ID!
    cdef readonly int product_type
    cdef readonly int order_flag
    cdef readonly int order_type
    cdef readonly int order_validity
    cdef readonly int quantity
    cdef readonly int filled
    cdef readonly int pending
    cdef readonly int disclosed
    cdef readonly float price
    cdef readonly float average_price
    cdef readonly float trigger_price
    cdef readonly float stoploss_price
    cdef readonly int side
    cdef readonly int status
    cdef readonly object status_message
    cdef readonly object exchange_timestamp
    cdef readonly object timestamp
    cdef readonly object tag
    
    cpdef to_dict(self)
    cpdef to_json(self)
    cpdef __reduce__(self)
    cpdef update(self,int update_type, object kwargs)
    cpdef partial_execution(self, Trade trade)
    cpdef partial_cancel(self)
    cpdef reject(self, object reason)
    cpdef user_update(self, object kwargs)
    cpdef update_from_pos(self, Position pos, price)
    cpdef is_open(self)
    cpdef is_buy(self)
    
    