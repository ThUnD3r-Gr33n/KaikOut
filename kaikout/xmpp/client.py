#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime
from kaikout.about import Documentation
from kaikout.database import Toml
from kaikout.log import Logger
from kaikout.utilities import Config, Log, BlockList
from kaikout.xmpp.bookmark import XmppBookmark
from kaikout.xmpp.chat import XmppChat
from kaikout.xmpp.commands import XmppCommands
from kaikout.xmpp.groupchat import XmppGroupchat
from kaikout.xmpp.message import XmppMessage
from kaikout.xmpp.moderation import XmppModeration
from kaikout.xmpp.muc import XmppMuc
from kaikout.xmpp.pubsub import XmppPubsub
from kaikout.xmpp.status import XmppStatus
import slixmpp
import time

# time_now = datetime.now()
# time_now = time_now.strftime("%H:%M:%S")

# def print_time():
#     # return datetime.now().strftime("%H:%M:%S")
#     now = datetime.now()
#     current_time = now.strftime("%H:%M:%S")
#     return current_time

logger = Logger(__name__)

class XmppClient(slixmpp.ClientXMPP):

    """
    KaikOut - A moderation chat bot for Jabber/XMPP.
    KaikOut is a chat control bot for XMPP groupchats.
    """

    def __init__(self, jid, password, hostname, port, alias):
        slixmpp.ClientXMPP.__init__(self, jid, password, hostname, port, alias)
        # Handlers for action messages.
        self.actions = {}
        self.action_count = 0
        # A handler for alias.
        self.alias = alias
        # A handler for configuration.
        self.defaults = Config.get_values('settings.toml', 'defaults')
        # Handlers for connectivity.
        self.connection_attempts = 0
        self.max_connection_attempts = 10
        self.task_ping_instance = {}
        self.reconnect_timeout = Config.get_values('accounts.toml', 'xmpp')['settings']['reconnect_timeout']
        # A handler for operators.
        self.operators = Config.get_values('accounts.toml', 'xmpp')['operators']
        # A handler for blocklist.
        #self.blocklist = {}
        BlockList.load_blocklist(self)
        # A handler for sessions.
        self.sessions = {}
        # A handler for settings.
        self.settings = {}
        # A handler for tasks.
        self.tasks = {}
        # Register plugins.
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0048') # Bookmarks
        self.register_plugin('xep_0060') # Publish-Subscribe
        self.register_plugin('xep_0050') # Ad-Hoc Commands
        self.register_plugin('xep_0084') # User Avatar
        self.register_plugin('xep_0085') # Chat State Notifications
        self.register_plugin('xep_0115') # Entity Capabilities
        self.register_plugin('xep_0122') # Data Forms Validation
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0249') # Direct MUC Invitations
        self.register_plugin('xep_0369') # Mediated Information eXchange (MIX)
        self.register_plugin('xep_0437') # Room Activity Indicators
        self.register_plugin('xep_0444') # Message Reactions
        # Register events.
        # self.add_event_handler("chatstate_composing", self.on_chatstate_composing)
        # self.add_event_handler('connection_failed', self.on_connection_failed)
        self.add_event_handler("disco_info", self.on_disco_info)
        self.add_event_handler("groupchat_direct_invite", self.on_groupchat_direct_invite) # XEP_0249
        self.add_event_handler("groupchat_invite", self.on_groupchat_invite) # XEP_0045
        self.add_event_handler("message", self.on_message)
        self.add_event_handler("reactions", self.on_reactions)
        # self.add_event_handler("room_activity", self.on_room_activity)
        # self.add_event_handler("session_resumed", self.on_session_resumed)
        self.add_event_handler("session_start", self.on_session_start)
        # Connect and process.
        self.connect()
        self.process()

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.

        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        if presence['muc']['nick'] != self.alias:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')


    async def on_disco_info(self, DiscoInfo):
        jid = DiscoInfo['from']
        await self['xep_0115'].update_caps(jid=jid)
        # jid_bare = DiscoInfo['from'].bare


    # TODO Test
    async def on_groupchat_invite(self, message):
        jid_full = str(message['from'])
        room = message['groupchat_invite']['jid']
        result = await XmppMuc.join(self, room)
        if result == 'ban':
            message_body = '{} is banned from {}'.format(self.alias, room)
            jid_bare = message['from'].bare
            # This might not be necessary because JID might not be of the inviter, but rather of the MUC
            XmppMessage.send(self, jid_bare, message_body, 'chat')
            logger.warning(message_body)
            print("on_groupchat_invite")
            print("BAN BAN BAN BAN BAN")
            print("on_groupchat_invite")
            print(jid_full)
            print(jid_full)
            print(jid_full)
            print("on_groupchat_invite")
            print("BAN BAN BAN BAN BAN")
            print("on_groupchat_invite")
        else:
            await XmppBookmark.add(self, room)
            message_body = (
                'Greetings! I am {}, the news anchor.\n'
                'My job is to bring you the latest news from sources you '
                'provide me with.\n'
                'You may always reach me via xmpp:{}?message'
                .format(self.alias, self.boundjid.bare))
            XmppMessage.send(self, room, message_body, 'groupchat')
            XmppStatus.send_status_message(self, room)


    async def on_groupchat_direct_invite(self, message):
        room = message['groupchat_invite']['jid']
        result = await XmppMuc.join(self, room)
        if result == 'ban':
            message_body = '{} is banned from {}'.format(self.alias, room)
            jid_bare = message['from'].bare
            XmppMessage.send(self, jid_bare, message_body, 'chat')
            logger.warning(message_body)
        else:
            await XmppBookmark.add(self, room)
            message_body = ('/me moderation chat bot. Jabber ID: xmpp:{}?message'
                            .format(self.boundjid.bare))
            XmppMessage.send(self, room, message_body, 'groupchat')
            XmppStatus.send_status_message(self, room)


    async def on_message(self, message):
        await XmppChat.process_message(self, message)
        # if message['type'] == 'groupchat':
        # if 'mucroom' in message.keys():
        if message['mucroom']:
            alias = message['mucnick']
            message_body = message['body']
            identifier = message['id']
            lang = message['lang']
            room = message['mucroom']
            timestamp_iso = datetime.now().isoformat()
            fields = ['message', timestamp_iso, alias, message_body, lang, identifier]
            filename = datetime.today().strftime('%Y-%m-%d') + '_' + room
            Log.csv(filename, fields)
            db_file = Toml.instantiate(self, room)
            timestamp = time.time()
            jid_bare = XmppMuc.get_full_jid(self, room, alias).split('/')[0]
            XmppCommands.update_last_activity(self, room, jid_bare, db_file, timestamp)
            # Toml.load_jid_settings(self, room)
            # await XmppChat.process_message(self, message)
            if (XmppMuc.is_moderator(self, room, self.alias) and
                self.settings[room]['enabled'] and
                alias != self.alias):
                identifier = message['id']
                fields = [alias, message_body, identifier, timestamp]
                Log.toml(self, room, fields, 'message')
                # Check for message
                if self.settings[room]['check_message']:
                    reason = XmppModeration.moderate_message(self, message_body, room)
                    if reason:
                        score_max = self.settings[room]['score_messages']
                        score = XmppCommands.raise_score(self, room, alias, db_file, reason)
                        if score > score_max:
                            if self.settings[room]['action']:
                                jid_bare = await XmppCommands.outcast(self, room, alias, reason)
                                # admins = await XmppMuc.get_affiliation_list(self, room, 'admin')
                                # owners = await XmppMuc.get_affiliation_list(self, room, 'owner')
                                moderators = await XmppMuc.get_role_list(
                                    self, room, 'moderator')
                                # Report to the moderators.
                                message_to_moderators = (
                                    'Participant {} ({}) has been banned from '
                                    'groupchat {}.'.format(alias, jid_bare, room))
                                for alias in moderators:
                                    jid_full = XmppMuc.get_full_jid(self, room, alias)
                                    XmppMessage.send(self, jid_full, message_to_moderators, 'chat')
                                # Inform the subject
                                message_to_participant = (
                                    'You were banned from groupchat {}.  Please '
                                    'contact the moderators if you think this was '
                                    'a mistake.'.format(room))
                                XmppMessage.send(self, jid_bare, message_to_participant, 'chat')
                            else:
                                await XmppCommands.devoice(self, room, alias, reason)
                # Check for inactivity
                if self.settings[room]['check_inactivity']:
                    roster_muc = XmppMuc.get_roster(self, room)
                    for alias in roster_muc:
                        if alias != self.alias:
                            jid_bare = XmppMuc.get_full_jid(self, room, alias).split('/')[0]
                            result, span = XmppModeration.moderate_last_activity(
                                self, room, jid_bare, timestamp)
                            if result:
                                message_to_participant = None
                                if 'inactivity_notice' not in self.settings[room]:
                                    self.settings[room]['inactivity_notice'] = []
                                noticed_jids = self.settings[room]['inactivity_notice']
                                if result == 'Inactivity':
                                    if jid_bare in noticed_jids: noticed_jids.remove(jid_bare)
                                    await XmppCommands.kick(self, room, alias, reason)
                                    message_to_participant = (
                                        'You were expelled from groupchat {} due to '
                                        'being inactive for {} days.'.format(room, span))
                                elif result == 'Warning' and jid_bare not in noticed_jids:
                                    noticed_jids.append(jid_bare)
                                    time_left = int(span)
                                    if not time_left: time_left = 'an'
                                    message_to_participant = (
                                        'This is an inactivity-warning.\n'
                                        'You are expected to be expelled from '
                                        'groupchat {} within {} hour time.'
                                        .format(room, int(span) or 'an'))
                                Toml.update_jid_settings(
                                    self, room, db_file, 'inactivity_notice', noticed_jids)
                                if message_to_participant:
                                    XmppMessage.send(
                                        self, jid_bare, message_to_participant, 'chat')


    async def on_muc_got_online(self, presence):
        room = presence['muc']['room']
        alias = presence['muc']['nick']
        presence_body = 'User has joined to the groupchat.'
        identifier = presence['id']
        lang = presence['lang']
        timestamp_iso = datetime.now().isoformat()
        fields = ['message', timestamp_iso, alias, presence_body, lang, identifier]
        filename = datetime.today().strftime('%Y-%m-%d') + '_' + room
        Log.csv(filename, fields)
        if (XmppMuc.is_moderator(self, room, self.alias) and
            self.settings[room]['enabled']):
            jid = presence['muc']['jid']
            from hashlib import sha256
            jid_to_sha256 = sha256(jid.bare.encode('utf-8')).hexdigest()
            for jid in self.blocklist['entries']:
                if jid not in self.settings[room]['rtbl_ignore']:
                    for node in self.blocklist['entries'][jid]:
                        for item_id in self.blocklist['entries'][jid][node]:
                            if jid_to_sha256 == item_id:
                                reason = 'Jabber ID has been marked by RTBL: Publisher: {}; Node: {}.'.format(
                                    jid, node)
                                await XmppCommands.devoice(self, room, alias, reason)
                                break
            # message_body = 'Greetings {} and welcome to groupchat {}'.format(alias, room)
            # XmppMessage.send(self, jid.bare, message_body, 'chat')
            # Send MUC-PM in case there is no indication for reception of 1:1
            # jid_from = presence['from']
            # XmppMessage.send(self, jid_from, message_body, 'chat')


    async def on_muc_presence(self, presence):
        alias = presence['muc']['nick']
        identifier = presence['id']
        jid_full = presence['muc']['jid']
        jid_bare = jid_full.bare
        lang = presence['lang']
        status_codes = presence['muc']['status_codes']
        actor_alias = presence['muc']['item']['actor']['nick']
        if 301 in status_codes:
            presence_body = 'User has been banned by {}'.format(actor_alias)
        elif 307 in status_codes:
            presence_body = 'User has been kicked by {}'.format(actor_alias)
        else:
            presence_body = presence['status']
        room = presence['muc']['room']
        timestamp_iso = datetime.now().isoformat()
        fields = ['presence', timestamp_iso, alias, presence_body, lang, identifier]
        filename = datetime.today().strftime('%Y-%m-%d') + '_' + room
        # if identifier and presence_body:
        Log.csv(filename, fields)
        db_file = Toml.instantiate(self, room)
        if (XmppMuc.is_moderator(self, room, self.alias) and
            self.settings[room]['enabled'] and
            alias != self.alias):
            timestamp = time.time()
            fields = [alias, presence_body, identifier, timestamp]
            Log.toml(self, room, fields, 'presence')
            # Count bans and kicks
            if self.settings[room]['check_moderation']:
                status_codes = presence['muc']['status_codes']
                if (301 in status_codes or 307 in status_codes):
                    actor_jid_bare = presence['muc']['item']['actor']['jid'].bare
                    actor_alias = presence['muc']['item']['actor']['nick']
                    if 301 in status_codes:
                        presence_body = 'User has been banned by {}'.format(actor_alias)
                        XmppCommands.update_score_ban(self, room, actor_jid_bare, db_file)
                    elif 307 in status_codes:
                        presence_body = 'User has been kicked by {}'.format(actor_alias)
                        XmppCommands.update_score_kick(self, room, actor_jid_bare, db_file)
                    if 'score_ban' in self.settings[room] and actor_jid_bare in self.settings[room]['score_ban']:
                        score_ban = self.settings[room]['score_ban'][actor_jid_bare]
                    else:
                        score_ban = 0
                    if 'score_kick' in self.settings[room] and actor_jid_bare in self.settings[room]['score_kick']:
                        score_kick = self.settings[room]['score_kick'][actor_jid_bare]
                    else:
                        score_kick = 0
                    score_outcast = score_ban + score_kick
                    if score_outcast > self.settings[room]['score_outcast']:
                        reason = 'Moderation abuse has been triggered'
                        await XmppMuc.set_affiliation(self, room, 'member', jid=actor_jid_bare, reason=reason)
                        await XmppMuc.set_role(self, room, actor_alias, 'participant', reason)
            # Check for status message
            if self.settings[room]['check_status']:
                reason, timer = XmppModeration.moderate_status_message(self, presence_body, room)
                if reason and timer and not (room in self.tasks and
                                             jid_bare in self.tasks[room] and
                                             'countdown' in self.tasks[room][jid_bare]):
                    print('reason and timer for jid: ' + jid_bare + ' at room ' + room)
                    score_max = self.settings[room]['score_presence']
                    score = XmppCommands.raise_score(self, room, alias, db_file, reason)
                    if room not in self.tasks:
                        self.tasks[room] = {}
                    if jid_bare not in self.tasks[room]:
                        self.tasks[room][jid_bare] = {}
                    # if 'countdown' in self.tasks[room][jid_bare]:
                    #     self.tasks[room][jid_bare]['countdown'].cancel()
                    if 'countdown' not in self.tasks[room][jid_bare]:
                        seconds = self.settings[room]['timer']
                        self.tasks[room][jid_bare]['countdown'] = asyncio.create_task(
                            XmppCommands.countdown(self, seconds, room, alias, reason))
                    message_to_participant = (
                        'Your status message "{}" violates policies of groupchat '
                        '{}.\n'
                        'You have {} seconds to change your status message, in '
                        'order to avoid consequent actions.'
                        .format(presence_body, room, seconds))
                    XmppMessage.send(self, jid_bare, message_to_participant, 'chat')
                elif reason and not (room in self.tasks
                                     and jid_bare in self.tasks[room] and
                                     'countdown' in self.tasks[room][jid_bare]):
                    print('reason for jid: ' + jid_bare + ' at room ' + room)
                    score_max = self.settings[room]['score_presence']
                    score = XmppCommands.raise_score(self, room, alias, db_file, reason)
                    if score > score_max:
                        if self.settings[room]['action']:
                            jid_bare = await XmppCommands.outcast(
                                self, room, alias, reason)
                            # admins = await XmppMuc.get_affiliation_list(self, room, 'admin')
                            # owners = await XmppMuc.get_affiliation_list(self, room, 'owner')
                            moderators = await XmppMuc.get_role_list(
                                self, room, 'moderator')
                            # Report to the moderators.
                            message_to_moderators = (
                                'Participant {} ({}) has been banned from '
                                'groupchat {}.'.format(alias, jid_bare, room))
                            for alias in moderators:
                                # jid_full = presence['muc']['jid']
                                jid_full = XmppMuc.get_full_jid(self, room, alias)
                                XmppMessage.send(self, jid_full, message_to_moderators, 'chat')
                            # Inform the subject.
                            message_to_participant = (
                                'You were banned from groupchat {}.  Please '
                                'contact the moderators if you think this was a '
                                'mistake.'.format(room))
                            XmppMessage.send(self, jid_bare, message_to_participant, 'chat')
                        else:
                            await XmppCommands.devoice(self, room, alias, reason)
                elif (room in self.tasks and
                      jid_bare in self.tasks[room] and
                      'countdown' in self.tasks[room][jid_bare]) and not reason:
                    print('cancel task for jid: ' + jid_bare + ' at room ' + room)
                    print(self.tasks[room][jid_bare]['countdown'])
                    if self.tasks[room][jid_bare]['countdown'].cancel():
                        print(self.tasks[room][jid_bare]['countdown'])
                        message_to_participant = 'Thank you for your cooperation.'
                        XmppMessage.send(self, jid_bare, message_to_participant, 'chat')
                    del self.tasks[room][jid_bare]['countdown']
            # Check for inactivity
            if self.settings[room]['check_inactivity']:
                roster_muc = XmppMuc.get_roster(self, room)
                for alias in roster_muc:
                    if alias != self.alias:
                        jid_bare = XmppMuc.get_full_jid(self, room, alias).split('/')[0]
                        result, span = XmppModeration.moderate_last_activity(
                            self, room, jid_bare, timestamp)
                        if result:
                            message_to_participant = None
                            if 'inactivity_notice' not in self.settings[room]:
                                self.settings[room]['inactivity_notice'] = []
                            noticed_jids = self.settings[room]['inactivity_notice']
                            if result == 'Inactivity':
                                if jid_bare in noticed_jids: noticed_jids.remove(jid_bare)
                                # FIXME Counting and creating of key entry "score_inactivity" appear not to occur.
                                score_inactivity = XmppCommands.raise_score_inactivity(self, room, jid_bare, db_file)
                                if score_inactivity > 10:
                                    jid_bare = await XmppCommands.outcast(self, room, alias, reason)
                                    # admins = await XmppMuc.get_affiliation_list(self, room, 'admin')
                                    # owners = await XmppMuc.get_affiliation_list(self, room, 'owner')
                                    moderators = await XmppMuc.get_role_list(
                                        self, room, 'moderator')
                                    # Report to the moderators.
                                    message_to_moderators = (
                                        'Participant {} ({}) has been banned from '
                                        'groupchat {} due to being inactive for over {} times.'.format(
                                            alias, jid_bare, room, score_inactivity))
                                    for alias in moderators:
                                        # jid_full = presence['muc']['jid']
                                        jid_full = XmppMuc.get_full_jid(self, room, alias)
                                        XmppMessage.send(self, jid_full, message_to_moderators, 'chat')
                                    # Inform the subject.
                                    message_to_participant = (
                                        'You were banned from groupchat {} due to being '
                                        'inactive for over {} times.  Please contact the '
                                        ' moderators if you think this was a mistake'
                                        .format(room, score_inactivity))
                                else:
                                    await XmppCommands.kick(self, room, alias, reason)
                                    message_to_participant = (
                                        'You were expelled from groupchat {} due to '
                                        'being inactive for over {} days.'.format(room, span))
                                XmppCommands.remove_last_activity(self, room, jid_bare, db_file)
                            elif result == 'Warning' and jid_bare not in noticed_jids:
                                noticed_jids.append(jid_bare)
                                time_left = int(span)
                                if not time_left: time_left = 'an'
                                message_to_participant = (
                                    'This is an inactivity-warning.\n'
                                    'You are expected to be expelled from '
                                    'groupchat {} within {} hour time.'
                                    .format(room, int(span) or 'an'))
                            Toml.update_jid_settings(
                                self, room, db_file, 'inactivity_notice', noticed_jids)
                            if message_to_participant:
                                XmppMessage.send(
                                    self, jid_bare, message_to_participant, 'chat')


    def on_muc_self_presence(self, presence):
        actor = presence['muc']['item']['actor']['nick']
        alias = presence['muc']['nick']
        room = presence['muc']['room']
        if actor and alias == self.alias: XmppStatus.send_status_message(self, room)


    def on_reactions(self, message):
        reactions = message['reactions']['values']
        alias = message['mucnick']
        room = message['mucroom']
        affiliation = XmppMuc.get_affiliation(self, room, alias)
        if affiliation == 'member' and '👎' in reactions:
            message_body = '{} {} has reacted to message {} with {}'.format(
                affiliation, alias, message['id'], message['reactions']['plugin']['value'])
            message.reply(message_body).send()
            print(message_body)
            print(room)


    def on_room_activity(self, presence):
        print('on_room_activity')
        print(presence)
        print('testing mix core')
        breakpoint()


    async def on_session_start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        # self.command_list()
        # await self.get_roster()
        rtbl_sources = Config.get_values('rtbl.toml')['sources']
        for source in rtbl_sources:
            jabber_id = source['jabber_id']
            node_id = source['node_id']
            subscribe = await XmppPubsub.subscribe(self, jabber_id, node_id)
            if subscribe['pubsub']['subscription']['subscription'] == 'subscribed':
                rtbl_list = await XmppPubsub.get_items(self, jabber_id, node_id)
                rtbl_items = rtbl_list['pubsub']['items']
                for item in rtbl_items:
                    exist = False
                    item_id = item['id']
                    for jid in self.blocklist['entries']:
                        for node in jid:
                            for item in node:
                                if item_id == item:
                                    exist = True
                                    break
                    if not exist:
                        # TODO Extract items item_payload.find(namespace + 'title')
                        # NOTE (Pdb)
                        # for i in item['payload'].iter(): i.attrib
                        # {'reason': 'urn:xmpp:reporting:abuse'}
                        BlockList.add_entry_to_blocklist(self, jabber_id, node_id, item_id)
