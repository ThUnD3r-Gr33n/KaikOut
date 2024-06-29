#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

TODO

1) Send message to inviter that bot has joined to groupchat.

2) If groupchat requires captcha, send the consequent message.

3) If groupchat error is received, send that error message to inviter.

FIXME

1) Save name of groupchat instead of jid as name

"""
from slixmpp.exceptions import IqError, IqTimeout, PresenceError
from kaikout.log import Logger

logger = Logger(__name__)


class XmppMuc:


    async def get_affiliation(self, room, affiliation):
        jids = await self.plugin['xep_0045'].get_affiliation_list(room, affiliation)
        return jids


    def get_alias(self, room, jid):
        alias = self.plugin['xep_0045'].get_nick(room, jid)
        return alias


    def get_full_jid(self, room, alias):
        """
        Get full JId.
    
        Parameters
        ----------
        jid_full : str
            Full Jabber ID.
        """
        jid_full = self.plugin['xep_0045'].get_jid_property(room, alias, 'jid')
        return jid_full


    def get_joined_rooms(self):
        rooms = self.plugin['xep_0045'].get_joined_rooms()
        return rooms


    async def get_role(self, room, role):
        jids = await self.plugin['xep_0045'].get_roles_list(room, role)
        return jids


    def get_roster(self, room):
        roster = self.plugin['xep_0045'].get_roster(room)
        return roster
    
    
    def is_moderator(self, room, alias):
        """Check if given JID is a moderator"""
        role = self.plugin['xep_0045'].get_jid_property(room, alias, 'role')
        if role == 'moderator':
            result = True
        else:
            result = False
        return result


    async def join(self, jid, alias=None, password=None):
        # token = await initdb(
        #     muc_jid,
        #     sqlite.get_setting_value,
        #     "token"
        #     )
        # if token != "accepted":
        #     token = randrange(10000, 99999)
        #     await initdb(
        #         muc_jid,
        #         sqlite.update_setting_value,
        #         ["token", token]
        #     )
        #     self.send_message(
        #         mto=inviter,
        #         mfrom=self.boundjid.bare,
        #         mbody=(
        #             "Send activation token {} to groupchat xmpp:{}?join."
        #             ).format(token, muc_jid)
        #         )
        logger.info('Joining groupchat\nJID     : {}\n'.format(jid))
        jid_from = str(self.boundjid) if self.is_component else None
        if not alias: alias = self.alias
        try:
            await self.plugin['xep_0045'].join_muc_wait(jid,
                                                        alias,
                                                        presence_options = {"pfrom" : jid_from},
                                                        password=password,
                                                        maxchars=0,
                                                        maxstanzas=0,
                                                        seconds=0,
                                                        since=0,
                                                        timeout=30)
            result = 'success'
        except IqError as e:
            logger.error('Error XmppIQ')
            logger.error(str(e))
            logger.error(jid)
            result = 'error'
        except IqTimeout as e:
            logger.error('Timeout XmppIQ')
            logger.error(str(e))
            logger.error(jid)
            result = 'timeout'
        except PresenceError as e:
            logger.error('Error Presence')
            logger.error(str(e))
            if (e.condition == 'forbidden' and
                e.presence['error']['code'] == '403'):
                logger.warning('{} is banned from {}'.format(self.alias, jid))
                result = 'ban'
            else:
                result = 'error'
        return result


    def leave(self, jid):
        jid_from = str(self.boundjid) if self.is_component else None
        message = ('This news bot will now leave this groupchat.\n'
                   'The JID of this news bot is xmpp:{}?message'
                   .format(self.boundjid.bare))
        status_message = ('This bot has left the group. '
                         'It can be reached directly via {}'
                         .format(self.boundjid.bare))
        self.send_message(mto=jid,
                          mfrom=self.boundjid,
                          mbody=message,
                          mtype='groupchat')
        self.plugin['xep_0045'].leave_muc(jid,
                                          self.alias,
                                          status_message,
                                          jid_from)


    async def set_affiliation(self, room, affiliation, jid=None, alias=None, reason=None):
        jid_from = str(self.boundjid) if self.is_component else None
        try:
            await self.plugin['xep_0045'].set_affiliation(
                room, affiliation, jid=jid, nick=alias, reason=reason, ifrom=jid_from)
        except IqError as e:
            logger.error('Error XmppIQ')
            logger.error('Could not set affiliation at room: {}'.format(room))
            logger.error(str(e))
            logger.error(room)


    async def set_role(self, room, alias, role, reason=None):
        jid_from = str(self.boundjid) if self.is_component else None
        try:
            await self.plugin['xep_0045'].set_role(
                room, alias, role, reason=None, ifrom=jid_from)
        except IqError as e:
            logger.error('Error XmppIQ')
            logger.error('Could not set role of alias: {}'.format(alias))
            logger.error(str(e))
            logger.error(room)
