# -*- coding: utf-8 -*-

import unittest
import os
import maildir


class TestCli(unittest.TestCase):
    def setUp(self):
        self.path = os.getcwd() + os.path.sep + 'tests/test-sample.py'

    def test_read_config_file(self):
        self.assertTrue(maildir.cli.read_config_file(self.path))

    def test_valid_config(self):
        self.assertTrue(maildir.cli.valid_config(maildir.cli.read_config_file(self.path)))

    def test_read_sample_config(self):
        self.assertIsNone(maildir.read_sample_config())

