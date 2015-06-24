# -*- coding: utf-8 -*-

"""
High-level interface to the Twack application.

`init_app()` will return a configured Application instance.
"""

from __future__ import division, print_function, unicode_literals

from datetime import datetime, timezone
from os import environ
from os.path import expanduser, join as join_path, curdir
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser, NoSectionError, NoOptionError

import tweepy

from .db import TweetStore

version = "0.0.0"
DEFAULT_DB_URL = 'postgresql://twack:twack@localhost/twack'


class ConfigurationError(Exception):
    """ Exception indicating an application configuration error. """
    pass


class AppConfig(object):
    def __init__(self):
        self._config = None

    @property
    def config(self):
        if self._config is None:
            self._config = ConfigParser()
            self._config.read(self.config_paths())
        return self._config

    @staticmethod
    def config_paths():
        return [
            '/etc/twack.conf',
            expanduser('~/.twack.conf'),
            join_path(curdir, 'twack.conf')
        ]

    def param(self, env_var, config_group, config_key,
              default=None, optional=True):
        """
        Obtain an environment variable.

        Raises a ConfigurationError if optional is False and the environment
        variable has not been defined.
        """
        result = environ.get(env_var)

        if result is None:
            try:
                result = self.config.get(config_group, config_key)
            except (NoSectionError, NoOptionError):
                pass

        if result is None:
            if not optional:
                raise ConfigurationError(
                    "Required configuration is missing. "
                    "The env-var '{key}' or the configuration value "
                    "'{section}.{item}' must be provided.".format(
                        key=env_var, section=config_group, item=config_key)
                )
            else:
                result = default
        return result

    def connection_params(self):
        """
        Obtain database connection parameters from the 'TWACK_DB_URL' env var.
        """
        url_val = self.param('TWACK_DB_URL', 'database', 'url', DEFAULT_DB_URL)
        url = urlparse.urlparse(url_val)

        # Remove any fragments:
        path = url.path[1:]
        path = path.split('?', 2)[0]

        # Handle postgres percent-encoded paths.
        hostname = url.hostname or ''
        if '%2f' in hostname.lower():
            hostname = hostname.replace('%2f', '/').replace('%2F', '/')

        # Gather dsn params:
        params = {
            'database': path or None,
            'user': url.username or None,
            'password': url.password or None,
            'host': hostname or None,
            'port': url.port or None,
        }

        return params

    def twitter_params(self):
        """
        Obtain twitter authentication params from the env vars 'TWITTER
        """
        consumer_key = self.param(
            'TWITTER_CONSUMER_KEY', 'twitter', 'consumer_key',
            optional=False)
        consumer_secret = self.param(
            'TWITTER_CONSUMER_SECRET', 'twitter', 'consumer_secret',
            optional=False)

        return {
            'consumer_key': consumer_key,
            'consumer_secret': consumer_secret,
        }


class Twitter(object):
    """
    Encapsulate a bunch of calls to the Twitter API.
    """

    def __init__(self, params):
        self._consumer_key = params['consumer_key']
        self._consumer_secret = params['consumer_secret']
        self._api = None

    @property
    def api(self):
        """
        A connected Tweepy API object, initialised on first access.
        """
        if self._api is None:
            auth = tweepy.AppAuthHandler(
                self._consumer_key, self._consumer_secret)
            self._api = tweepy.API(auth)
        return self._api

    def profile(self, screen_name):
        """
        Obtain a user's profile.
        """
        return self.api.get_user(screen_name=screen_name)

    def follower_ids(self, screen_name):
        """
        Obtain a user's followers' ids.
        """
        return self.api.followers_ids(screen_name=screen_name)

    def friend_ids(self, screen_name):
        """
        Obtain the ids of all the accounts a user is following on Twitter.
        """
        return self.api.friends_ids(screen_name=screen_name)

    def friends(self, screen_name):
        """
        Obtain full friend instances for each account a user is following
        on Twitter.
        """
        cursor = tweepy.Cursor(self.api.friends, screen_name=screen_name,
                               skip_status=True, include_user_entites=False)
        for friend in cursor.items():
            yield friend


class Application(object):
    """
    High-level interface to Twack application operations.
    """

    def __init__(self, store, twitter):
        self._tweet_store = store
        self._twitter = twitter

    def initdb(self):
        """
        Initialise an empty database with the required schema.
        """
        with self._tweet_store as store:
            store.initdb()

    def blitz(self):
        """
        Destroy an existing Twack schema.
        """
        with self._tweet_store as store:
            store.blitz()

    def load(self, screen_name):
        """
        Load a user's friends and followers from Twitter and store in
        the database.
        """
        twitter_id = self.screen_name_to_id(screen_name)
        followers = self._twitter.follower_ids(screen_name)
        friends = self._twitter.friend_ids(screen_name)
        load_dt = datetime.now(tz=timezone.utc)
        with self._tweet_store as store:
            store.save_load(twitter_id, followers, friends, load_dt)

    def screen_name_to_id(self, screen_name):
        """
        Given a user's screen-name, obtain the associated Twitter ID.
        """
        with self._tweet_store as store:
            account_id = store.get_user_id(screen_name)
            if account_id is None:
                profile = self._twitter.profile(screen_name=screen_name)
                load_dt = datetime.now(tz=timezone.utc)
                store.update_account_info(
                    profile.id, profile.screen_name, load_dt)
                account_id = profile.id
            return account_id


def init_app():
    """
    Obtain an Application object initialised from environment variables.
    """
    app_config = AppConfig()

    tweet_store = TweetStore(app_config.connection_params())
    twitter = Twitter(app_config.twitter_params())

    return Application(tweet_store, twitter)
