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
Created on Wed Oct  3 17:28:53 2018

@author: academy
"""

from sys import getsizeof as sys_getsizeof
from os import path as os_path
import pandas as pd
from collections import OrderedDict
import click

from blueshift.trades._position import Position
from blueshift.trades._order import Order
from blueshift.utils.ctx_mgr import AddPythonPath
from blueshift.utils.types import NANO_SECOND, Platform

def datetime_time_to_nanos(dt):
    return (dt.hour*60 + dt.minute)*60*NANO_SECOND

def read_positions_from_dict(positions_dict, asset_finder):
    """read from a dict keyed by asset symbol """
    current_pos = {}
    for sym in positions_dict:
        asset = asset_finder.lookup_symbol(sym)
        pos = positions_dict[sym]
        pos['asset'] = asset
        pos['timestamp'] = pd.Timestamp(pos['timestamp'])
        position = Position.from_dict(positions_dict[sym])
        current_pos[asset] = position
        
    return current_pos

def read_transactions_from_dict(txns_dict, asset_finder, 
                                key_transform=lambda x:x):
    """ read from a timestamped ordered dict of transactions """
    txns = OrderedDict()
    order_ids = set()
    for key in txns_dict:
        values = txns_dict[key]
        transactions = []
        for value in values:
            value['asset'] = asset_finder.lookup_symbol(value['asset'])
            transactions.append(Order.from_dict(value))
            order_ids.add(value['oid'])
        txns[key_transform(key)] = transactions
    return txns, order_ids

def read_orders(orders, asset_finder, key_transform=str):
    """ read from a order_id keyed dictionary of orders """
    out = {}
    order_ids = set()
    for key in orders:
        order = orders[key]
        order['asset'] = asset_finder.lookup_symbol(order['asset'])
        out[key_transform(key)] = Order.from_dict(order)
        order_ids.add(key)
    
    return out, order_ids

def sizeof(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys_getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([sizeof(v, seen) for v in obj.values()])
        size += sum([sizeof(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += sizeof(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([sizeof(i, seen) for i in obj])
    return size

def exec_user_module(source, module, path):
    '''
        function to load multi-file user code in to Blueshift. This
        execs the source_file, which may contain full (NOT relative)
        import of other resources from the module `module_name`. The
        path is usually the local source dir under the Blueshift
        root which contains the `module_name`, which in turn contains
        the `source_file`.
    '''
    namespace = {}
    
    if os_path.isfile(source):
        source_file = os_path.basename(source)
        if module==None:
            with open(source) as algofile:
                algo_text = algofile.read()
            code = compile(algo_text,source_file,'exec')
            exec(code, namespace)
        else:
            module_path = os_path.expanduser(path)
            with AddPythonPath(module_path):
                path = os_path.join(module_path, module, source)
                with open(path) as fp:
                    algo_text = fp.read()
                code = compile(algo_text,source_file,'exec')
                exec(code, namespace)
    elif isinstance(source, str):
            source_file = "<string>"
            algo_text = source
            code = compile(algo_text,source_file,'exec')
            exec(code, namespace)
    else:
        raise 
    
    return namespace
    
    
def list_to_args_kwargs(opt_list):
    '''
        Utility to convert extra arguments passed from command 
        processors (click) in to args and kwargs
    '''
    args = []
    kwargs = {}
    processed = False
    
    extract_param = lambda s:s.strip('-').replace('-','_')
    
    for idx, opt in enumerate(opt_list):
        if processed:
            processed = False
            continue
        if not opt.startswith('-'):
            args.append(extract_param(opt))
        elif idx+1 < len(opt_list) and opt_list[idx+1].startswith('-'):
            args.append(extract_param(opt))
        elif idx+1 < len(opt_list):
            kwargs[extract_param(opt)] = extract_param(
                    opt_list[idx+1])
            processed = True
        else:
            args.append(extract_param(opt))
            
    return args, kwargs
    
def generate_args(strargs):
    if not strargs:
        return []
    
    strargs = strargs.replace('-','_')
    return strargs.split(',')


def generate_kwargs(strkwargs):
    kwargs = {}
    if not strkwargs:
        return kwargs
    
    strkwargs = strkwargs.replace('-','_')
    pairs = strkwargs.split(',')
    for pair in pairs:
        pair = pair.split('=')
        if len(pair)<2:
            key, value = pair[0], None
        else:
            key, value = tuple(pair[:2])
        kwargs[key] = value
        
    return kwargs
        
def dict_diff(d1, d2):
    '''
        take difference of two dictions, treating the value as integer. it
        will list all keys (union of keys) in a new dict with values as the
        difference between the first and the second dict values, skipping
        zeros and non-numbers.
    '''
    diff = {}
    keys = set(d1.keys()).union(set(d2.keys()))
    for key in keys:
        try:
            value = int(d1.get(key,0)) - int(d2.get(key,0))
        except (ValueError, TypeError):
            pass
        else:
            if value !=0:
                diff[key] = value
    
    return diff

def if_notebook():
    """ check if the current platform is a notebook or similar """
    import sys
    return 'ipykernel' in sys.modules

def if_ipython():
    """ check if the current platform is running IPython """
    import sys
    return 'IPython' in sys.modules

def if_docker():
    """ check if the current platform is a docker container """
    import os
    return os.path.exists('/.dockerenv') or os.path.exists('/.dockerinit')

def print_ansi_colour(msg, colour):
    """ print with ansi colour escape codes """
    colour_map = {"red":"31", "yellow":"33", "green":"32"}
    code = colour_map.get(colour, None)
    if code:
        msg = "\033["+code+";1m"+msg+"\033[0m"
        print(msg)
    else:
        print(msg)

def print_msg(msg, _type, platform):
    """ print with ansi colour escape codes based on platform """
    type_map = {"error":"red", "warn":"yellow", "info":"green"}
    fg = type_map.get(_type, None)
    
    if platform == Platform.NOTEBOOK:
        print_ansi_colour(msg, type_map.get(_type, None))
    else:
        click.secho(msg, fg=fg)