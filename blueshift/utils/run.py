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
Created on Tue Nov 13 09:00:35 2018

@author: prodipta

does the background object building and defines run_algo.

"""
from os.path import basename
from os import _exit as os_exit
from sys import exit as sys_exit

from blueshift.algo import TradingAlgorithm, BlueShiftEnvironment, MODE
from blueshift.controls import register_env
from blueshift.alerts import get_alert_manager
from blueshift.utils.helpers import print_msg, if_notebook
from blueshift.utils.types import Platform

def run_algo(output, show_progress=False, publish=False, 
             *args, **kwargs):
    """ run algo from parameters """
    
    trading_environment = kwargs.pop("trading_environment", None)
    
    if not trading_environment:
        # try to create an environment from the parameters
        try:
            trading_environment = BlueShiftEnvironment(*args, **kwargs)
        except BaseException as e:
            print_msg(str(e), _type="error", 
                      platform=Platform.NOTEBOOK if if_notebook() else \
                      Platform.CONSOLE)
            
            sys_exit(1)
            os_exit(1)
            
    if not trading_environment:
        print_msg("failed to create a trading environment",
                  _type="error", 
                  platform=Platform.NOTEBOOK if if_notebook() else \
                  Platform.CONSOLE)
        sys_exit(1)
        os_exit(1)
        
    register_env(trading_environment)
    platform = trading_environment.platform
    
    alert_manager = get_alert_manager()
    broker = trading_environment.broker_tuple
    mode = trading_environment.mode
    algo_file = trading_environment.algo_file
    
    try:
        algo = TradingAlgorithm(
                name=trading_environment.name, broker=broker, 
                algo=algo_file, mode=mode)
    except BaseException as e:
        print_msg(str(e), _type="error", 
                  platform=Platform.NOTEBOOK if if_notebook() else \
                  Platform.CONSOLE)
        
        sys_exit(1)
        os_exit(1)
    
    broker_name = str(broker.broker._name)
    tz = broker.clock.trading_calendar.tz
    
    if mode == MODE.BACKTEST:
        '''
            print initial messages and run the algo object backtest.
        '''        
        length = len(broker.clock.session_nanos)
        print_msg(
                f"\nStarting backtest with {basename(algo_file)}", 
                _type="warn", platform=platform)
        
        msg = f"algo: {trading_environment.name}, broker:{broker_name}, timezone:{tz}, total sessions:{length}\n"
        print_msg(msg, _type="info2", platform=platform)
        perfs = algo.back_test_run(alert_manager, publish,
                                   show_progress)
        
        print_msg(
                f"backtest run complete", _type="info", platform=platform)
        
        if output:
            perfs.to_csv(output)
        
        return perfs
        
        
    elif mode == MODE.LIVE:
        '''
            For live run, there is no generator. We run the main 
            async event loop inside the Algorithm object itself.
            So all messaging has to be handled there. Here we just
            call the main function and leave it alone to complete.
        '''
        print_msg("\nstarting LIVE", _type="warn", platform=platform)
        msg = "starting LIVE, algo:"+ basename(algo_file) +\
                " with broker:" + broker_name + ", timezone:" + tz + "\n"
        print_msg(msg, _type="none", platform=platform)
        algo.live_run(alert_manager=alert_manager,
                      publish_packets=publish)
        
    else:
        '''
            Somehow we ended up with unknown mode.
        '''
        print_msg(
                f"illegal mode supplied.", _type="error", 
                platform=platform)
        sys_exit(1)
        os_exit(1)