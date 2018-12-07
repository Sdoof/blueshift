# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 10:43:45 2018

@author: prodipta
"""

import bcolz
import os
import pandas as pd
import random
import sqlalchemy as sa

def get_random_sym(syms):
    idx = random.randint(0,len(syms)-1)
    return syms[idx]

def query_ctable(ct, syms):
    sym = get_random_sym(syms)
    query_string = str(f"symbol=='{sym}'")
    return list(ct.where(query_string, vm='python'))
    
def query_pandas(df, syms):
    sym = get_random_sym(syms)
    return df.loc[df.symbol==sym]

def query_sql(db_path, table_name, syms):
    sym = get_random_sym(syms)
    query = f"select * from {table_name} where symbol = '{sym}'"
    return select_from_table(db_path, table_name, query)
    
def get_all_tables_sqlite(db_path):
    db_path = "sqlite:///"+db_path
    engine = sa.create_engine(db_path)
    conn = engine.connect()
    query = "select name from sqlite_master where type='table'"
    return pd.read_sql(query,conn)

def select_all_table(db_path, table_name):
    db_path = "sqlite:///"+db_path
    engine = sa.create_engine(db_path)
    conn = engine.connect()
    query = f"select * from {table_name}"
    return pd.read_sql(query,conn)

def select_from_table(db_path, table_name, query):
    db_path = "sqlite:///"+db_path
    engine = sa.create_engine(db_path)
    conn = engine.connect()
    return pd.read_sql(query,conn)
    
df = pd.read_csv(os.path.expanduser("~/.blueshift/data/asset_db.csv"))
syms = df.symbol

ct = bcolz.ctable.fromdataframe(df, 
                                rootdir=os.path.expanduser(
                                        "~/.blueshift/data/asset_db.bcolz"))
ct = bcolz.ctable(rootdir=os.path.expanduser(
                                        "~/.blueshift/data/asset_db.bcolz"))

engine = sa.create_engine('sqlite:///'+ 
                          os.path.expanduser(
                                  "~/.blueshift/data/asset_db.sqlite"))


df.iloc[:,:18].to_sql('equities', con=engine, if_exists='append', chunksize=50)

'''
    best asset db is either in memory pandas dataframe or sqlite. Explore
    postgreSQL as well for scaling later.
'''
import os
from blueshift.data.ingestors.ingestor import OHLCVCSVtoBColzIngestor,DataTransform
from blueshift.data.interfaces.utils import merge_date_time, no_change, one
from blueshift.data.interfaces.bcolzio import BColzWriter, BcolzSchema, BColzReader

strpath = 'C:/Users/academy.academy-72/Desktop/dev platform/data/GDFL/data'
strfile = 'GFDLCM_STOCK_16042018.csv'
root_dir = os.path.expanduser('~/.blueshift/data/gdfl.bcolz')
    
input_cols = ['Ticker', 'Date', 'Time', 'Open', 'High', 'Low', 
                    'Close', 'Volume','Open Interest']

trans_dict = {'timestamp':DataTransform(merge_date_time,['Date','Time']),
              'symbol':DataTransform(no_change,['Ticker']),
              'open': DataTransform(no_change,['Open']),
              'high': DataTransform(no_change,['High']),
              'low': DataTransform(no_change,['Low']),
              'close': DataTransform(no_change,['Close']),
              'volume': DataTransform(no_change,['Volume']),
              'adj_ratio':DataTransform(one,[])}


converter = OHLCVCSVtoBColzIngestor(frequency='1m',
                                    cols = input_cols,
                                    transformation=trans_dict,
                                    scaling=10000,
                                    symbol_col='symbol',
                                    index_col='timestamp')

source = os.path.join(strpath,strfile)


schema = BcolzSchema(root=os.path.expanduser('~/.blueshift/bcolz'), 
                     prefixes=["minute"],
                     sid_splits = [2,2])

writer = BColzWriter(ncols=6, 
                     names=["open","high","low","close","volume","adj_ratio"], 
                     meta_data={"scaling":10000,'noscale':['volume']}, 
                     schema=schema)

sid = 1
for sym, data, freq in converter.read_large_csv(source):
    writer.write_dataframe(sid, data)
    sid = sid + 1


reader = BColzReader(schema=schema)
df = reader.read_dataframe(6)

import bcolz
ct = bcolz.ctable(rootdir=os.path.expanduser('~/.blueshift/bcolz/minute/00/00/000001.bcolz'))