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
Created on Thu Oct 18 23:24:18 2018

@author: prodipta
"""

def positive_int(x):
    if isinstance(x, int) and x > 0:
        return True, ""
    return False, "Invalid argument {} in function {}, expected"  \
                    "positive integer"

def positive_num(x):
    if isinstance(x, (int, float)) and x > 0:
        return True, ""
    return False, "Invalid argument {} in function {}, expected" \
                    "positive number"