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
from kaikout.xmpp.muc import XmppMuc
from kaikout.xmpp.observation import XmppObservation
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
                alias != self.alias and
                jid_bare and
                jid_bare not in self.settings[room]['jid_whitelist']):
                identifier = message['id']
                fields = [alias, message_body, identifier, timestamp]
                Log.toml(self, room, fields, 'message')
                # Check for message
                await XmppObservation.observe_message(self, db_file, alias, message_body, room)
                # Check for inactivity
                await XmppObservation.observe_inactivity(self, db_file, room)


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
        jid_bare = presence['muc']['jid'].bare
        if (XmppMuc.is_moderator(self, room, self.alias) and
            self.settings[room]['enabled'] and
            jid_bare and
            jid_bare not in self.settings[room]['jid_whitelist']):
            await XmppObservation.observe_jid(self, alias, jid_bare, room)
            # message_body = 'Greetings {} and welcome to groupchat {}'.format(alias, room)
            # XmppMessage.send(self, jid.bare, message_body, 'chat')
            # Send MUC-PM in case there is no indication for reception of 1:1
            # jid_from = presence['from']
            # XmppMessage.send(self, jid_from, message_body, 'chat')


    async def on_muc_presence(self, presence):
        alias = presence['muc']['nick']
        identifier = presence['id']
        jid_bare = presence['muc']['jid'].bare
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
            await XmppObservation.observe_strikes(self, db_file, presence, room)
            if jid_bare and jid_bare not in self.settings[room]['jid_whitelist']:
                # Check for status message
                await XmppObservation.observe_status_message(self, alias, db_file, jid_bare, presence_body, room)
                # Check for inactivity
                await XmppObservation.observe_inactivity(self, db_file, room)


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
