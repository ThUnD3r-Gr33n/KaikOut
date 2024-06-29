#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kaikout.database import Toml
from kaikout.log import Logger
from kaikout.xmpp.presence import XmppPresence
from kaikout.xmpp.utilities import XmppUtilities
import sys

logger = Logger(__name__)


class XmppStatus:


    def send_status_message(self, room, status_mode=None, status_text=None):
        """
        Send status message.
    
        Parameters
        ----------
        jid : str
            Jabber ID.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: jid: {}'.format(function_name, room))
        if not status_mode and not status_text:
            if XmppUtilities.is_moderator(self, room, self.alias):
                if room not in self.settings:
                    Toml.instantiate(self, room)
                    # Toml.load_jid_settings(self, room)
                if self.settings[room]['enabled']:
                    jid_task = self.actions[room] if room in self.actions else None
                    if jid_task and len(jid_task):
                        status_mode = 'dnd'
                        status_text = jid_task[list(jid_task.keys())[0]]
                    else:
                        status_mode = 'available'
                        status_text = '👁️ Moderating'
                else:
                    status_mode = 'xa'
                    status_text = '💤 Disabled'
            else:
                status_text = '⚠️ KaikOut requires moderation privileges'
                status_mode = 'away'
        XmppPresence.send(self, room, status_text, status_type=status_mode)
