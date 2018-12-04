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
Main entry point 
"""

import click
from sys import exit as sys_exit
from os import path as os_path
from os import environ as os_environ
from os import mkdir
import json

from blueshift.configs import generate_default_config
from blueshift.utils.types import (HashKeyType, 
                                   TimezoneType,
                                   DateType)
from blueshift.utils.run import BlueShiftEnvironment, run_algo
from blueshift.utils.general_helpers import list_to_args_kwargs
from blueshift.utils.exceptions import BlueShiftException

CONTEXT_SETTINGS = dict(ignore_unknown_options=True,
                        #allow_extra_args=True,
                        token_normalize_func=lambda x: x.lower())



@click.group()
@click.option(
    '--api-key', 
    '-a',
    envvar="BLUESHIFT_API_KEY",
    default=None,
    type=HashKeyType(length=16),
    help='your Blueshift API key. Visit the site to generate one.'
)
@click.option(
    '--config-file', 
    '-c',
    envvar="BLUESHIFT_CONFIG_FILE",
    default='~/.blueshift/.blueshift_config.json',
    type=click.Path(),
    help='Blueshift config file. You can generate a config template'
            'using the `config` command.'
)
@click.pass_context
def main(ctx, api_key, config_file):
    '''
        Blueshift is a stand-alone as well as API connected complete
        trading system. It supports multiple assets across multiple 
        markets - both for back-testing and live trading and research.
        
        Usage:\n
            blueshift config > ~/blushift_config.json\n
            blueshift run --mode backtest [--data-frequency 5m --initial-capital 1000] --algo-file 'myalgo.py'\n
            blueshift query [--api-key your-blueshift-api-key] --algo your-unique-backtest-or-livetrade-ID --command query-command\n
            blueshift --help
    '''
    ctx.obj = {'config':config_file,
               'api_key': api_key
               }

@main.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--root',
    default='~/.blueshift',
    type=click.Path(file_okay=False, writable=True),
    help='your local Blueshift root directory.',
    )
@click.option(
    '--timezone',
    default='Etc/UTC',
    type=TimezoneType(),
    help='your default timezone.',
    )
@click.option(
    '--broker',
    default=None,
    type=click.STRING,
    help='name of the broker. For a list of accepted brokers see the website.',
    )
@click.option(
    '--broker_id',
    default=None,
    type=click.STRING,
    help='your user ID with this broker, if any.',
    )
@click.option(
    '--broker-key',
    default=None,
    type=HashKeyType(length=16),
    help='any API key provided by your broker.',
    )
@click.option(
    '--broker-secret',
    default=None,
    type=HashKeyType(),
    help='any API secret key provided by your broker.',
    )
@click.pass_context
def config(ctx, root, timezone, broker, broker_id, broker_key, 
           broker_secret):
    '''
        Create a template for Blueshift configuration file with
        the given inputs.
    '''
    try:
        # get the base template
        config = json.loads(generate_default_config())
        
        # update the dict with supplied parameters.
        root = os_path.expanduser(root)
        config['owner'] = os_environ.get('USERNAME')
        config['api_key'] = ctx.obj.get('api_key', None)
        config['user_workspace']['root'] = root
        
        # create all directories in root if they do not exists already
        for d in config['user_workspace']:
            if d=='root':
                if not os_path.exists(root): mkdir(root)
            else:
                full_path = os_path.join(root, 
                                         config['user_workspace'][d])
                if not os_path.exists(full_path): mkdir(full_path)
        
        click.echo(json.dumps(config))
    except BlueShiftException as e:
        click.secho(str(e), fg="red")
        sys_exit(1)
    

@main.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '-s',
    '--start-date',
    default=None,
    type=DateType(),
    help='start date for backtest. Will be ignored for live mode.',
    )
@click.option(
    '-e',
    '--end-date',
    default=None,
    type=DateType(),
    help='end date for backtest. Will be ignored for live mode.',
    )
@click.option(
    '-c',
    '--initial-capital',
    default=10000,
    type=click.FLOAT,
    help='Initial capital for backtest.'\
            ' Will be ignored for live mode.',
    )
@click.option(
    '-a',
    '--algo-file',
    default=None,
    type=click.Path(file_okay=True, writable=True),
    help='Algo script file or module path.',
    )
@click.option(
    '-m',
    '--run-mode',
    default='backtest',
    type=click.Choice(['backtest', 'live']),
    help='Run mode [backtest, live].',
    )
@click.option(
    '--broker',
    default=None,
    type=click.STRING,
    help='Choose the broker to run this strategy.',
    )
@click.option(
    '--name',
    default='myalgo',
    help='Name of this run',
    )
@click.option(
    '--platform',
    default='blueshift',
    type=click.Choice(['blueshift', 'api', 'stand-alone']),
    help='Platform type. [blueshift, api, stand-alone]',
    )
@click.option(
    '--output',
    default=None,
    type=click.Path(file_okay=True, writable=True),
    help='Output file to write to',
    )
@click.option(
    '--show-progress/--no-progress',
    default=False,
    help='Turn on/ off the progress bar. [show-progress/no-progress')
@click.option(
    '--publish/--no-publish',
    default=False,
    help='Turn on/ off streaming results. [publish/no-publish')
@click.argument('arglist', nargs=-1, type=click.STRING)
@click.pass_context
def run(ctx, start_date, end_date, initial_capital, 
        algo_file, run_mode, broker, name, platform, output, show_progress, 
        publish, arglist):
    '''
        Set up the context and trigger the run.
    '''
    try:
        args, kwargs = list_to_args_kwargs(arglist)
        
        configfile = os_path.expanduser(ctx.obj['config'])
        algo_file = algo_file
        trading_environment = BlueShiftEnvironment()
        trading_environment.create_environment(config_file=configfile,
                                               algo_file=algo_file,
                                               start_date=start_date,
                                               end_date=end_date,
                                               initial_capital=\
                                                   initial_capital,
                                               mode=run_mode,
                                               broker=broker,
                                               *args,**kwargs)
        
        run_algo(name, output, show_progress, publish,
                 trading_environment=trading_environment, 
                 *args, **kwargs)
    except BlueShiftException as e:
        click.secho(str(e), fg="red")
        sys_exit(1)


if __name__ == "__main__":
    main()