#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio import Lock
from kaikout.log import Logger
from sqlite3 import connect, Error, IntegrityError
import os
import sys
import time
import tomli_w
import tomllib

# from eliot import start_action, to_file
# # with start_action(action_type="list_feeds()", db=db_file):
# # with start_action(action_type="last_entries()", num=num):
# # with start_action(action_type="get_feeds()"):
# # with start_action(action_type="remove_entry()", source=source):
# # with start_action(action_type="search_entries()", query=query):
# # with start_action(action_type="check_entry()", link=link):

CURSORS = {}

# aiosqlite
DBLOCK = Lock()

logger = Logger(__name__)


class SQLite:


    def create_connection(db_file):
        """
        Create a database connection to the SQLite database
        specified by db_file.

        Parameters
        ----------
        db_file : str
            Path to database file.
    
        Returns
        -------
        conn : object
            Connection object or None.
        """
        time_begin = time.time()
        function_name = sys._getframe().f_code.co_name
        message_log = '{}'
        logger.debug(message_log.format(function_name))
        conn = None
        try:
            conn = connect(db_file)
            conn.execute("PRAGMA foreign_keys = ON")
            # return conn
        except Error as e:
            logger.warning('Error creating a connection to database {}.'.format(db_file))
            logger.error(e)
        time_end = time.time()
        difference = time_end - time_begin
        if difference > 1: logger.warning('{} (time: {})'.format(function_name,
                                                                 difference))
        return conn


    def create_tables(db_file):
        """
        Create SQLite tables.

        Parameters
        ----------
        db_file : str
            Path to database file.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {}'
                    .format(function_name, db_file))
        with SQLite.create_connection(db_file) as conn:
            activity_table_sql = (
                """
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER NOT NULL,
                    stanza_id TEXT,
                    alias TEXT,
                    jid TEXT,
                    body TEXT,
                    thread TEXT,
                    PRIMARY KEY ("id")
                  );
                """
                )
            filters_table_sql = (
                """
                CREATE TABLE IF NOT EXISTS filters (
                    id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY ("id")
                  );
                """
                )
            outcast_table_sql = (
                """
                CREATE TABLE IF NOT EXISTS outcast (
                    id INTEGER NOT NULL,
                    alias TEXT,
                    jid TEXT,
                    reason TEXT,
                    PRIMARY KEY ("id")
                  );
                """
                )
            settings_table_sql = (
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value INTEGER,
                    PRIMARY KEY ("id")
                  );
                """
                )
            cur = conn.cursor()
            # cur = get_cursor(db_file)
            cur.execute(activity_table_sql)
            cur.execute(filters_table_sql)
            cur.execute(outcast_table_sql)
            cur.execute(settings_table_sql)


    def get_cursor(db_file):
        """
        Allocate a cursor to connection per database.

        Parameters
        ----------
        db_file : str
            Path to database file.
    
        Returns
        -------
        CURSORS[db_file] : object
            Cursor.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {}'
                    .format(function_name, db_file))
        if db_file in CURSORS:
            return CURSORS[db_file]
        else:
            with SQLite.create_connection(db_file) as conn:
                cur = conn.cursor()
                CURSORS[db_file] = cur
        return CURSORS[db_file]


    async def import_feeds(db_file, feeds):
        """
        Insert a new feed into the feeds table.

        Parameters
        ----------
        db_file : str
            Path to database file.
        feeds : list
            Set of feeds (Title and URL).
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {}'
                    .format(function_name, db_file))
        async with DBLOCK:
            with SQLite.create_connection(db_file) as conn:
                cur = conn.cursor()
                for feed in feeds:
                    logger.debug('{}: feed: {}'
                                .format(function_name, feed))
                    url = feed['url']
                    title = feed['title']
                    sql = (
                        """
                        INSERT
                        INTO feeds_properties(
                            title, url)
                        VALUES(
                            ?, ?)
                        """
                        )
                    par = (title, url)
                    try:
                        cur.execute(sql, par)
                    except IntegrityError as e:
                        logger.warning("Skipping: " + str(url))
                        logger.error(e)


    async def add_metadata(db_file):
        """
        Insert a new feed into the feeds table.

        Parameters
        ----------
        db_file : str
            Path to database file.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {}'
                    .format(function_name, db_file))
        async with DBLOCK:
            with SQLite.create_connection(db_file) as conn:
                cur = conn.cursor()
                sql = (
                    """
                    SELECT id
                    FROM feeds_properties
                    ORDER BY id ASC
                    """
                    )
                ixs = cur.execute(sql).fetchall()
                for ix in ixs:
                    feed_id = ix[0]
                    # Set feed status
                    sql = (
                        """
                        INSERT
                        INTO feeds_state(
                            feed_id)
                        VALUES(
                            ?)
                        """
                        )
                    par = (feed_id,)
                    try:
                        cur.execute(sql, par)
                    except IntegrityError as e:
                        logger.warning(
                            "Skipping feed_id {} for table feeds_state".format(feed_id))
                        logger.error(e)
                    # Set feed preferences.
                    sql = (
                        """
                        INSERT
                        INTO feeds_preferences(
                            feed_id)
                        VALUES(
                            ?)
                        """
                        )
                    par = (feed_id,)
                    try:
                        cur.execute(sql, par)
                    except IntegrityError as e:
                        logger.warning(
                            "Skipping feed_id {} for table feeds_preferences".format(feed_id))
                        logger.error(e)


    async def insert_feed(db_file, url, title, identifier, entries=None, version=None,
                          encoding=None, language=None, status_code=None,
                          updated=None):
        """
        Insert a new feed into the feeds table.

        Parameters
        ----------
        db_file : str
            Path to database file.
        url : str
            URL.
        title : str
            Feed title.
        identifier : str
            Feed identifier.
        entries : int, optional
            Number of entries. The default is None.
        version : str, optional
            Type of feed. The default is None.
        encoding : str, optional
            Encoding of feed. The default is None.
        language : str, optional
            Language code of feed. The default is None.
        status : str, optional
            HTTP status code. The default is None.
        updated : ???, optional
            Date feed was last updated. The default is None.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {} url: {}'
                    .format(function_name, db_file, url))
        async with DBLOCK:
            with SQLite.create_connection(db_file) as conn:
                cur = conn.cursor()
                sql = (
                    """
                    INSERT
                    INTO feeds_properties(
                        url, title, identifier, entries, version, encoding, language, updated)
                    VALUES(
                        ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    )
                par = (url, title, identifier, entries, version, encoding, language, updated)
                cur.execute(sql, par)
                sql = (
                    """
                    SELECT id
                    FROM feeds_properties
                    WHERE url = :url
                    """
                    )
                par = (url,)
                feed_id = cur.execute(sql, par).fetchone()[0]
                sql = (
                    """
                    INSERT
                    INTO feeds_state(
                        feed_id, status_code, valid)
                    VALUES(
                        ?, ?, ?)
                    """
                    )
                par = (feed_id, status_code, 1)
                cur.execute(sql, par)
                sql = (
                    """
                    INSERT
                    INTO feeds_preferences(
                        feed_id)
                    VALUES(
                        ?)
                    """
                    )
                par = (feed_id,)
                cur.execute(sql, par)


    async def remove_feed_by_url(db_file, url):
        """
        Delete a feed by feed URL.

        Parameters
        ----------
        db_file : str
            Path to database file.
        url : str
            URL of feed.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {} url: {}'
                    .format(function_name, db_file, url))
        with SQLite.create_connection(db_file) as conn:
            async with DBLOCK:
                cur = conn.cursor()
                sql = (
                    """
                    DELETE
                    FROM feeds_properties
                    WHERE url = ?
                    """
                    )
                par = (url,)
                cur.execute(sql, par)


    async def remove_feed_by_index(db_file, ix):
        """
        Delete a feed by feed ID.

        Parameters
        ----------
        db_file : str
            Path to database file.
        ix : str
            Index of feed.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {} ix: {}'
                    .format(function_name, db_file, ix))
        with SQLite.create_connection(db_file) as conn:
            async with DBLOCK:
                cur = conn.cursor()
                # # NOTE Should we move DBLOCK to this line? 2022-12-23
                # sql = (
                #     "DELETE "
                #     "FROM entries "
                #     "WHERE feed_id = ?"
                #     )
                # par = (url,)
                # cur.execute(sql, par) # Error? 2024-01-05
                # sql = (
                #     "DELETE "
                #     "FROM archive "
                #     "WHERE feed_id = ?"
                #     )
                # par = (url,)
                # cur.execute(sql, par)
                sql = (
                    """
                    DELETE
                    FROM feeds_properties
                    WHERE id = ?
                    """
                    )
                par = (ix,)
                cur.execute(sql, par)


    def get_feeds_by_tag_id(db_file, tag_id):
        """
        Get feeds of given tag.
    
        Parameters
        ----------
        db_file : str
            Path to database file.
        tag_id : str
            Tag ID.

        Returns
        -------
        result : tuple
            List of tags.
        """
        function_name = sys._getframe().f_code.co_name
        logger.debug('{}: db_file: {} tag_id: {}'
                    .format(function_name, db_file, tag_id))
        with SQLite.create_connection(db_file) as conn:
            cur = conn.cursor()
            sql = (
                """
                SELECT feeds_properties.*
                FROM feeds_properties
                INNER JOIN tagged_feeds ON feeds_properties.id = tagged_feeds.feed_id
                INNER JOIN tags ON tags.id = tagged_feeds.tag_id
                WHERE tags.id = ?
                ORDER BY feeds_properties.title;
                """
                )
            par = (tag_id,)
            result = cur.execute(sql, par).fetchall()
            return result


class Toml:


    def instantiate(self, room):
        """
        Callback function to instantiate action on database.

        Parameters
        ----------
        jid_file : str
            Filename.
        callback : ?
            Function name.
        message : str, optional
            Optional kwarg when a message is a part or
            required argument. The default is None.

        Returns
        -------
        object
            Coroutine object.
        """
        data_dir = Toml.get_default_data_directory()
        if not os.path.isdir(data_dir):
            os.mkdir(data_dir)
        if not os.path.isdir(data_dir + "/toml"):
            os.mkdir(data_dir + "/toml")
        filename = os.path.join(data_dir, "toml", r"{}.toml".format(room))
        if not os.path.exists(filename):
            Toml.create_settings_file(self, filename)
        Toml.load_jid_settings(self, room, filename)
        return filename


    def get_default_data_directory():
        if os.environ.get('HOME'):
            data_home = os.path.join(os.environ.get('HOME'), '.local', 'share')
            return os.path.join(data_home, 'kaikout')
        elif sys.platform == 'win32':
            data_home = os.environ.get('APPDATA')
            if data_home is None:
                return os.path.join(
                    os.path.dirname(__file__) + '/kaikout_data')
        else:
            return os.path.join(os.path.dirname(__file__) + '/kaikout_data')


    def get_data_file(data_dir, room):
        toml_file = os.path.join(data_dir, "toml", r"{}.toml".format(room))
        return toml_file


    def create_settings_file(self, filename):
        data = self.defaults
        content = tomli_w.dumps(data)
        with open(filename, 'w') as f: f.write(content)


    def load_jid_settings(self, room, filename):
        # data_dir = Toml.get_default_data_directory()
        # filename = Toml.get_data_file(data_dir, room)
        with open(filename, 'rb') as f: self.settings[room] = tomllib.load(f)


    def update_jid_settings(self, room, filename, key, value):
        with open(filename, 'rb') as f: data = tomllib.load(f)
        self.settings[room][key] = value
        data = self.settings[room]
        content = tomli_w.dumps(data)
        with open(filename, 'w') as f: f.write(content)

