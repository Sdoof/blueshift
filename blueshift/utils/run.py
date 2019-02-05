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
import click

from blueshift.algo import TradingAlgorithm, BlueShiftEnvironment, MODE
from blueshift.controls import register_env
from blueshift.alerts import get_alert_manager


def run_algo(output, show_progress=False, publish=False, 
             *args, **kwargs):
    
    run_algo_cli(output, show_progress, publish, *args, **kwargs)
    


def run_algo_cli(output, show_progress=False, publish=False, 
             *args, **kwargs):
    """ run algo from parameters for console """
    
    trading_environment = kwargs.pop("trading_environment", None)
    
    if not trading_environment:
        # try to create an environment from the parameters
        trading_environment = BlueShiftEnvironment(*args, **kwargs)
    
    if not trading_environment:
        click.secho("failed to create a trading environment", fg="red")
        sys_exit(1)
        os_exit(1)
        
    register_env(trading_environment)
    
    alert_manager = get_alert_manager()
    broker = trading_environment.broker_tuple
    mode = trading_environment.mode
    algo_file = trading_environment.algo_file
    algo = TradingAlgorithm(
            name=trading_environment.name, broker=broker, algo=algo_file, 
            mode=mode)
    
    broker_name = str(broker.broker._name)
    tz = broker.clock.trading_calendar.tz
    
    if mode == MODE.BACKTEST:
        '''
            print initial messages and run the algo object backtest.
        '''        
        length = len(broker.clock.session_nanos)
        click.secho(f"\nStarting backtest with {basename(algo_file)}", 
                                              fg="yellow")
        msg = f"algo: {trading_environment.name}, broker:{broker_name}, timezone:{tz}, total sessions:{length}\n"
        click.echo(msg)
        perfs = algo.back_test_run(alert_manager, publish,
                                   show_progress)
        
        click.secho(f"backtest run complete", fg="green")
        
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
        click.secho("\nstarting LIVE", fg="yellow")
        msg = "starting LIVE, algo:"+ basename(algo_file) +\
                " with broker:" + broker_name + ", timezone:" + tz + "\n"
        click.echo(msg)
        algo.live_run(alert_manager=alert_manager,
                      publish_packets=publish)
        
    else:
        '''
            Somehow we ended up with unknown mode.
        '''
        click.secho(f"illegal mode supplied.", fg="red")
        sys_exit(1)
        os_exit(1)