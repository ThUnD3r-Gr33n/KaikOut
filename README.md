# Moderation bot for XMPP

KaikOut is a portmanteau of Kaiko and Out.

Kaiko (懐古) translates from Japanese to "Old-Fashioned".

_Because spam has never been in fashion, unless it is served on a plate._

## KaikOut

KaikOut is a moderation bot for the XMPP communication network.

KaikOut is an XMPP bot that suprvises group chat activity and assists in blocking and preventing of abusive and unsolicited type of messages and activities.

KaikOut is designed primarily for the XMPP communication network (aka Jabber). Visit https://xmpp.org/software/ for more information.

You can run your own KaikOut instance as a client, from your own computer, server, and even from a Linux phone (i.e. Droidian, Kupfer, Mobian, NixOS, postmarketOS), as well as from Termux.

All you need is one of the above and an XMPP account to connect KaikOut with.

Good luck!

### Slixmpp

KaikOut is a powered by [slixmpp](https://codeberg.org/poezio/slixmpp).

### XMPP

XMPP is the Extensible Messaging and Presence Protocol, a set of open technologies for instant messaging, presence, multi-party chat, voice and video calls, collaboration, lightweight middleware, content syndication, and generalized routing of XML data.

Visit [XMPP](https://xmpp.org/) for more information [about](https://xmpp.org/about/) the XMPP protocol and check the [list](https://xmpp.org/software/) of XMPP clients.

KaikOut is primarily designed for XMPP (aka Jabber), yet it is built to be extended to other protocols.

## Features

### Control

- **Blocklist** - Check messages for denied phrases and words (activated by default).
- **Frequency** - Check the frequency of messages and status messages (activated by default).
- **Inactivity** - Check for inactivity (deactivated by default).
- **Moderation Abuse** - KaikOut moderates the moderators.

### Report

- **Logger** - Log messages to CSV files.
- **Moderation Reports** - KaikOut immediately reports to moderators about moderation activities made by other moderators.
- **Self Reports** - KaikOut immediately reports to moderators about its moderation activities.

### Special

- **Remote Management** - KaikOut can be managed in two fashions, publicly (groupchat) and privately (chat).
- **Simultaneous** - KaikOut is designed to handle multiple contacts, including groupchats, Simultaneously.
- **Visual interface** - Interactive interface for XMPP using Ad-Hoc Commands,

## Preview

KaikOut as appears with Cheogram.

<img alt="Chat: Session" src="kaikout/documentation/screenshots/chat_session.jpg" width="200px"/>
<img alt="Ad-Hoc: Commands" src="kaikout/documentation/screenshots/adhoc_commands.jpg" width="200px"/>
<img alt="Ad-Hoc: Edit bookmark" src="kaikout/documentation/screenshots/adhoc_edit.jpg" width="200px"/>
<img alt="Ad-Hoc: Settings" width="200px" src="kaikout/documentation/screenshots/adhoc_settings.jpg"/>

## Getting Started

### Install

It is possible to install KaikOut using pip and pipx.

#### pip inside venv

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install git+https://git.xmpp-it.net/sch/KaikOut
```

#### pipx

##### Install

```
$ pipx install git+https://git.xmpp-it.net/sch/KaikOut
```

##### Update

```
$ pipx uninstall kaikout
$ pipx install git+https://git.xmpp-it.net/sch/KaikOut
```

### Start

Start by executing the command `kaikout` and enter Username and Password of an existing XMPP account.

```
$ kaikout
```

You can also start KaikOut as follows:

```
$ kaikout --jid ACCOUNT_JABBER_ID --password ACCOUNT_PASSWORD
```

It is advised to use a dedicated extra account for KaikOut.

## Recommended Clients

KaikOut works with any XMPP chat client; if you want to make use of the visual interface which KaikOut has to offer (i.e. Ad-Hoc Commands), then you are advised to use [Cheogram](https://cheogram.com), [Converse](https://conversejs.org), [Gajim](https://gajim.org), [monocles chat](https://monocles.chat), [Movim](https://mov.im), [Poezio](https://poez.io), [Profanity](https://profanity-im.github.io), [Psi](https://psi-im.org) or [Psi+](https://psi-plus.com).

### Support

Please join our support groupchat whether you want help, discuss new features or just greet us.

- [Main Groupchat](xmpp:kaikout@chat.woodpeckersnest.space?join) (International)

## Authors

[Schimon](xmpp:sch@pimux.de?message) (Author).

## License

AGPL3 license.

## Copyright

Schimon Jehudah Zackary, 2024
