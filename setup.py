# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="Twack",
    version="0.0.0",
    author="Mark Smith",
    author_email="judy@judy.co.uk",
    description="Track your Twitter follows and followers",
    license="MIT",
    keywords="twitter metrics",
    url="https://www.github.com/judy2k/twack",

    packages=["twacklib"],
    install_requires=[
        "click>=3.3,<4.0",
        "psycopg2>=2.5.4",
        "tweepy>=3.3.0",
    ],
    entry_points=dict(console_scripts=['twack=twacklib.cli:main',]),
    zip_safe=False,
)
