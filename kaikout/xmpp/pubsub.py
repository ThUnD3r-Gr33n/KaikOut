#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Functions create_node and create_entry are derived from project atomtopubsub.

"""

import hashlib
from kaikout.log import Logger
from slixmpp.exceptions import IqTimeout, IqError

logger = Logger(__name__)


class XmppPubsub:


    async def get_pubsub_services(self):
        results = []
        iq = await self['xep_0030'].get_items(jid=self.boundjid.domain)
        items = iq['disco_items']['items']
        for item in items:
            iq = await self['xep_0030'].get_info(jid=item[0])
            identities = iq['disco_info']['identities']
            for identity in identities:
                if identity[0] == 'pubsub' and identity[1] == 'service':
                    result = {}
                    result['jid'] = item[0]
                    if item[1]: result['name'] =  item[1]
                    elif item[2]: result['name'] = item[2]
                    else: result['name'] = item[0]
                    results.extend([result])
        return results


    async def get_node_properties(self, jid, node):
        config = await self.plugin['xep_0060'].get_node_config(jid, node)
        subscriptions = await self.plugin['xep_0060'].get_node_subscriptions(jid, node)
        affiliations = await self.plugin['xep_0060'].get_node_affiliations(jid, node)
        properties = {'config': config,
                      'subscriptions': subscriptions,
                      'affiliations': affiliations}
        breakpoint()
        return properties


    async def get_node_configuration(self, jid, node_id):
        node = await self.plugin['xep_0060'].get_node_config(jid, node_id)
        if not node:
            print('NODE CONFIG', node_id, str(node))
        return node


    async def get_nodes(self, jid):
        nodes = await self.plugin['xep_0060'].get_nodes(jid)
        # 'self' would lead to slixmpp.jid.InvalidJID: idna validation failed:
        return nodes


    async def get_item(self, jid, node, item_id):
        item = await self.plugin['xep_0060'].get_item(jid, node, item_id)
        return item


    async def get_items(self, jid, node):
        items = await self.plugin['xep_0060'].get_items(jid, node)
        return items


    async def subscribe(self, jid, node):
        result = await self['xep_0060'].subscribe(jid, node)
        return result


    async def get_node_subscriptions(self, jid, node):
        try:
            subscriptions = await self['xep_0060'].get_node_subscriptions(jid, node)
            return subscriptions
        except IqError as e:
            print(e)
