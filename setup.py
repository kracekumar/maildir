#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from maildir import __version__

setup(
    name='maildir',
    license='BSD',
    version=__version__,
    description='maildir implementation in python',
    author=u'Kracekumar Ramaraju',
    author_email='me@kracekumar.com, kracethekingmaker@gmail.com',
    url='http://github.com/kracekumar/maildir',
    packages=find_packages(),
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
    install_requires=['gevent'],
    entry_points={
        'console_scripts': [
            'maildir = maildir.cli:main',
        ]
    }
)
