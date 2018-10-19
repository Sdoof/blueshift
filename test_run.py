# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 10:33:18 2018

@author: prodipta
"""

from blueshift.algorithm.algorithm import TradingAlgorithm

algo = TradingAlgorithm(capital=10000, algo="user_algo.py")
algo.back_test_run()