# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 10:00:58 2018

@author: academy
"""
import os
from abc import ABCMeta
import pandas as pd
import json
import sqlalchemy as sa
import pymongo
from functools import lru_cache
from blueshift.assets._assets import create_asset_from_dict
from blueshift.utils.cutils import check_input

# TODO: add instrument id in hash, also add search by instrument id

LRU_CACHE_SIZE = 4096

class AssetDBConfiguration(object):
    '''
        This tells where and how to look for asset data. All asset
        related info can sit in a single file/ table/ collection. 
        Another source is required in case we want to capture 
        potential change in symbols (typically applicable to equities
        only). This is the symbol mapping file/ table/ collection.
    '''
    
    def __init__(self, *args, **kwargs):
        self.type = kwargs.get("db_type","csv")
        self.conn_string = kwargs.get("conn_string",".")
        self.db_name = kwargs.get("db_name","asset_db.csv")
        self.sym_map = kwargs.get("sym_map",None)
        self.table_name = kwargs.get("table_name","asset_db.csv")
        
    def __str__(self):
        return "AssetDBConfiguration, db type:%s, db name:%s" % (
                self.type, self.db_name)
        
    def __repr__(self):
        return self.__str__()
    
    def to_json(self):
        d = {}
        d['type'] = self.type
        d['conn_string'] = self.conn_string
        d['db_name'] = self.db_name
        d['sym_map'] = self.sym_map
        d['table_name'] = self.table_name
        return json.dumps(d)
    
    @classmethod
    def from_json(cls, jsonstr:str):
        check_input(cls.from_json,locals())
        d = json.loads(jsonstr)
        return cls(**d)

        

class AssetDBQueryInterface(metaclass=ABCMeta):
    '''
        ABC for the asset db implementation interface. Any type of
        asset db (csv, sqlite, mongo or others) must implement this
        interface so that asset finder object can talk to the db.
    '''
    
    def __init__(self, asset_db_config):
        self.asset_db_config = asset_db_config
    
    def query_asset_class_type(self,sids):
        raise NotImplementedError
        
    def query_instrument_type(self,sids):
        raise NotImplementedError
        
    def query_marketdata_type(self,sids):
        raise NotImplementedError
        
    def query_symbols(self,sids):
        raise NotImplementedError
        
    def query_exchange(self,sids):
        raise NotImplementedError
        
    def query_calendar(self,sids):
        raise NotImplementedError
        
    def query_cols_filtered(self,query_col, *fetch_cols, filter_col, 
                            filter_value):
        raise NotImplementedError
        
class AssetDBQueryEngineCSV(AssetDBQueryInterface):
    '''
        A simple CSV implementation of the asset db interface.
    '''
    def __init__(self, asset_db_config):
        super(AssetDBQueryEngineCSV,self).__init__(asset_db_config)
        str_path = os.path.join(self.asset_db_config.conn_string,
                                self.asset_db_config.db_name)
        with open(str_path) as asset_db_file:
            self.asset_db = pd.read_csv(asset_db_file)
        
        if self.asset_db_config.sym_map:
            str_path = os.path.join(self.asset_db_config.conn_string,
                                self.asset_db_config.sym_map)
            with open(str_path) as sym_map_file:
                self.sym_map = pd.read_csv(sym_map_file)
        
    def query_asset_class_type(self,sids):
        return self.asset_db.asset_class[self.asset_db.sid.isin(sids)]
        
    def query_instrument_type(self,sids):
        return self.asset_db.instrument_type[self.asset_db.sid.isin(sids)]
        
    def query_marketdata_type(self,sids):
        return self.asset_db.mktdata_type[self.asset_db.sid.isin(sids)]
        
    def query_symbols(self,syms):
        return self.asset_db.sid[self.asset_db.symbol.isin(syms)]
        
    def query_exchange(self,sids):
        return self.asset_db.exchange_name[self.asset_db.sid.isin(sids)]
        
    def query_calendar(self,sids):
        return self.asset_db.calendar_name[self.asset_db.sid.isin(sids)]
        
    def query_cols_filtered(self, filter_col, filter_value, 
                        filter_type, fetch_cols):
        if filter_type == "in":
            x = self.asset_db.loc[self.asset_db[filter_col].isin(filter_value),
                             fetch_cols]
            if len(x)==0:
                return None
            elif len(x)==1:
                return x[0]
            else:
                return x.to_list()
        elif filter_type == "equals":
            x = self.asset_db.loc[self.asset_db[filter_col] == filter_value,
                             fetch_cols]
            return x
        else:
            raise ValueError("Unknown filter type")
            
    def query_all_filtered(self, filter_col, filter_value, 
                           filter_type):
        if filter_type == "in":
            x = self.asset_db.loc[self.asset_db[filter_col].isin(filter_value)]
            return x
        elif filter_type == "equals":
            x = self.asset_db.loc[self.asset_db[filter_col] == filter_value]
            return x
        else:
            raise ValueError("Unknown filter type")
    
            
class AssetFinder(object):
    '''
        The asset finder that interfaces with user API to fetch and
        look up assets.
    '''
    
    def __init__(self, query_engine):
        self.query_engine = query_engine
        self._caches = (self._asset_cache, self._sym_map_cache) \
                    = {}, {}
        
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def fetch_asset(self, sid):
        asset_data = self.query_engine.query_all_filtered("sid",sid,"equals")
    
        if asset_data.empty:
            return None
        
        return create_asset_from_dict(asset_data.iloc[0].to_dict())
    
    def fetch_assets(self, sids):
        assets = []
        for sid in sids:
            assets.append(self.fetch_asset(sid))
            
        return assets
    
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def lookup_symbol(self, sym, as_of_date=None):
        sid = self.query_engine.query_cols_filtered("symbol",sym,
                                                    "equals",
                                                    "sid")
        if sid.empty:
            return None
        
        return self.fetch_asset(sid.iloc[0])
    
    def lookup_symbols(self, syms, as_of_date=None):
        assets = []
        for sym in syms:
            assets.append(self.lookup_symbol(sym,as_of_date))
            
        return assets
        
        
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        