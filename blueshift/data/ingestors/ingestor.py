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
Created on Wed Dec  5 10:32:40 2018

@author: prodipta
"""
import pandas as pd
import numpy as np
from collections import namedtuple
from abc import ABC, abstractmethod

from blueshift.assets._assets import MktDataType
from blueshift.utils.types import NANO_SECOND

'''
    Transformation defines a structure to apply a transformation column
    wise to input data. The `func` specifies the function to be applied,
    and the `arg_cols` list the name of the columns in the dataframe to
    be used as input to this `func`.
'''
DataTransform = namedtuple('DataTransform',["func", "arg_cols"])

class Ingestor(ABC):
    '''
        Base class for data ingeston.
    '''
    def __init__(self, *args, **kwargs):
        self._source_root = None
        self._dest_root = None
        self._frequency = kwargs.pop("frequency", None)
        self._source_type = None
        self._dest_type = None
        self._data_type = None
        
    @property
    def frequency(self):
        return self._frequency
    
    @property
    def source(self):
        self._source_root
        
    @property
    def dest(self):
        self._dest_root
        
    @property
    def source_type(self):
        self._source_type
        
    @property
    def dest_type(self):
        self._dest_type
        
    @property
    def data_type(self):
        self._data_type
        
    @abstractmethod
    def ingest(self, *args, **kwargs):
        pass
        
    
class OHLCVCSVtoBColzIngestor(Ingestor):
    
    def __init__(self, *args, **kwargs):
        super(OHLCVCSVtoBColzIngestor, self).__init__(*args, **kwargs)
        self._source_type = 'csv'
        self._dest_type = 'bcolz'
        self._data_type = MktDataType.OHLCV
        
        self._scale_factor = kwargs.pop('scaling', 10000)
        self._trans_dict = kwargs.pop("transformation", {})
        self._expected_input_cols = kwargs.pop("cols", [])
        self._out_cols = list(self._trans_dict.keys())
        
        self._split_col = kwargs.pop("symbol_col","symbol")
        self._index_col = kwargs.pop("index_col",None)
        self._ohlcva = ['open','high','low','close','volume','adj_ratio']
        
        for c in self._ohlcva:
            if c not in self._out_cols:
                msg = f"transformation is incomplete, missing {c}"
                raise ValueError(msg)
                
        self._convert_dtypes = [np.float64, np.int32, np.int64]
        self.skip_scaling_cols = ["volume"]
        self._read_chunk = kwargs.pop("chunksize", 10000)

    def check_columns(self, df, cols):
        '''
            Given a dataframe check if the expected columns are available.
        '''
        headers = list(df.columns)
        for h in cols:
            if h not in headers:
                msg = f"expected column {h} is missing in data"
                raise ValueError(msg)
                
    def screen_columns(self, df, cols):
        '''
            Screen columns from a input dataframe
        '''
        self.check_columns(df, cols)
        return df[cols]
    
    def transform_df(self, df):
        self.check_columns(df, self._expected_input_cols)
        out_df = pd.DataFrame({})
        for col in self._out_cols:
            out_df[col] = self._apply_transformation(df, 
                  self._trans_dict[col])
        return out_df
    
    def integer_conversion(self, df):
        '''
            We convert all data to int32 for bcolz. Timestamps are converted
            to nano and then to seconds since epoch and saved as int32. All
            floats are multipleid by scale factor and saved as int32. If a
            column is not convertable (like text) we leave it as is.
        '''
        scale_factor = self._scale_factor
        
        for c in df.columns:
            if c=='timestamp':
                df.loc[:,c] = df[c].astype(np.int64)
                df.loc[:,c] = (df[c]/NANO_SECOND).astype(np.int32)
                continue
            
            if df[c].dtype not in self._convert_dtypes:
                continue
            
            if c in self.skip_scaling_cols:
                scale_factor = 1
            else:
                scale_factor = self._scale_factor
            
            df.loc[:,c] = (df[c]*scale_factor).astype(np.int32)
        return df
    
    def _generate_data(self, df):        
        df = self.transform_df(df)
        df = self.integer_conversion(df)
        syms = set(df[self._split_col].tolist())
        
        for sym in syms:
            data = df.loc[df[self._split_col]==sym,:]
            data = self.screen_columns(data, [self._index_col, 
                                              *self._ohlcva])
            if self._index_col:
                data = data.set_index(self._index_col)
            yield sym, data, self._frequency

    @staticmethod
    def _apply_transformation(df, trans:DataTransform):
        args = []
        for a in trans.arg_cols:
            args.append(df[a])
        return np.vectorize(trans.func)(*args)
    
    def read_large_csv(self, source):
        chunks = pd.read_csv(source, chunksize=self._read_chunk)
        for chunk in chunks:
            for sym, data, freq in self._generate_data(chunk):
                print(f"{sym}:{len(data)}")
                yield sym, data, freq
                    
    def _get_sid(self, sym):
        return 
                
    def ingest(self, *args, **kwargs):
        pass


