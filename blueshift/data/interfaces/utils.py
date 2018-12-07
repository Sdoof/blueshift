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
Created on Thu Dec  6 09:20:52 2018

@author: prodipta
"""
import pandas as pd
from hashlib import md5

def merge_date_time(x:pd.Timestamp,y:pd.Timestamp):
    '''
        This function takes in a date part (as naive timestamp) and a 
        time part (as Timestamp to today's date), and return a combined 
        timestamp.
    '''
    x = pd.Timestamp(x)
    y = pd.Timestamp(y)
    return pd.Timestamp(x.value + y.value - y.normalize().value)

def one():
    '''
        This function returns a constant value.
    '''
    return 1

def no_change(value):
    '''
        A function to return a value unchanged.
    '''
    return value

def dataframe_hash(df):
    first_row = ''.join([str(e) for e in df.iloc[0].tolist()])
    last_row = ''.join([str(e) for e in df.iloc[-1].tolist()])
    checksum = (first_row + last_row).encode()
    return md5(checksum).hexdigest()