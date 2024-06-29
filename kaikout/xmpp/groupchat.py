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
from kaikout.xmpp.bookmark import XmppBookmark
from kaikout.xmpp.muc import XmppMuc
from kaikout.xmpp.status import XmppStatus
from kaikout.log import Logger, Message

logger = Logger(__name__)


class XmppGroupchat:

    async def autojoin(self, bookmarks):
        mucs_join_success = []
        for bookmark in bookmarks:
            if bookmark["jid"] and bookmark["autojoin"]:
                if not bookmark["nick"]:
                    bookmark["nick"] = self.alias
                    logger.error('Alias (i.e. Nicknname) is missing for '
                                  'bookmark {}'.format(bookmark['name']))
                alias = bookmark["nick"]
                room = bookmark["jid"]
                Message.printer('Joining to MUC {} ...'.format(room))
                result = await XmppMuc.join(self, room, alias)
                if result == 'ban':
                    await XmppBookmark.remove(self, room)
                    logger.warning('{} is banned from {}'.format(self.alias, room))
                    logger.warning('Groupchat {} has been removed from bookmarks'
                                   .format(room))
                else:
                    mucs_join_success.append(room)
                    logger.info('Autojoin groupchat\n'
                                'Name  : {}\n'
                                'JID   : {}\n'
                                'Alias : {}\n'
                                .format(bookmark["name"],
                                        bookmark["jid"],
                                        bookmark["nick"]))
            elif not bookmark["jid"]:
                logger.error('JID is missing for bookmark {}'
                              .format(bookmark['name']))
        return mucs_join_success
