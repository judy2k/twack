#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data storage interface for the Twack application.
"""

from __future__ import division, print_function, unicode_literals
from collections import namedtuple

from os.path import abspath, dirname, join as join_path

import psycopg2


SQL_DIR = abspath(join_path(dirname(__file__), 'sql'))

Load = namedtuple(
    'Load', ['account_id', 'followers', 'friends', 'added_dt']
)


Event = namedtuple(
    'Event',
    ['subject_id', 'verb', 'object_id', 'event_start_dt', 'event_end_dt'],
)


def _load_sql(key):
    """
    Load sql from the twacklib.sql data sub-package.
    """
    path = join_path(SQL_DIR, '{key}.sql'.format(key=key))
    with open(path, 'r') as sql_file:
        return sql_file.read()


class TweetStore(object):
    """
    Interface to Twack's persistent storage.

    Should be used as a context-manager with the `with` statement, which avoids
    having to call `commit` explicitly.
    """

    def __init__(self, connection_params):
        self._connection_params = connection_params
        self.__conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()

    def commit(self):
        """
        If a connection has been opened, call `commit` on it.
        """
        if self.__conn:
            self._conn.commit()

    @property
    def _conn(self):
        """
        A connection to the Twack PostgreSQL database.
        """
        if self.__conn is None:
            self.__conn = psycopg2.connect(**self._connection_params)
        return self.__conn

    def initdb(self):
        """
        Initialise an empty database.
        """
        with self._conn.cursor() as cursor:
            cursor.execute(_load_sql('initdb'))

    def blitz(self):
        """
        Destroy an existing Twack database.
        """
        with self._conn.cursor() as cursor:
            cursor.execute(_load_sql('blitz'))

    def get_user_id(self, screen_name):
        """
        Obtain a Twitter user-id for a given screen-name.

        Returns `None` if the information is not available.
        """
        with self._conn.cursor() as cursor:
            cursor.execute(
                """ SELECT id FROM twitter_account WHERE screen_name = %s """,
                (screen_name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

    def update_account_info(self, user_id, screen_name, load_dt):
        """
        Update (or insert) a user account record with the provided screen-name.
        """
        with self._conn.cursor() as cursor:
            if self.get_user_id(screen_name) is None:
                # insert
                cursor.execute(
                    """
                    INSERT INTO twitter_account (
                      id, screen_name, added_dt, updated_dt
                    ) VALUES (%s, %s, %s, %s)""",
                    (user_id, screen_name, load_dt, load_dt))
            else:
                # update
                cursor.execute(
                    """
                    UPDATE twitter_account
                      SET screen_name = %s, updated_dt = %s
                      WHERE id = %s
                    """,
                    (screen_name, load_dt, user_id))

    def save_load(self, twitter_id, followers, friends, load_dt):
        """
        Store the provided load information.
        """
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO relationship_load
                  (account_id, followers, friends, added_dt)
                VALUES
                  (%s, %s, %s, %s)
            """, (twitter_id, followers, friends, load_dt))
            # This load may be inserted in between other loads. If so, delete
            # any events that straddle this load, so they can be re-generated.
            cursor.execute(
                """
                DELETE FROM relationship_event WHERE
                  event_start_dt < %(load_dt)s
                  AND
                  event_end_dt > %(load_dt)s""",
                {'load_dt': load_dt})

            # Get previous load:
            cursor.execute(
                """
                SELECT account_id, followers, friends, r_data.added_dt
                  FROM relationship_load r_data
                  INNER JOIN (
                    SELECT MAX(added_dt) added_dt
                      FROM relationship_load
                      WHERE added_dt < %s
                  ) r_filter
                  ON r_filter.added_dt = r_data.added_dt
                """,
                (load_dt,)
            )
            row = cursor.fetchone()
            if row:
                last_load = Load(*row)

                # Create events between previous load and this one:
                for event in events(
                    twitter_id,
                    last_load.added_dt,
                    load_dt,
                    set(last_load.friends),
                    set(friends),
                    set(last_load.followers),
                    set(followers),
                ):
                    cursor.execute("""
                        INSERT INTO relationship_event (
                          subject_id, verb, object_id,
                          event_start_dt, event_end_dt
                        ) VALUES (
                          %(subject_id)s, %(verb)s, %(object_id)s,
                          %(event_start_dt)s, %(event_end_dt)s
                        )
                    """, event._asdict())


def events(account_id, last_load_dt, this_load_dt, last_friends, this_friends,
           last_followers, this_followers):
    new_followers = this_followers - last_followers
    lost_followers = last_followers - this_followers
    new_friends = this_friends - last_friends
    abandoned_friends = last_friends - this_friends
    for new_follower in new_followers:
        yield Event(
            new_follower, 'follow', account_id, last_load_dt, this_load_dt)
    for lost_follower in lost_followers:
        yield Event(
            lost_follower, 'unfollow', account_id,
            last_load_dt, this_load_dt)
    for new_friend in new_friends:
        yield Event(
            account_id, 'follow', new_friend, last_load_dt, this_load_dt)
    for abandoned_friend in abandoned_friends:
        yield Event(
            account_id, 'unfollow', abandoned_friend,
            last_load_dt, this_load_dt)
