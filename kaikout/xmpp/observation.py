#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from hashlib import sha256
from kaikout.database import Toml
from kaikout.log import Logger
from kaikout.xmpp.commands import XmppCommands
from kaikout.xmpp.message import XmppMessage
from kaikout.xmpp.moderation import XmppModeration
from kaikout.xmpp.muc import XmppMuc

logger = Logger(__name__)

class XmppObservation:


    async def observe_inactivity(self, db_file, room):
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
                            reason = 'Inactivity detected'
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


    async def observe_jid(self, alias, jid_bare, room):
        jid_to_sha256 = sha256(jid_bare.encode('utf-8')).hexdigest()
        for jid in self.blocklist['entries']:
            if jid not in self.settings[room]['rtbl_ignore']:
                for node in self.blocklist['entries'][jid]:
                    for item_id in self.blocklist['entries'][jid][node]:
                        if jid_to_sha256 == item_id:
                            reason = 'Jabber ID has been marked by RTBL: Publisher: {}; Node: {}.'.format(
                                jid, node)
                            await XmppCommands.devoice(self, room, alias, reason)
                            break


    async def observe_message(self, db_file, alias, message_body, room):
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


    async def observe_status_message(self, alias, db_file, jid_bare, presence_body, room):
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


    async def observe_strikes(self, db_file, presence, room):
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
