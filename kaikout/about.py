#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Documentation:

    def about():
        return ('KaikOut'
                '\n'
                'KaikOut - Kaiko Out group chat anti-spam and moderation bot.'
                'Spam has never been in fashion.'
                '\n\n'
                'KaikOut is an XMPP bot that suprvises group chat activity '
                'and assists in blocking and preventing of unsolicited type '
                'of messages.'
                '\n\n'
                'KaikOut is a portmanteau of Kaiko and Out'
                '\n'
                'Kaiko (懐古) translates from Japanese to "Old-Fashioned"'
                '\n\n'
                'https://git.xmpp-it.net/sch/Kaikout'
                '\n\n'
                'Copyright 2024 Schimon Jehudah Zackary'
                '\n\n'
                'Made in Switzerland'
                '\n\n'
                '🇨🇭️')

    def commands():
        return ("add URL [tag1,tag2,tag3,...]"
                "\n"
                " Bookmark URL along with comma-separated tags."
                "\n\n"
                "mod name <ID> <TEXT>"
                "\n"
                " Modify bookmark title."
                "\n"
                "mod note <ID> <TEXT>"
                "\n"
                " Modify bookmark description."
                "\n"
                "tag [+|-] <ID> [tag1,tag2,tag3,...]"
                "\n"
                " Modify bookmark tags. Appends or deletes tags, if flag tag "
                "is preceded by \'+\' or \'-\' respectively."
                "\n"
                "del <ID> or <URL>"
                "\n"
                " Delete a bookmark by ID or URL."
                "\n"
                "\n"
                "id <ID>"
                "\n"
                " Print a bookmark by ID."
                "\n"
                "last"
                "\n"
                " Print most recently bookmarked item."
                "\n"
                "tag <TEXT>"
                "\n"
                " Search bookmarks of given tag."
                "\n"
                "search <TEXT>"
                "\n"
                " Search bookmarks by a given search query."
                "\n"
                "search any <TEXT>"
                "\n"
                " Search bookmarks by a any given keyword."
                # "\n"
                # "regex"
                # "\n"
                # " Search bookmarks using Regular Expression."
                "\n")

    def notice():
        return ('Copyright 2024 Schimon Jehudah Zackary'
                '\n\n'
                'Permission is hereby granted, free of charge, to any person '
                'obtaining a copy of this software and associated '
                'documentation files (the “Software”), to deal in the '
                'Software without restriction, including without limitation '
                'the rights to use, copy, modify, merge, publish, distribute, '
                'sublicense, and/or sell copies of the Software, and to '
                'permit persons to whom the Software is furnished to do so, '
                'subject to the following conditions:'
                '\n\n'
                'The above copyright notice and this permission notice shall '
                'be included in all copies or substantial portions of the '
                'Software.'
                '\n\n'
                'THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY '
                'KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE '
                'WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR '
                'PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR '
                'COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER '
                'LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR '
                'OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE '
                'SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.')

