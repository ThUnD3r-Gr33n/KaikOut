#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from email.utils import parseaddr
import hashlib
from kaikout.database import Toml
from kaikout.log import Logger
import kaikout.sqlite as sqlite
import os
import sys
import tomli_w
from urllib.parse import urlsplit

try:
    import tomllib
except:
    import tomli as tomllib

logger = Logger(__name__)


class Config:


    def get_default_data_directory():
        """
        Determine the directory path where data will be stored.
    
        * If $XDG_DATA_HOME is defined, use it;
        * else if $HOME exists, use it;
        * else if the platform is Windows, use %APPDATA%;
        * else use the current directory.

        Returns
        -------
        str
            Path to data directory.
        """
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
    #    config_home = xdg.BaseDirectory.xdg_config_home
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
                config_home = os.path.join(
                    os.environ.get('HOME'), '.config'
                    )
        return os.path.join(config_home, 'kaikout')


    def get_setting_value(db_file, key):
        value = sqlite.get_setting_value(db_file, key)
        if value:
            value = value[0]
        else:
            value = Config.get_value('settings', 'Settings', key)
        return value


    def get_values(filename, key=None):
        config_dir = Config.get_default_config_directory()
        if not os.path.isdir(config_dir): config_dir = '/usr/share/kaikout/'
        if not os.path.isdir(config_dir): config_dir = os.path.dirname(__file__) + "/assets"
        config_file = os.path.join(config_dir, filename)
        with open(config_file, mode="rb") as f: result = tomllib.load(f)
        values = result[key] if key else result
        return values


class Documentation:


    def manual(filename, section=None, command=None):
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: filename: {}'.format(function_name, filename))
        config_dir = Config.get_default_config_directory()
        with open(config_dir + '/' + filename, mode="rb") as f: cmds = tomllib.load(f)
        if section == 'all':
            cmd_list = ''
            for cmd in cmds:
                for i in cmds[cmd]:
                    cmd_list += cmds[cmd][i] + '\n'
        elif command and section:
            try:
                cmd_list = cmds[section][command]
            except KeyError as e:
                logger.error(e)
                cmd_list = None
        elif section:
            try:
                cmd_list = []
                for cmd in cmds[section]:
                    cmd_list.extend([cmd])
            except KeyError as e:
                logger.error('KeyError:' + str(e))
                cmd_list = None
        else:
            cmd_list = []
            for cmd in cmds:
                cmd_list.extend([cmd])
        return cmd_list


class Log:


    def csv(filename, fields):
        """
        Log message to CSV file.

        Parameters
        ----------
        message : slixmpp.stanza.message.Message
            Message object.
    
        Returns
        -------
        None.
        """
        data_dir = Config.get_default_data_directory()
        if not os.path.isdir(data_dir): os.mkdir(data_dir)
        if not os.path.isdir(data_dir + "/logs"): os.mkdir(data_dir + "/logs")
        csv_file = os.path.join(data_dir, "logs", r"{}.csv".format(filename))
        if not os.path.exists(csv_file):
            columns = ['type', 'timestamp', 'alias', 'body', 'lang', 'identifier']
            with open(csv_file, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
        with open(csv_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(fields)


    def toml(self, room, fields, stanza_type):
        """
        Log message to TOML file.

        Parameters
        ----------
        room : str
            Group chat Jabber ID.
        fields : list
            alias, room, identifier, timestamp.
        stanza_type: str
            message or presence.
    
        Returns
        -------
        None.
        """
        alias, content, identifier, timestamp = fields
        data_dir = Toml.get_default_data_directory()
        filename = Toml.get_data_file(data_dir, room)
        # filename = room + '.toml'
        entry = {}
        entry['alias'] = alias
        entry['body'] = content
        entry['id'] = identifier
        entry['timestamp'] = timestamp
        activity_type = 'activity_' + stanza_type
        message_activity_list = self.settings[room][activity_type] if activity_type in self.settings[room] else []
        while len(message_activity_list) > 20: message_activity_list.pop(0)
        message_activity_list.append(entry)
        self.settings[room][activity_type] = message_activity_list # NOTE This directive might not be needed
        data = self.settings[room]
        content = tomli_w.dumps(data)
        with open(filename, 'w') as f: f.write(content)


class Url:


    def check_xmpp_uri(uri):
        """
        Check validity of XMPP URI.

        Parameters
        ----------
        uri : str
            URI.
    
        Returns
        -------
        jid : str
            JID or None.
        """
        jid = urlsplit(uri).path
        if parseaddr(jid)[1] != jid:
            jid = False
        return jid


class String:


    def md5_hash(url):
        """
        Hash URL string to MD5 checksum.

        Parameters
        ----------
        url : str
            URL.
    
        Returns
        -------
        url_digest : str
            Hashed URL as an MD5 checksum.
        """
        url_encoded = url.encode()
        url_hashed = hashlib.md5(url_encoded)
        url_digest = url_hashed.hexdigest()
        return url_digest
