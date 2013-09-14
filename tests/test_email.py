# -*- coding: utf-8 -*-

import unittest
import os
import maildir


class TestMail(unittest.TestCase):
    def setUp(self):
        self.path = os.getcwd() + os.path.sep + 'tests/config.py'
        self.config = maildir.cli.read_config_file(self.path)
        self.emails = [maildir.mail.SSLEmail(c['username'], c['password'], c['host']) for c in self.config.config]
        self.emails[0].connect()

    def testEmailObject(self):
        self.assertIsInstance(self.emails[0], maildir.mail.SSLEmail)

    def testAuthentication(self):
        self.assertTrue(self.emails[0].logged_in)

    def test_fetch_lists(self):
        self.emails[0].fetch_lists()
        self.assertTrue(len(self.emails[0].mailboxes) > 1)

    def test_fetch_mails(self):
        self.emails[0].fetch_lists()
        mb = self.emails[0].mailboxes[0]
        print self.emails[0].mailboxes
        self.emails[0].select_mailbox(mb)
        res, data = self.emails[0].fetch_mails()
        print res, data

