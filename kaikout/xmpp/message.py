#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kaikout.log import Logger
import xml.sax.saxutils as saxutils

logger = Logger(__name__)

"""

NOTE

See XEP-0367: Message Attaching

"""

class XmppMessage:


    # def process():


    def send(self, jid, message_body, chat_type):
        jid_from = str(self.boundjid) if self.is_component else None
        self.send_message(mto=jid,
                          mfrom=jid_from,
                          mbody=message_body,
                          mtype=chat_type)


    def send_headline(self, jid, message_subject, message_body, chat_type):
        jid_from = str(self.boundjid) if self.is_component else None
        self.send_message(mto=jid,
                          mfrom=jid_from,
                          # mtype='headline',
                          msubject=message_subject,
                          mbody=message_body,
                          mtype=chat_type,
                          mnick=self.alias)


    # NOTE We might want to add more characters
    # def escape_to_xml(raw_string):
    # escape_map = {
    #     '"' : '&quot;',
    #     "'" : '&apos;'
    # }
    # return saxutils.escape(raw_string, escape_map)
    def send_oob(self, jid, url, chat_type):
        jid_from = str(self.boundjid) if self.is_component else None
        url = saxutils.escape(url)
        # try:
        html = (
            f'<body xmlns="http://www.w3.org/1999/xhtml">'
            f'<a href="{url}">{url}</a></body>')
        message = self.make_message(mto=jid,
                                    mfrom=jid_from,
                                    mbody=url,
                                    mhtml=html,
                                    mtype=chat_type)
        message['oob']['url'] = url
        message.send()
        # except:
        #     logging.error('ERROR!')
        #     logging.error(jid, url, chat_type, html)


    # FIXME Solve this function
    def send_oob_reply_message(message, url, response):
        reply = message.reply(response)
        reply['oob']['url'] = url
        reply.send()


    # def send_reply(self, message, message_body):
    #     message.reply(message_body).send()


    def send_reply(self, message, response):
        message.reply(response).send()
