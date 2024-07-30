#!/usr/bin/env python3

# Kaikout: Kaiko Out anti-spam bot for XMPP
# Copyright (C) 2024 Schimon Zackary
# This file is part of Kaikout.
# See the file LICENSE for copying permission.

# from kaikout.about import Documentation
from kaikout.utilities import Config
# from kaikout.xmpp.chat import XmppChat
from kaikout.xmpp.client import XmppClient
from getpass import getpass
from argparse import ArgumentParser
import logging
# import os
# import slixmpp
# import sys

def main():
    # Setup the command line arguments.
    parser = ArgumentParser(description=XmppClient.__doc__)

    # Output verbosity options.
    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const", dest="loglevel",
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO)

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    account_xmpp = Config.get_values('accounts.toml', 'xmpp')

    if args.jid is None and not account_xmpp['client']['jid']:
        args.jid = input("Username: ")
    if args.password is None and not account_xmpp['client']['password']:
        args.password = getpass("Password: ")

    # Try configuration file
    if 'client' in account_xmpp:
        jid = account_xmpp['client']['jid']
        password = account_xmpp['client']['password']
        alias = account_xmpp['client']['alias'] if 'alias' in account_xmpp['client'] else None
        hostname = account_xmpp['client']['hostname'] if 'hostname' in account_xmpp['client'] else None
        port = account_xmpp['client']['port'] if 'port' in account_xmpp['client'] else None
        XmppClient(jid, password, hostname, port, alias)

if __name__ == '__main__':
    main()
