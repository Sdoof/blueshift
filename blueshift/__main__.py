# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 14:40:36 2018

@author: prodipta
"""
import click
from os import path as os_path
from os import environ as os_environ
from os import mkdir
import json

import sys
blueshift_path = 'C:/Users/academy.academy-72/Desktop/dev platform/blueshift'
if blueshift_path not in sys.path:
    sys.path.append(blueshift_path)

from blueshift.configs import generate_default_config
from blueshift.utils.types import (HashKeyType, 
                                   TimezoneType,
                                   DateType)
from blueshift.utils.start_up import create_environment

@click.group()
@click.option(
    '--api-key', 
    '-a',
    default=None,
    type=HashKeyType(),
    help='your Blueshift API key. Visit the site to generate one.'
)
@click.option(
    '--config-file', 
    '-c',
    default='~/.blueshift_config.json',
    type=click.Path(),
    help='path to Blueshift config file. You can generate a template'
            'using the `config` command.'
)
@click.pass_context
def main(ctx, api_key, config_file):
    '''
        Blueshift is a stand-alone as well as API connected complete
        trading system. It supports multiple assets across multiple 
        markets - both for back-testing and live trading and research.
        
        Usage:
            blueshift config > ~/blushift_config.json
            blueshift run --mode backtest [--data-frequency 5m --initial-capital 1000] --algo-file 'myalgo.py'
            blueshift query [--api-key your-blueshift-api-key] --algo your-unique-backtest-or-livetrade-ID --command query-command
            blueshift --help
    '''
    ctx.obj = {'config':config_file,
               'api_key': api_key
               }

@main.command()
@click.option(
    '--root',
    default='~/.blueshift',
    type=click.Path(file_okay=False, writable=True),
    help='your local Blueshift root directory.',
    )
@click.option(
    '-tz',
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
    # get the base template
    config = json.loads(generate_default_config())
    
    # update the dict with supplied parameters.
    root = os_path.expanduser(root)
    config['owner'] = os_environ.get('USERNAME')
    config['api_key'] = ctx.obj.get('api_key', None)
    config['user_workspace']['root'] = root
    config['live_broker']['broker_name'] = broker
    config['live_broker']['api_key'] = broker_key
    config['live_broker']['api_secret'] = broker_secret
    config['live_broker']['broker_id'] = broker_id
    config['calendar']['tz'] = timezone
    
    # create all directories in root if they do not exists already
    for d in config['user_workspace']:
        if d=='root':
            if not os_path.exists(root): mkdir(root)
        else:
            full_path = os_path.join(root, 
                                     config['user_workspace'][d])
            if not os_path.exists(full_path): mkdir(full_path)
    
    print(json.dumps(config))
    

@main.command()
@click.option(
    '-start',
    '--start-date',
    default=None,
    type=DateType(),
    help='start date for backtest. Will be ignored for live mode',
    )
@click.option(
    '-end',
    '--end-date',
    default=None,
    type=DateType(),
    help='end date for backtest. Will be ignored for live mode',
    )
@click.option(
    '-algo',
    '--algo-file',
    default=None,
    type=click.Path(file_okay=False, writable=True),
    help='Algo script file or module path.',
    )
@click.pass_context
def run(ctx):
    pass

if __name__ == "__main__":
    main()