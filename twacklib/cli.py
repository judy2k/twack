#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import click

from . import init_app, version

@click.group()
@click.version_option()
def main():
    """
    Top-level command.
    """
    pass


@main.command()
def initdb():
    """
    Initialise an empty Twack database.
    """
    click.echo('Init database')
    init_app().initdb()


@main.command()
@click.argument('screen-name')
def load(screen_name):
    """
    Load and store a user's friends and followers from Twitter.
    """
    init_app().load(screen_name)


@main.command()
def blitz():
    """
    Destroy an existing Twack database.
    """
    init_app().blitz()
