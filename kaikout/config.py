#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kaikout.log import Logger
import os
import sys
try:
    import tomllib
except:
    import tomli as tomllib

logger = Logger(__name__)


class Config:


    def get_default_data_directory():
        if os.environ.get('HOME'):
            data_home = os.path.join(os.environ.get('HOME'), '.local', 'share')
            return os.path.join(data_home, 'kaikout')
        elif sys.platform == 'win32':
            data_home = os.environ.get('APPDATA')
            if data_home is None:
                return os.path.join(
                    os.path.dirname(__file__) + '/kaikout_data')
        else:
            return os.path.join(os.path.dirname(__file__) + '/kaikout_data')


    def get_default_config_directory():
        """
        Determine the directory path where configuration will be stored.
    
        * If $XDG_CONFIG_HOME is defined, use it;
        * else if $HOME exists, use it;
        * else if the platform is Windows, use %APPDATA%;
        * else use the current directory.

        Returns
        -------
        str
            Path to configuration directory.
        """
        # config_home = xdg.BaseDirectory.xdg_config_home
        config_home = os.environ.get('XDG_CONFIG_HOME')
        if config_home is None:
            if os.environ.get('HOME') is None:
                if sys.platform == 'win32':
                    config_home = os.environ.get('APPDATA')
                    if config_home is None:
                        return os.path.abspath('.')
                else:
                    return os.path.abspath('.')
            else:
                config_home = os.path.join(os.environ.get('HOME'), '.config')
        return os.path.join(config_home, 'kaikout')


    def get_values(filename, key=None):
        config_dir = Config.get_default_config_directory()
        if not os.path.isdir(config_dir):
            config_dir = '/usr/share/kaikout/'
        if not os.path.isdir(config_dir):
            config_dir = os.path.dirname(__file__) + "/assets"
        config_file = os.path.join(config_dir, filename)
        with open(config_file, mode="rb") as defaults:
            result = tomllib.load(defaults)
        values = result[key] if key else result
        return values
