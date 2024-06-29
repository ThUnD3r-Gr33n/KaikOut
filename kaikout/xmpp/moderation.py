#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kaikout.database import Toml
from kaikout.log import Logger
from kaikout.xmpp.commands import XmppCommands

logger = Logger(__name__)

class XmppModeration:


    def moderate_last_activity(self, room, jid_bare, timestamp):
        result = None
        if 'last_activity' not in self.settings[room]:
            self.settings[room]['last_activity'] = {}
        if jid_bare not in self.settings[room]['last_activity']:
            # self.settings[room]['last_activity'][jid_bare] = timestamp
            # last_activity_for_jid = self.settings[room]['last_activity'][jid_bare]
            db_file = Toml.instantiate(self, room)
            # Toml.update_jid_settings(self, room, db_file, 'last_activity', last_activity_for_jid)
            XmppCommands.update_last_activity(self, room, jid_bare, db_file, timestamp)
        else:
            jid_last_activity = self.settings[room]['last_activity'][jid_bare]
            span_inactivity = self.settings[room]['inactivity_span']
            span_inactivity_in_seconds = 60*60*24*span_inactivity
            if timestamp - jid_last_activity > span_inactivity_in_seconds:
                result = 'Inactivity'
                return result, span_inactivity
            span_inactivity_warn = self.settings[room]['inactivity_warn']
            span_inactivity_warn_in_seconds = 60*span_inactivity_warn
            if timestamp - jid_last_activity > span_inactivity_in_seconds - span_inactivity_warn_in_seconds:
                time_left = span_inactivity_in_seconds - (timestamp - jid_last_activity)
                time_left_in_seconds = time_left/60/60
                result = 'Warning'
                return result, time_left_in_seconds
        if not result:
            return None, None


    def moderate_message(self, message_body, room):
        # Process a message for faults and unsolicitations.
        message_body_lower = message_body.lower()
        message_body_lower_split = message_body_lower.split()

        # Count instances.
        message_body_lower_split_sort = list(set(message_body_lower_split))
        for i in message_body_lower_split_sort:
            count = message_body_lower_split.count(i)
            count_max = self.settings[room]['count']
            if count > count_max:
                reason = 'Spam (Repetition)'
                return reason

        # Check for denied phrases or words.
        blocklist = self.settings[room]['deny']
        for i in blocklist:
            if i in message_body_lower:
                # jid_bare = XmppMuc.get_full_jid(self, room, alias).split('/')[0]
                reason = 'Spam (Blocklist)'
                return reason

        # Check for frequency.
        message_activity = self.settings[room]['activity_message']
        length = len(message_activity)
        message_frequency = self.settings[room]['frequency_messages']
        if (message_activity[length-1]['timestamp'] - message_activity[length-2]['timestamp'] < message_frequency and
            message_activity[length-1]['alias'] == message_activity[length-2]['alias'] and
            message_activity[length-1]['id'] != message_activity[length-2]['id']):
            reason = 'Spam (Flooding)'
            return reason
        
        # message_activity = self.settings[room]['activity_message']
        # count = {}
        # for i in message_activity:
        #     message_activity.pop()
        #     for j in message_activity:
        #         if (i['timestamp'] - j['timestamp'] < 3 and
        #             i['alias'] == j['alias'] and
        #             i['id'] != j['id']):
        #             if 'alias' in count:
        #                 count['alias'] += 1
        #             else:
        #                 count['alias'] = 0


    def moderate_status_message(self, status_message, room):
        # Process a status message for faults and unsolicitations.
        status_message_lower = status_message.lower()
        status_message_lower_split = status_message_lower.split()
        reason = None

        # Count instances.
        message_body_lower_split_sort = list(set(status_message_lower_split))
        for i in message_body_lower_split_sort:
            count = status_message_lower_split.count(i)
            count_max = self.settings[room]['count']
            if count > count_max:
                reason = 'Spam (Repetition)'
                return reason, 1

        # Check for denied phrases or words.
        blocklist = self.settings[room]['deny']
        for i in blocklist:
            if i in status_message_lower:
                # jid_bare = XmppMuc.get_full_jid(self, room, alias).split('/')[0]
                reason = 'Spam (Blocklist)'
                return reason, 1

        # Check for frequency.
        presence_activity = self.settings[room]['activity_presence']
        length = len(presence_activity)
        presence_frequency = self.settings[room]['frequency_presence']
        if (presence_activity[length-1]['body'] and
            presence_activity[length-2]['body'] and
            presence_activity[length-1]['timestamp'] - presence_activity[length-2]['timestamp'] < presence_frequency and
            presence_activity[length-1]['alias'] == presence_activity[length-2]['alias'] and
            presence_activity[length-1]['id'] != presence_activity[length-2]['id'] and
            presence_activity[length-1]['body'] != presence_activity[length-2]['body']):
            reason = 'Spam (Flooding)'
            return reason, 0

        if not reason:
            return None, None
