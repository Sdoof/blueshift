# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 13:27:48 2018

@author: academy
"""
import pandas as pd
from blueshift.assets.assets import (
        AssetDBConfiguration,
        AssetDBQueryEngineCSV,
        AssetFinder)
import unittest

asset_db_config = AssetDBConfiguration()
asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
asset_finder = AssetFinder(asset_db_query_engine)

n = len(asset_db_query_engine.asset_db)
n = 442
sids = [i for i in range(n)]

t1 = pd.Timestamp.now()
x1 = asset_finder.fetch_assets(sids)
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

t1 = pd.Timestamp.now()
y1 = asset_finder.fetch_assets(sids)
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

syms = asset_db_query_engine.asset_db.symbol.tolist()

t1 = pd.Timestamp.now()
x2 = asset_finder.lookup_symbols(syms)
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

t1 = pd.Timestamp.now()
y2 = asset_finder.lookup_symbols(syms)
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

t1 = pd.Timestamp.now()
for sym in syms:
    asset_finder.lookup_symbol(sym, pd.Timestamp('2018-10-03',tz='Etc/UTC'))
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

t1 = pd.Timestamp.now()
for sym in syms:
    asset_finder.lookup_symbol(sym, pd.Timestamp('2018-10-03',tz='Etc/UTC'))
t2 = pd.Timestamp.now()
print((t2-t1).total_seconds()*1000)

class TestAssets(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_asset_lookups(self):
        self.assertEqual(len(x1), len(y1))
        self.assertEqual(len(x2), len(y2))
        self.assertEqual(len(x1), len(x2))
        self.assertEqual(x1[99].symbol, x2[99].symbol)
        
if __name__ == '__main__':
    unittest.main()