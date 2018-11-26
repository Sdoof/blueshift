# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 11:25:53 2018

@author: academy
"""
import json

from .config import BlueShiftConfig, register_config, get_config
from .defaults import (blueshift_root, blueshift_log_path,
                       blueshift_data_path, blueshift_source_path,
                       blueshift_save_perfs_path,
                       blueshift_saved_objs_path,
                       blueshift_saved_orders_path,
                       _default_config, ensure_directory,
                       get_config_alerts, get_config_tz,
                       get_config_recovery, get_config_name,
                       get_config_channel,
                       get_config_calendar_details,
                       get_config_backtest_details,
                       get_config_livetrade_details,
                       get_config_env_vars,
                       blueshit_run_set_name,
                       blueshift_run_get_name)


def generate_default_config(filename=None):
    if not filename:
        return json.dumps(_default_config)
        
    with open(filename,"w") as fp:
        json.dump(_default_config,fp)
    



__all__ = [generate_default_config,
           register_config,
           get_config,
           BlueShiftConfig,
           blueshift_root,
           blueshift_log_path,
           blueshift_data_path,
           blueshift_source_path,
           blueshift_save_perfs_path,
           blueshift_saved_objs_path,
           blueshift_saved_orders_path,
           get_config_alerts,
           get_config_tz,
           get_config_recovery,
           get_config_name,
           get_config_channel,
           get_config_calendar_details,
           get_config_backtest_details,
           get_config_livetrade_details,
           get_config_env_vars,
           blueshit_run_set_name,
           blueshift_run_get_name,
           ensure_directory]
