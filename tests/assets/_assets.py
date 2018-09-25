# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 18:47:19 2018

@author: prodipta
"""

from pandas import Timestamp
import unittest
from blueshift.assets._assets import (MarketData, 
                                      Asset,
                                      Equity,
                                      EquityFutures,
                                      Forex,
                                      EquityOptions)
                                      

mktdata = MarketData(1,'NIFTY','S&P NIFTY 50 Index',
                     Timestamp('1990-01-01'),
                     Timestamp('2019-12-31'))

asset = Asset(2,'NIFTY','S&P NIFTY 50 Index',
                     Timestamp('1990-01-01'),
                     Timestamp('2019-12-31'),
                     auto_close_date=Timestamp('2019-12-31'),
                     exchange_name='NSE',
                     calendar_name='NSE')

equity = Equity(3,'NIFTY','S&P NIFTY 50 Index',
                     Timestamp('1990-01-01'),
                     Timestamp('2019-12-31'),
                     auto_close_date=Timestamp('2019-12-31'),
                     exchange_name='NSE',
                     calendar_name='NSE')

futures = EquityFutures(4,1,'NIFTY18SEP11150CE','NIFTY',
                    'Nifty Sep 18 Call 11150', Timestamp('2018-01-01'),
                    Timestamp('2018-09-27'),Timestamp('2018-09-27'),
                    None,75,0.05,None,
                    'NSE-FO','NSE')

fx = Forex(5,"EUR/USD","EUR/USD","EUR","USD","Euro in US Dollar",
           Timestamp('1990-01-01'),Timestamp('2019-12-31'),
           tick_size = 0.0001, exchange_name='FXCM',
           calendar_name='FX_calendar')

opt = EquityOptions(100,1,'NIFTY18SEP11150CE','NIFTY',
                    'Nifty Sep 18 Call 11150', Timestamp('2018-01-01'),
                    Timestamp('2018-09-27'),Timestamp('2018-09-27'),
                    None,11150,75,0.05,None,
                    'NSE-FO','NSE')

mktdata_dict = {'sid': 1,
 'symbol': 'NIFTY',
 'name': 'S&P NIFTY 50 Index',
 'start_date': Timestamp('1990-01-01 00:00:00'),
 'end_date': Timestamp('2019-12-31 00:00:00'),
 'mktdata_type': 1}

asset_dict = {'sid': 2,
 'symbol': 'NIFTY',
 'name': 'S&P NIFTY 50 Index',
 'start_date': Timestamp('1990-01-01 00:00:00'),
 'end_date': Timestamp('2019-12-31 00:00:00'),
 'mktdata_type': 1,
 'mult': 1.0,
 'tick_size': 0.009999999776482582,
 'auto_close_date': Timestamp('2019-12-31 00:00:00'),
 'exchange_name': 'NSE',
 'calendar_name': 'NSE',
 'asset_class': 1}

equity_dict = {'sid': 3,
 'symbol': 'NIFTY',
 'name': 'S&P NIFTY 50 Index',
 'start_date': Timestamp('1990-01-01 00:00:00'),
 'end_date': Timestamp('2019-12-31 00:00:00'),
 'mktdata_type': 1,
 'mult': 1.0,
 'tick_size': 0.009999999776482582,
 'auto_close_date': Timestamp('2019-12-31 00:00:00'),
 'exchange_name': 'NSE',
 'calendar_name': 'NSE',
 'asset_class': 1}

futures_dict = {'sid': 4,
 'symbol': 'NIFTY18SEP11150CE',
 'name': 'Nifty Sep 18 Call 11150',
 'start_date': Timestamp('2018-01-01 00:00:00'),
 'end_date': Timestamp('2018-09-27 00:00:00'),
 'mktdata_type': 1,
 'mult': 75.0,
 'tick_size': 0.05000000074505806,
 'auto_close_date': Timestamp('2018-09-27 00:00:00'),
 'exchange_name': 'NSE-FO',
 'calendar_name': 'NSE',
 'asset_class': 2,
 'root': 'NIFTY',
 'underlying_sid': 1,
 'expiry_date': Timestamp('2018-09-27 00:00:00'),
 'notice_date': Timestamp('2018-09-27 00:00:00')}

fx_dict = {'sid': 5,
 'symbol': 'EUR/USD',
 'name': 'Euro in US Dollar',
 'start_date': Timestamp('1990-01-01 00:00:00'),
 'end_date': Timestamp('2019-12-31 00:00:00'),
 'mktdata_type': 1,
 'mult': 1.0,
 'tick_size': 9.999999747378752e-05,
 'auto_close_date': None,
 'exchange_name': 'FXCM',
 'calendar_name': 'FX_calendar',
 'asset_class': 4,
 'ccy_pair': 'EUR/USD',
 'base_ccy': ('EUR',),
 'quote_ccy': ('USD',)}

opt_dict = {'sid': 100,
 'symbol': 'NIFTY18SEP11150CE',
 'name': 'Nifty Sep 18 Call 11150',
 'start_date': Timestamp('2018-01-01 00:00:00'),
 'end_date': Timestamp('2018-09-27 00:00:00'),
 'mktdata_type': 1,
 'mult': 75.0,
 'tick_size': 0.05000000074505806,
 'auto_close_date': Timestamp('2018-09-27 00:00:00'),
 'exchange_name': 'NSE-FO',
 'calendar_name': 'NSE',
 'asset_class': 3,
 'root': 'NIFTY',
 'underlying_sid': 1,
 'expiry_date': Timestamp('2018-09-27 00:00:00'),
 'notice_date': Timestamp('2018-09-27 00:00:00'),
 'strike': 11150.0}



class TestAssets(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_dicts(self):
        self.assertEqual(mktdata.to_dict(), mktdata_dict)
        self.assertEqual(asset.to_dict(), asset_dict)
        self.assertEqual(equity.to_dict(), equity_dict)
        self.assertEqual(futures.to_dict(), futures_dict)
        self.assertEqual(fx.to_dict(), fx_dict)
        self.assertEqual(opt.to_dict(), opt_dict)
        
if __name__ == '__main__':
    unittest.main()