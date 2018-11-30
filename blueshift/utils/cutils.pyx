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
Created on Wed Oct 17 22:26:24 2018

@author: prodipta
"""

from blueshift.utils.exceptions import ValidationError

cpdef check_input(object f, dict env):
    cdef str var
    cdef object check

    for var, check in f.__annotations__.items():
        val = env[var]
        if check.__class__ == type:
            if isinstance(val, check):
                return
            msg = "Invalid argument {} in function {}: expected" \
                    "type {}".format(var,f.__name__,check)
            raise ValidationError(msg)
        elif callable(check):
            truth, msg = check(val)
            if truth:
                return
            raise ValidationError(msg.format(var,f.__name__))
