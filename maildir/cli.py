# -*- coding: utf-8 -*-

import argparse
import os
import imp
import gevent
from .mail import SSLEmail


def read_sample_config(filename='sample-config.py'):
    """
    Read the sample config
    """
    filename = os.path.dirname(__file__) + os.path.sep + filename
    try:
        with open(filename) as f:
            for line in f.readlines():
                print(line.split('\n')[0])
    except IOError:
        raise IOError("Sample file not found")


def valid_config(config):
    for item in config.config:
        if not ('username' in item and 'password' in item and 'host' in item and 'service' in item and 'path' in item):
            return False
    return True


def read_config_file(filepath):
    """
    Read configuration file and return details.
    Configuration file should be python file.
    """
    if os.path.exists(filepath):
        filename = os.path.join(filepath)
        if filename.endswith(".py"):
            try:
                d = imp.load_source("config", filepath)
                return d
            except Exception, e:
                raise Exception(e.msg)
    else:
        raise IOError("Path %s doesn't exist" % (filepath))


def main():
    """
    Main entry for command line application
    """
    parser = argparse.ArgumentParser(
        description="Maildir configuration details")
    parser.add_argument('-config', type=unicode, help='config file path which should be python file')
    parser.add_argument('-format', action='store_true', default='py', help='print sample config file')
    args = parser.parse_args()
    if args.config is None and args.format is not True:
        print(parser.format_help())
    elif args.config:
        config = read_config_file(args.config)
        if valid_config(config):
            emails = [SSLEmail(config=c) for c in config.config]
            try:
                # Concurrency
                jobs = [gevent.spawn(email.run_forever) for email in emails]
                gevent.joinall(jobs)
            except (KeyboardInterrupt, SystemExit):
                print("Shutting down")
        else:
            print("config file is out of format")
            print(read_sample_config())
    elif args.format:
        read_sample_config()


if __name__ == "__main__":
    main()

