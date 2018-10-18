# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 11:22:26 2018

@author: prodipta
"""
from blueshift.algorithm.api import api_function

def initialize(context):
    api_function("test1")
    
def handle_data(context, data):
    pass
