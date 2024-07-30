#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import kaikout.config as config
from kaikout.config import Config
from kaikout.log import Logger
from kaikout.database import Toml
from kaikout.utilities import Documentation, Url
from kaikout.version import __version__
from kaikout.xmpp.bookmark import XmppBookmark
from kaikout.xmpp.muc import XmppMuc
from kaikout.xmpp.status import XmppStatus
from kaikout.xmpp.utilities import XmppUtilities
from slixmpp.exceptions import IqError, IqTimeout
import sys
import time

try:
    import tomllib
except:
    import tomli as tomllib

logger = Logger(__name__)


    # for task in main_task:
    #     task.cancel()

    # Deprecated in favour of event "presence_available"
    # if not main_task:
    #     await select_file()

class XmppCommands:


    async def clear_filter(self, room, db_file, key):
        value = []
        self.settings[room][key] = value
        Toml.update_jid_settings(self, room, db_file, key, value)
        message = 'Filter {} has been purged.'.format(key)
        return message


    async def devoice(self, room, alias, reason):
        status_message = '🚫 Committing an action (devoice) against participant {}'.format(alias)
        self.action_count += 1
        task_number = self.action_count
        if room not in self.actions: self.actions[room] = {}
        self.actions[room][task_number] = status_message
        XmppStatus.send_status_message(self, room)
        jid_full = XmppMuc.get_full_jid(self, room, alias)
        if jid_full:
            jid_bare = jid_full.split('/')[0]
            await XmppMuc.set_role(self, room, alias, 'visitor', reason)
        await asyncio.sleep(5)
        del self.actions[room][task_number]
        XmppStatus.send_status_message(self, room)
        return jid_bare


    async def countdown(self, time, room, alias, reason):
        while time > 1:
            time -= 1
            print([time, room, alias], end='\r')
            await asyncio.sleep(1)
        await XmppCommands.devoice(self, room, alias, reason)
        


    def fetch_gemini():
        message = 'Gemini and Gopher are not supported yet.'
        return message


    def get_interval(self, jid_bare):
        result = Config.get_setting_value(
            self.settings, jid_bare, 'interval')
        message = str(result)
        return message


    async def bookmark_add(self, muc_jid):
        await XmppBookmark.add(self, jid=muc_jid)
        message = ('Groupchat {} has been added to bookmarks.'
                   .format(muc_jid))
        return message


    async def bookmark_del(self, muc_jid):
        await XmppBookmark.remove(self, muc_jid)
        message = ('Groupchat {} has been removed from bookmarks.'
                   .format(muc_jid))
        return message
        
    async def invite_jid_to_muc(self, jid_bare):
        muc_jid = 'slixfeed@chat.woodpeckersnest.space'
        if await XmppUtilities.get_chat_type(self, jid_bare) == 'chat':
            self.plugin['xep_0045'].invite(muc_jid, jid_bare)


    async def kick(self, room, alias, reason):
        status_message = '🚫 Committing an action (kick) against participant {}'.format(alias)
        self.action_count += 1
        task_number = self.action_count
        if room not in self.actions: self.actions[room] = {}
        self.actions[room][task_number] = status_message
        XmppStatus.send_status_message(self, room)
        jid_full = XmppMuc.get_full_jid(self, room, alias)
        if jid_full:
            jid_bare = jid_full.split('/')[0]
            await XmppMuc.set_affiliation(self, room, 'none', jid_bare, reason)
        await asyncio.sleep(5)
        del self.actions[room][task_number]
        XmppStatus.send_status_message(self, room)
        return jid_bare


    async def muc_join(self, command):
        if command:
            muc_jid = Url.check_xmpp_uri(command)
            if muc_jid:
                # TODO probe JID and confirm it's a groupchat
                result = await XmppMuc.join(self, muc_jid)
                # await XmppBookmark.add(self, jid=muc_jid)
                if result == 'ban':
                    message = '{} is banned from {}'.format(self.alias, muc_jid)
                else:
                    await XmppBookmark.add(self, muc_jid)
                    message = 'Joined groupchat {}'.format(muc_jid)
            else:
                message = '> {}\nGroupchat JID appears to be invalid.'.format(muc_jid)
        else:
            message = '> {}\nGroupchat JID is missing.'
        return message


    async def muc_leave(self, room):
        XmppMuc.leave(self, room)
        await XmppBookmark.remove(self, room)


    async def outcast(self, room, alias, reason):
        status_message = '🚫 Committing an action (ban) against participant {}'.format(alias)
        self.action_count += 1
        task_number = self.action_count
        if room not in self.actions: self.actions[room] = {}
        self.actions[room][task_number] = status_message
        XmppStatus.send_status_message(self, room)
        jid_full = XmppMuc.get_full_jid(self, room, alias)
        if jid_full:
            jid_bare = jid_full.split('/')[0]
            await XmppMuc.set_affiliation(self, room, 'outcast', jid_bare, reason)
        # else:
        #     # Could "alias" ever be relevant?
        #     # Being a moderator is essential to be able to outcast.
        #     # JIDs are visible to moderators.
        #     await XmppMuc.set_affiliation(self, room, 'outcast', alias, reason)
        await asyncio.sleep(5)
        del self.actions[room][task_number]
        XmppStatus.send_status_message(self, room)
        return jid_bare


    async def print_bookmarks(self):
        conferences = await XmppBookmark.get_bookmarks(self)
        message = '\nList of groupchats:\n\n```\n'
        for conference in conferences:
            message += ('Name: {}\n'
                        'Room: {}\n'
                        '\n'
                        .format(conference['name'], conference['jid']))
        message += ('```\nTotal of {} groupchats.\n'.format(len(conferences)))
        return message


    def print_help():
        result = Documentation.manual('commands.toml')
        message = '\n'.join(result)
        return message


    def print_help_list():
        command_list = Documentation.manual('commands.toml', section='all')
        message = ('Complete list of commands:\n'
                   '```\n{}\n```'.format(command_list))
        return message


    def print_help_specific(command_root, command_name):
        command_list = Documentation.manual('commands.toml',
                                     section=command_root,
                                     command=command_name)
        if command_list:
            command_list = ''.join(command_list)
            message = (command_list)
        else:
            message = 'KeyError for {} {}'.format(command_root, command_name)
        return message


    def print_help_key(command):
        command_list = Documentation.manual('commands.toml', command)
        if command_list:
            command_list = ' '.join(command_list)
            message = ('Available command `{}` keys:\n'
                       '```\n{}\n```\n'
                       'Usage: `help {} <command>`'
                       .format(command, command_list, command))
        else:
            message = 'KeyError for {}'.format(command)
        return message


    def print_info_list():
        config_dir = config.get_default_config_directory()
        with open(config_dir + '/' + 'information.toml', mode="rb") as information:
            result = tomllib.load(information)
        message = '\n'.join(result)
        return message


    def print_info_specific(entry):
        config_dir = config.get_default_config_directory()
        with open(config_dir + '/' + 'information.toml', mode="rb") as information:
            entries = tomllib.load(information)
        if entry in entries:
            # command_list = '\n'.join(command_list)
            message = (entries[entry]['info'])
        else:
            message = 'KeyError for {}'.format(entry)
        return message


    def print_options(self, room):
        message = ''
        for key in self.settings[room]:
            val = self.settings[room][key]
            steps = 18 - len(key)
            pulse = ''
            for step in range(steps):
                pulse += ' '
            message += '\n' + key + pulse + ' = ' + str(val)
        return message


    # """You have {} unread news items out of {} from {} news sources.
    # """.format(unread_entries, entries, feeds)
    def print_statistics(db_file):
        """
        Print statistics.

        Parameters
        ----------
        db_file : str
            Path to database file.

        Returns
        -------
        msg : str
            Statistics as message.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {}'
                    .format(function_name, db_file))
        entries_unread = sqlite.get_number_of_entries_unread(db_file)
        entries = sqlite.get_number_of_items(db_file, 'entries_properties')
        feeds_active = sqlite.get_number_of_feeds_active(db_file)
        feeds_all = sqlite.get_number_of_items(db_file, 'feeds_properties')
        message = ("Statistics:"
                   "\n"
                   "```"
                   "\n"
                   "News items   : {}/{}\n"
                   "News sources : {}/{}\n"
                   "```").format(entries_unread,
                                 entries,
                                 feeds_active,
                                 feeds_all)
        return message


    def print_support_jid():
        muc_jid = 'slixfeed@chat.woodpeckersnest.space'
        message = 'Join xmpp:{}?join'.format(muc_jid)
        return message


    def print_unknown():
        message = 'An unknown command.  Type "help" for a list of commands.'
        return message


    def print_version():
        message = __version__
        return message


    def raise_score(self, room, alias, db_file, reason):
        """
        Raise score by one.

        Parameters
        ----------
        room : str
            Jabber ID.
        alias : str
            Alias.
        db_file : str
            Database filename.
        reason : str
            Reason.

        Returns
        -------
        result.

        """
        status_message = '✒️ Writing a score against {} for {}'.format(alias, reason)
        self.action_count += 1
        task_number = self.action_count
        if room not in self.actions: self.actions[room] = {}
        self.actions[room][task_number] = status_message
        XmppStatus.send_status_message(self, room)
        scores = self.settings[room]['scores'] if 'scores' in self.settings[room] else {}
        jid_full = XmppMuc.get_full_jid(self, room, alias)
        if jid_full:
            jid_bare = jid_full.split('/')[0]
            scores[jid_bare] = scores[jid_bare] + 1 if jid_bare in scores else 1
            Toml.update_jid_settings(self, room, db_file, 'scores', scores)
        time.sleep(5)
        del self.actions[room][task_number]
        XmppStatus.send_status_message(self, room)
        result = scores[jid_bare] if jid_full and jid_bare else 0
        return result


    def update_score_ban(self, room, jid_bare, db_file):
        """
        Update ban score.

        Parameters
        ----------
        room : str
            Jabber ID.
        jid_bare : str
            Jabber ID.
        db_file : str
            Database filename.

        Returns
        -------
        result.

        """
        scores = self.settings[room]['score_ban'] if 'score_ban' in self.settings[room] else {}
        scores[jid_bare] = scores[jid_bare] + 1 if jid_bare in scores else 1
        Toml.update_jid_settings(self, room, db_file, 'score_ban', scores)
        # result = scores[jid_bare]
        # return result


    def update_score_kick(self, room, jid_bare, db_file):
        """
        Update kick score.

        Parameters
        ----------
        room : str
            Jabber ID.
        jid_bare : str
            Jabber ID.
        db_file : str
            Database filename.

        Returns
        -------
        result.

        """
        scores = self.settings[room]['score_kick'] if 'score_kick' in self.settings[room] else {}
        scores[jid_bare] = scores[jid_bare] + 1 if jid_bare in scores else 1
        Toml.update_jid_settings(self, room, db_file, 'score_kick', scores)
        # result = scores[jid_bare]
        # return result


    def update_last_activity(self, room, jid_bare, db_file, timestamp):
        """
        Update last message activity.

        Parameters
        ----------
        room : str
            Jabber ID.
        db_file : str
            Database filename.
        jid_bare : str
            Jabber ID.
        timestamp : 
            Time stamp.

        Returns
        -------
        result.

        """
        activity = self.settings[room]['last_activity'] if 'last_activity' in self.settings[room] else {}
        activity[jid_bare] = timestamp
        Toml.update_jid_settings(self, room, db_file, 'last_activity', activity)


    async def restore_default(self, room, db_file, key=None):
        if key:
            value = self.defaults[key]
            self.settings[room][key] = value
            # data_dir = Toml.get_default_data_directory()
            # db_file = Toml.get_data_file(data_dir, jid_bare)
            Toml.update_jid_settings(self, room, db_file, key, value)
            message = ('Setting {} has been restored to default value.'
                        .format(key))
        else:
            self.settings = self.defaults
            data_dir = Toml.get_default_data_directory()
            db_file = Toml.get_data_file(data_dir, room)
            Toml.create_settings_file(self, db_file)
            message = 'Default settings have been restored.'
        return message


    def set_filter(self, room, db_file, keywords, filter, axis):
        """

        Parameters
        ----------
        db_file : str
            Database filename.
        keywords : str
            keyword (word or phrase).
        filter : str
            'allow' or 'deny'.
        axis : boolean
            True for + (plus) and False for - (minus).

        Returns
        -------
        None.

        """
        keyword_list = self.settings[room][filter] if filter in self.settings[room] else []
        new_keywords = keywords.split(',')
        processed_keywords = []
        if axis:
            action = 'added'
            for keyword in new_keywords:
                if keyword and keyword not in keyword_list:
                    keyword_trim = keyword.strip()
                    keyword_list.append(keyword_trim)
                    processed_keywords.append(keyword_trim)
        else:
            action = 'removed'
            for keyword in new_keywords:
                if keyword and keyword in keyword_list:
                    keyword_trim = keyword.strip()
                    keyword_list.remove(keyword_trim)
                    processed_keywords.append(keyword_trim)
        Toml.update_jid_settings(self, room, db_file, filter, keyword_list)
        processed_keywords.sort()
        message = 'Keywords "{}" have been {} to list "{}".'.format(
            ', '.join(processed_keywords), action, filter)
        return message


    async def set_interval(self, db_file, jid_bare, val):
        try:
            val_new = int(val)
            val_old = Config.get_setting_value(
                self.settings, jid_bare, 'interval')
            await Config.set_setting_value(
                self.settings, jid_bare, db_file, 'interval', val_new)
            message = ('Updates will be sent every {} minutes '
                       '(was: {}).'.format(val_new, val_old))
        except Exception as e:
            logger.error(str(e))
            message = ('No action has been taken.  Enter a numeric value only.')
        return message


    def update_setting_value(self, room, db_file, key, value):
        Toml.update_jid_settings(self, room, db_file, key, value)
