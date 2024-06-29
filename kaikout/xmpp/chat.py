#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from slixmpp import JID
from kaikout.database import Toml
from kaikout.log import Logger
from kaikout.utilities import Documentation
from kaikout.xmpp.commands import XmppCommands
from kaikout.xmpp.message import XmppMessage
from kaikout.xmpp.muc import XmppMuc
from kaikout.xmpp.status import XmppStatus
from kaikout.xmpp.utilities import XmppUtilities
import time


logger = Logger(__name__)


    # for task in main_task:
    #     task.cancel()

    # Deprecated in favour of event "presence_available"
    # if not main_task:
    #     await select_file()


class XmppChat:


    async def process_message(self, message):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good practice to check the messages's type before
        processing or sending replies.

        Parameters
        ----------
        message : str
            The received message stanza. See the documentation
            for stanza objects and the Message stanza to see
            how it may be used.
        """
        # jid_bare = message['from'].bare
        # jid_full = str(message['from'])

        # Process commands.
        message_type = message['type']
        message_body = message['body']
        if message_type == 'groupchat':
            alias = message['mucnick']
            room = message['mucroom']
            if (message['mucnick'] == self.alias or
                not XmppUtilities.is_moderator(self, room, alias) or
                not message_body.startswith('%')):
                return
        elif message_type in ('chat', 'normal'):
            jid = message['from']
            jid_bare = jid.bare
            jid_full = jid.full
            room = self.sessions[jid_bare] if jid_bare in self.sessions else message_body
            status_mode,status_text, message_response = None, None, None
            if '@' in room:
                if room in XmppMuc.get_joined_rooms(self):
                    alias = await XmppUtilities.is_jid_of_moderators(
                        self, room, jid_full)
                    if jid_bare not in self.sessions:
                        if alias:
                        # alias = XmppMuc.get_alias(self, room, jid)
                        # if XmppUtilities.is_moderator(self, room, alias):
                            self.sessions[jid_bare] = room
                            message_response = (
                                'A session to configure groupchat {} has been '
                                'established.'.format(room))
                            status_mode = 'chat'
                            status_text = 'Session is opened: {}'.format(room)
                            owners = await XmppMuc.get_affiliation(self, room,
                                                                   'owner')
                            for owner in owners:
                                message_notification = (
                                    'A session for groupchat {} has been '
                                    'activated by moderator {}'
                                    .format(room, jid_bare))
                                XmppMessage.send(
                                    self, owner, message_notification, 'chat')
                        else:
                            message_response = (
                                'You do not appear to be a moderator of '
                                'groupchat {}'.format(room))
                            status_mode = 'available'
                            status_text = (
                                'Type the desired groupchat - in which you '
                                'are a moderator at - to configure')
                            moderators = await XmppMuc.get_role(
                                self, room, 'moderator')
                            message_notification = (
                                'An unauthorized attempt to establish a '
                                'session for groupchat {} has been made by {}'
                                .format(room, jid_bare))
                            for moderator in moderators:
                                jid_full = XmppMuc.get_full_jid(self, room,
                                                                moderator)
                                XmppMessage.send(
                                    self, jid_full, message_notification, 'chat')
                    elif not alias:
                        del self.sessions[jid_bare]
                        message_response = (
                            'The session has been ended, because you are no '
                            'longer a moderator at groupchat {}'.format(room))
                        status_mode = 'away'
                        status_text = 'Session is closed: {}'.format(room)
                        moderators = await XmppMuc.get_role(
                            self, room, 'moderator')
                        message_notification = (
                            'The session for groupchat {} with former '
                            'moderator {} has been terminated.\n'
                            'A termination message has been sent to {}'
                            .format(room, jid_bare, jid_bare))
                        for moderator in moderators:
                            jid_full = XmppMuc.get_full_jid(self, room,
                                                            moderator)
                            XmppMessage.send(
                                self, jid_full, message_notification, 'chat')
                    else:
                        room = self.sessions[jid_bare]
                else:
                    message_response = (
                        'Invite KaikOut to groupchat "{}" and try again.\n'
                        'A session will not begin if KaikOut is not present '
                        'in groupchat.'.format(room))
            else:
                message_response = ('The text "{}" does not appear to be a '
                                    'valid groupchat Jabber ID.'.format(room))
            if status_mode and status_text:
                XmppStatus.send_status_message(self, jid_full, status_mode,
                                               status_text)
            if message_response:
                XmppMessage.send_reply(self, message, message_response)
                return
        else:
            return

        db_file = Toml.instantiate(self, room)

        # # Support private message via groupchat
        # # See https://codeberg.org/poezio/slixmpp/issues/3506
        # if message_type == 'chat' and message.get_plugin('muc', check=True):
        #     # jid_bare = message['from'].bare
        #     if (jid_bare == jid_full[:jid_full.index('/')]):
        #         # TODO Count and alert of MUC-PM attempts
        #         return

        command_time_start = time.time()

        command = message_body[1:] if message_type == 'groupchat' else message_body
        command_lowercase = command.lower()

        # if not self.settings[room]['enabled']:
        #     if not command_lowercase.startswith('start'):
        #         return

        response = None
        match command_lowercase:
            case 'help':
                command_list = XmppCommands.print_help()
                response = ('Available command keys:\n'
                            '```\n{}\n```\n'
                            'Usage: `help <key>`'
                            .format(command_list))
            case 'help all':
                command_list = Documentation.manual('commands.toml',
                                                    section='all')
                response = ('Complete list of commands:\n'
                            '```\n{}\n```'
                            .format(command_list))
            case _ if command_lowercase.startswith('help'):
                command = command[5:].lower()
                command = command.split(' ')
                if len(command) == 2:
                    command_root = command[0]
                    command_name = command[1]
                    command_list = Documentation.manual(
                        'commands.toml', section=command_root,
                        command=command_name)
                    if command_list:
                        command_list = ''.join(command_list)
                        response = (command_list)
                    else:
                        response = ('KeyError for {} {}'
                                    .format(command_root, command_name))
                elif len(command) == 1:
                    command = command[0]
                    command_list = Documentation.manual('commands.toml',
                                                        command)
                    if command_list:
                        command_list = ' '.join(command_list)
                        response = ('Available command `{}` keys:\n'
                                    '```\n{}\n```\n'
                                    'Usage: `help {} <command>`'
                                    .format(command, command_list, command))
                    else:
                        response = 'KeyError for {}'.format(command)
                else:
                    response = ('Invalid. Enter command key '
                                'or command key & name')
            case 'info':
                entries = XmppCommands.print_info_list()
                response = ('Available command options:\n'
                            '```\n{}\n```\n'
                            'Usage: `info <option>`'
                            .format(entries))
            case _ if command_lowercase.startswith('info'):
                entry = command[5:].lower()
                response = XmppCommands.print_info_specific(entry)
            case _ if command_lowercase.startswith('action'):
                value = command[6:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'action', value)
                        atype = 'ban' if value else 'devoice'
                        response = 'Action has been set to {} ({})'.format(
                            atype, value)
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['action'])
            case _ if command_lowercase.startswith('allow +'):
                value = command[7:]
                if value:
                    response = XmppCommands.set_filter(
                        self, room, db_file, value, 'allow', True)
                else:
                    response = ('No action has been taken.  '
                                'Missing keywords.')
            case _ if command_lowercase.startswith('allow -'):
                value = command[7:]
                if value:
                    response = XmppCommands.set_filter(
                        self, room, db_file, value, 'allow', False)
                else:
                    response = ('No action has been taken.  '
                                'Missing keywords.')
            case _ if command_lowercase.startswith('ban'):
                if command[4:]:
                    value = command[4:].split()
                    alias = value[0]
                    reason = ' '.join(value[1:]) if len(value) > 1 else None
                    await XmppCommands.outcast(self, room, alias, reason)
            case _ if command_lowercase.startswith('bookmark +'):
                if XmppUtilities.is_operator(self, jid_bare):
                    muc_jid = command[11:]
                    response = await XmppCommands.bookmark_add(
                        self, muc_jid)
                else:
                    response = ('This action is restricted. '
                                'Type: adding bookmarks.')
            case _ if command_lowercase.startswith('bookmark -'):
                if XmppUtilities.is_operator(self, jid_bare):
                    muc_jid = command[11:]
                    response = await XmppCommands.bookmark_del(
                        self, muc_jid)
                else:
                    response = ('This action is restricted. '
                                'Type: removing bookmarks.')
            case 'bookmarks':
                if XmppUtilities.is_operator(self, jid_bare):
                    response = await XmppCommands.print_bookmarks(self)
                else:
                    response = ('This action is restricted. '
                                'Type: viewing bookmarks.')
            case _ if command_lowercase.startswith('clear'):
                key = command[6:]
                response = await XmppCommands.clear_filter(self, room, db_file,
                                                           key)
            case _ if command_lowercase.startswith('count'):
                value = command[5:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'count', value)
                        response = 'Count has been set to {}'.format(value)
                    except:
                        response = ('No action has been taken.  '
                                    'Enter a numerical value.')
                else:
                    response = str(self.settings[room]['count'])
            case _ if command_lowercase.startswith('default'):
                key = command[8:]
                if key:
                    response = await XmppCommands.restore_default(
                        self, room, db_file, key)
                else:
                    response = ('No action has been taken.  '
                                'Missing key.')
            case 'defaults':
                response = await XmppCommands.restore_default(self, room,
                                                              db_file)
            case _ if command_lowercase.startswith('deny +'):
                value = command[6:].strip()
                if value:
                    response = XmppCommands.set_filter(
                        self, room, db_file, value, 'deny', True)
                else:
                    response = ('No action has been taken.  '
                                'Missing keywords.')
            case _ if command_lowercase.startswith('deny -'):
                value = command[6:].strip()
                if value:
                    response = XmppCommands.set_filter(
                        self, room, db_file, value, 'deny', False)
                else:
                    response = ('No action has been taken.  '
                                'Missing keywords.')
            case 'finished off':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'finished', 0)
                response = 'Finished indicator has deactivated.'
            case 'finished on':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'finished', 1)
                response = 'Finished indicator has activated.'
            case _ if command_lowercase.startswith('frequency messages'):
                value = command[18:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'frequency_messages', value)
                        response = ('Minimum allowed frequency for messages '
                                    'has been set to {}'.format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['frequency_messages'])
            case _ if command_lowercase.startswith('frequency presence'):
                value = command[18:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'frequency_presence', value)
                        response = ('Minimum allowed frequency for presence '
                                    'has been set to {}'.format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['frequency_presence'])
            case 'goodbye':
                if message_type == 'groupchat':
                    await XmppCommands.muc_leave(self, room)
                else:
                    response = 'This command is valid in groupchat only.'
            case 'inactivity off':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'check_inactivity', 0)
                response = 'Inactivity check has been deactivated.'
            case 'inactivity on':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'check_inactivity', 1)
                response = 'Inactivity check has been activated.'
            case _ if command_lowercase.startswith('inactivity span'):
                value = command[15:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'inactivity_span', value)
                        response = ('The maximum allowed time of inactivity '
                                    'has been set to {} days'.format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['inactivity_span'])
            case _ if command_lowercase.startswith('inactivity warn'):
                value = command[15:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'inactivity_warn', value)
                        response = ('The time of inactivity to send a warning '
                                    'upon before action has been set to {} '
                                    'minutes'.format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['inactivity_warn'])
            case _ if command_lowercase.startswith('join'):
                muc_jid = command[5:]
                response = await XmppCommands.muc_join(self, muc_jid)
            case 'options':
                response = 'Options:\n```'
                response += XmppCommands.print_options(self, room)
                response += '\n```'
            case _ if command_lowercase.startswith('kick'):
                if command[5:]:
                    value = command[5:].split()
                    alias = value[0]
                    reason = ' '.join(value[1:]) if len(value) > 1 else None
                    await XmppCommands.kick(self, room, alias, reason)
            case 'message off':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'check_message', 0)
                response = 'Message check has been deactivated.'
            case 'message on':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'check_message', 1)
                response = 'Message check has been activated.'
            case _ if command_lowercase.startswith('score messages'):
                value = command[14:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'score_messages', value)
                        response = ('Score for messages has been set to {}'
                                    .format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['score_messages'])
            case _ if command_lowercase.startswith('score presence'):
                value = command[14:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'score_presence', value)
                        response = ('Score for presence has been set to {}'
                                    .format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['score_presence'])
            case _ if command_lowercase.startswith('scores reset'):
                jid_bare = command[12:].strip()
                if jid_bare:
                    del self.settings[room]['scores'][jid_bare]
                    value = self.settings[room]['scores']
                    XmppCommands.update_setting_value(
                        self, room, db_file, 'scores', value)
                    response = 'Score for {} has been reset'.format(jid_bare)
                else:
                    XmppCommands.update_setting_value(
                        self, room, db_file, 'scores', {})
                    response = 'All scores have been reset'
            case _ if command_lowercase.startswith('scores'):
                jid_bare = command[6:].strip()
                if jid_bare:
                    response = str(self.settings[room]['scores'][jid_bare])
                else:
                    response = str(self.settings[room]['scores'])
            case 'start':
                XmppCommands.update_setting_value(self, room, db_file,
                                                  'enabled', 1)
                XmppStatus.send_status_message(self, room)
            case 'stats':
                response = XmppCommands.print_statistics(db_file)
            case 'status off':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'check_status', 0)
                response = 'Status message check has been deactivated'
            case 'status on':
                XmppCommands.update_setting_value(
                    self, room, db_file, 'check_status', 1)
                response = 'Status message check has been activated'
            case 'stop':
                XmppCommands.update_setting_value(self, room, db_file,
                                                  'enabled', 0)
                XmppStatus.send_status_message(self, room)
            case 'support':
                response = XmppCommands.print_support_jid()
                await XmppCommands.invite_jid_to_muc(self, room)
            case _ if command_lowercase.startswith('timer'):
                value = command[5:].strip()
                if value:
                    try:
                        value = int(value)
                        XmppCommands.update_setting_value(
                            self, room, db_file, 'timer', value)
                        response = ('Timer value for countdown before '
                                    'committing an action has been set to {} '
                                    'seconds'.format(value))
                    except:
                        response = 'Enter a numerical value.'
                else:
                    response = str(self.settings[room]['timer'])
            case 'version':
                response = XmppCommands.print_version()
            case _ if command_lowercase.startswith('xmpp:'):
                response = await XmppCommands.muc_join(self, command)
            case _:
                response = XmppCommands.print_unknown()

        command_time_finish = time.time()
        command_time_total = command_time_finish - command_time_start
        command_time_total = round(command_time_total, 3)

        if response: XmppMessage.send_reply(self, message, response)

        if room in self.settings and self.settings[room]['finished']:
            response_finished = ('Finished. Total time: {}s'
                                 .format(command_time_total))
            XmppMessage.send_reply(self, message, response_finished)