#           subscribe['from'] = xmppbl.org
#           subscribe['pubsub']['subscription']['node'] = 'muc_bans_sha256'
            subscriptions = await XmppPubsub.get_node_subscriptions(self, jabber_id, node_id)
        await self['xep_0115'].update_caps()
        bookmarks = await XmppBookmark.get_bookmarks(self)
        print(bookmarks)
        rooms = await XmppGroupchat.autojoin(self, bookmarks)
        # See also get_joined_rooms of slixmpp.plugins.xep_0045
        for room in rooms:
            XmppStatus.send_status_message(self, room)
            self.add_event_handler("muc::%s::got_online" % room, self.on_muc_got_online)
            self.add_event_handler("muc::%s::presence" % room, self.on_muc_presence)
            self.add_event_handler("muc::%s::self-presence" % room, self.on_muc_self_presence)
        await asyncio.sleep(5)
        self.send_presence(
            pshow='available',
            pstatus='👁️ KaikOut Moderation Chat Bot')


    def command_list(self):
        self['xep_0050'].add_command(node='search',
                                     name='🔍️ Search',
                                     handler=self._handle_search)
        self['xep_0050'].add_command(node='settings',
                                     name='⚙️ Settings',
                                     handler=self._handle_settings)
        self['xep_0050'].add_command(node='about',
                                     name='📜️ About',
                                     handler=self._handle_about)


    def _handle_cancel(self, payload, session):
        text_note = ('Operation has been cancelled.'
                     '\n\n'
                     'No action was taken.')
        session['notes'] = [['info', text_note]]
        return session


    def _handle_about(self, iq, session):
        text_note = Documentation.about()
        session['notes'] = [['info', text_note]]
        return session
