# -*- coding: utf-8 -*-

from setuptools import setup

requirements = open('requirements/_base.txt').read().splitlines()
print(type(requirements[0]))

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
    scripts=['twack'],
    install_requires=requirements
)
