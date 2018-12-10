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
Created on Thu Dec  6 09:50:26 2018

@author: prodipta
"""

from os import path as os_path
import numpy as np
import pandas as pd
import bcolz


from blueshift.configs.defaults import ensure_directory
from blueshift.data.interfaces.interface import DataWriter, DataReader
from blueshift.data.interfaces.utils import dataframe_hash
from blueshift.utils.types import NANO_SECOND

'''
    We define asset ids to be upto 6 digit (so max possible is 999999)
'''
class BcolzSchema(object):
    '''
        The directory structure begins at the root. The directories are structured 
        first as daily vs minute sub-dirs at first level, followed by asset level
        prefixes (six digits, split into XX-XX-XX.bcolz).
    '''
    def __init__(self, root, prefixes=[], max_assets=6, sid_splits=[2,2],
                 expectedlen=0):
        self._root = root
        self._max_sid_digits = max_assets
        self._sid_split_levels = sid_splits
        self._prefixes = prefixes
        self._expectedlen = expectedlen
        if expectedlen == 0:
            # see http://bcolz.blosc.org/en/latest/opt-tips.html
            ##informing-about-the-length-of-your-carrays
            self._expectedlen = 500*252*15
        
    def map_sid_to_path(self, sid):
        chrsid = str(sid).zfill(self._max_sid_digits)
        sub_dirs = []
        start = 0
        for pos in self._sid_split_levels:
            end = pos+start
            sub_dirs.append(chrsid[start:end])
            start = end
        return os_path.join(self._root, *self._prefixes, 
                            *sub_dirs, chrsid+".bcolz")
    
    def map_path_to_sid(self, sid_path):
        try:
            return int(os_path.splitext(os_path.basename(str(sid_path)))[0])
        except (ValueError, TypeError):
            raise ValueError("not valid path")
            
    def write_dataframes(self, sids, *args, **kwargs):
        pass


class BColzWriter(DataWriter):
    '''
        serialize data to bcolz. Data must be in the form of dataframe
        (or convertible to such) and integer (signed 32).
    '''
    INDEX_NAME = 'timestamp'
    SCALE_KEY = 'scaling'
    NOSCALE_KEY = 'noscale'
    
    def __init__(self, ncols, names, meta_data={}, *args, **kwargs):
        self._type = 'BColz'
        self._ncols = ncols
        self._colnames = names
        self._meta_data = meta_data
        self._cparams = kwargs.pop("cparams", bcolz.cparams())
        self._schema = kwargs.pop("schema", None)
        
        if not isinstance(self._schema, BcolzSchema):
            raise ValueError("Illegal or no schema supplied.")
            
        if not isinstance(self._cparams, bcolz.toplevel.cparams):
            try:
                self._cparams = bcolz.cparams(**self._cparams)
            except (TypeError, NameError):
                raise ValueError("Illegal compression params supplied.")
        
    def _create_ctable(self, sid_path):
        sid_dir = os_path.dirname(sid_path)
        ensure_directory(sid_dir)
        ncols = self._ncols + 1 # for timestamp column
        colnames = [self.INDEX_NAME] + self._colnames
        columns = [np.empty(0, np.int32)]*ncols
        
        ct = bcolz.ctable(rootdir = sid_path, columns = columns, 
                          names=colnames, 
                          expectedlen=self._schema._expectedlen, mode='w')
        
        for key in self._meta_data:
            ct.attrs[key] = self._meta_data[key]
        ct.flush()
        
        return ct

    def _ensure_ctable(self, sid):
        sid_path = self._schema.map_sid_to_path(sid)
        if not os_path.exists(sid_path):
            return self._create_ctable(sid_path)
        return bcolz.ctable(rootdir=sid_path, mode='a')
            
    def _update_meta_data(self, sid, meta_data):
        ct = self._ensure_ctable(sid)
        for key in self._meta_data:
            ct.attr[key] = self._meta_data[key]
        ct.flush()
        
    def write_dataframe(self, sid, df):
        ct = self._ensure_ctable(sid)
        current_hash = dataframe_hash(df)
        try:
            last_hash = ct.attrs['hash']
            if current_hash  == last_hash:
                return
        except KeyError:
            pass
        dts = df.index
        cols = [dts]+[df[name] for name in self._colnames]

        ct.append(cols)
        ct.attrs['hash'] = current_hash
        ct.flush()
        
class BColzReader(DataReader):
    '''
        de-serialize data to bcolz. Data must be in the form of numpy array
        (or convertible to such) and integer (signed 32).
    '''
    INDEX_NAME = 'timestamp'
    SCALE_KEY = 'scaling'
    NOSCALE_KEY = 'noscale'
    
    def __init__(self, schema, *args, **kwargs):
        self._type = 'BColz'
        self._schema = schema
        
    def read_dataframe(self, sid):
        sid_path = self._schema.map_sid_to_path(sid)
        try:
            ct = bcolz.ctable(rootdir=sid_path)
            scale = ct.attrs[self.SCALE_KEY]
            try:
                no_scale_cols = ct.attrs[self.NOSCALE_KEY]
            except KeyError:
                no_scale_cols = None
            return self._to_dataframe(ct, scale, no_scale_cols)
        except:
            ValueError(f"{sid} could not be found.")
            
    def _to_dataframe(self, ct, scale, no_scale_cols=None):
        df = ct.todataframe()
        df[self.INDEX_NAME] = pd.to_datetime(df[self.INDEX_NAME].\
                                  astype(np.int64)*NANO_SECOND)
        
        df = df.set_index(self.INDEX_NAME)
        
        names = ct.names.copy()
        names.remove(self.INDEX_NAME)
        
        for col in names:
            if no_scale_cols:
                if col in no_scale_cols:
                    continue
            df[col] = df[col]/scale
            
        return df
        
    def _read_field(self, sid, field):
        sid_path = self._schema.map_sid_to_path(sid)
        ts_path = os_path.join(sid_path, self.INDEX_NAME)
        f_path = os_path.join(sid_path, field)
        
        
        