# -*- coding: utf-8 -*-

import datetime
from time import sleep
import os
import re
import imaplib
import email
import mailbox
import sqlite3
import logging


__all__ = ['SSLEmail', 'IMAP4_MESSAGE']


class IMAP4_MESSAGE:
    OK = u'OK'
    SELECTED = u'SELECTED'


class SSLEmail(object):
    """
    Email class to fetch the email from the server.
    """
    def __init__(self, config):
        """
        username, password, host, keyfile=None, certfile=None, port=993, service='local'
        :param username unicode: username of the email like maildir@gmail.com.
        :param password unicode: password of the email account.
        :param host unicode
        :param port integer: port of connect to
        """
        for key in config:
            setattr(self, key, config[key])
        self.logger_name = "mail_backup_%s" % self.service
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.fh = logging.FileHandler('mail_backup_%s.log' % self.service)
        self.fh.setLevel(logging.INFO)
        frmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.fh.setFormatter(frmt)
        self.logger.addHandler(self.fh)
        self.db = "mail_backup_%s.db" % self.service
        self.port = 993 or self.port
        self.certfile = None or self.certfile if hasattr(self, 'certfile') else None
        self.keyfile = None or self.keyfile if hasattr(self, 'keyfile') else None
        self.mail = imaplib.IMAP4_SSL('imap.gmail.com', keyfile=self.keyfile, certfile=self.certfile)
        self.list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
        self.dirs = ['new', 'cur', 'tmp', 'attachments']
        self.logger.info("Backup{ username: %s, service: %s}" % (self.username, self.service))
        self.create_db()

    def create_db(self):
        con = sqlite3.connect(self.db)
        with con:
            cur = con.cursor()
            try:
                cur.execute("create table Mail(id UnicodeText, created_at DateTime)")
                self.logger.info("Mail table created")
            except sqlite3.OperationalError:
                pass

    def mail_exists(self, mail_id):
        con = sqlite3.connect(self.db)
        with con:
            cur = con.cursor()
            try:
                cur.execute("select id from Mail where id=:id", {"id": mail_id})
                if cur.fetchone():
                    return True
                return False
            except sqlite3.ProgrammingError:
                return True

    def add_to_mail_table(self, mail_id):
        con = sqlite3.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute("""insert into Mail(id, created_at) values(:id, :datetime)""", {"id": unicode(mail_id), "datetime": datetime.datetime.now()})
            self.logger.info("inserted %s " % mail_id)
            con.commit()

    def create_directories(self, path=None, dirs=None):
        path = path or self.path
        if path.endswith(os.path.sep):
            path = path + self.username
        else:
            path = path + os.path.sep + self.username
        self.path = path
        if not os.path.exists(path):
            os.mkdir(path)
            self.logger.info("directory %s created" % path)
        for directory in dirs or self.dirs:
            p = path + os.path.sep + directory
            if not os.path.exists(p):
                os.mkdir(p)
                self.logger.info("directory %s created" % path)

    def connect(self):
        # conenct to IMAP4 server
        r = self.mail.login(self.username, self.password)
        if r[0] == IMAP4_MESSAGE.OK:
            self.logged_in = True
        else:
            self.logged_in = False

    def extract_mail_box(self, line):
        """
        Given a line, extract mailbox name
        """
        flags, delimiter, mailbox_name = self.list_response_pattern.match(line).groups()
        mailbox_name = mailbox_name.strip('"')
        self.logger.info("%s selected" % (mailbox_name))
        return (flags, delimiter, mailbox_name)

    def fetch_lists(self):
        """
        Get all lists from server and extract mailbox name.
        """
        self.raw_lists = self.mail.list()
        self.mailboxes = []
        for l in self.raw_lists[1]:
            r = self.extract_mail_box(l)
            self.logger.info("list: %s selected" % (r[-1]))
            self.mailboxes.append(r[-1])

    def select_mailbox(self, mailbox, readyonly=True):
        """
        Select mailbox
        """
        r = self.mail.select(mailbox, readyonly)
        if r[0] == IMAP4_MESSAGE.OK:
            self.current_mailbox = mailbox
        else:
            try:
                self.mailboxes.remove(mailbox)
            except ValueError:
                pass
            self.current_mailbox = None

    def fetch_details(self):
        """
        Fetch all mail details
        """
        if self.current_mailbox:
            res, data = self.mail.search(None, "ALL")
            return (res, data)
        return None

    def fetch(self, mail_id):
        """
        Fetch email from server.
        """
        result, data = self.mail.fetch(mail_id, "(RFC822)")
        for d in data:
            if isinstance(d, tuple):
                msg = email.message_from_string(d[1])
                return msg
        return None

    def save_to_disk(self, msg, path=None):
        """
        If service is local create maildir
        """
        mdir = mailbox.Maildir(path or self.path)
        m = mailbox.MaildirMessage(msg)
        #m.set_payload()
        params = msg.get_params()
        if params:
            if not self.mail_exists(params[-1][-1]):
                mdir.add(m)
                self.add_to_mail_table(params[-1][-1])

    def has_attachment(self, msg):
        for part in msg.walk():
            if part.get('Content-Disposition'):
                return True
        return False

    def get_attachment(self, msg):
        attachments = {}
        for part in msg.walk():
            if part.get('Content-Disposition'):
                k = part.get('X-Attachment-Id', 'X-') + "-" + part.get('Content-Disposition')
                if not k in attachments:
                    attachments[k] = part.get_payload(decode=True)
        return attachments

    def store_attachment(self, name, content, path=None):
        name = name[0:100]
        if not self.mail_exists(name):
            with open(os.path.join(path or self.path, u'attachments', u'attachments-' + name), 'wb') as f:
                f.write(content)
                self.add_to_mail_table(name)
                self.logger.info("attachment saved %s" % name)

    def run_forever(self):
        """
        From this point onwards this method runs till the program is killed.
        """
        # Connect
        try:
            self.create_directories()
            if not self.mail.state == IMAP4_MESSAGE.SELECTED:
                self.connect()
            # Get all mailboxes
            self.fetch_lists()
            # Get All mailboxes
            for m in self.mailboxes:
                self.select_mailbox(m)
                r = self.fetch_details()
                if r:
                    #Get Message ids
                    ids = r[1][0].split()
                    for mail_id in ids:
                        msg = self.fetch(mail_id[:100])
                        #Store Email body
                        if msg and self.service:
                            self.save_to_disk(msg)
                        #Store Attachments
                        if self.has_attachment(msg):
                            attachments = self.get_attachment(msg)
                            for item in attachments:
                                self.store_attachment(item, attachments[item])
                        

            #sleep(60)
            try:
                self.mail.close()
            except:
                pass
            self.mail.logout()

        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Shutting down because of KeyboardInterrupt or SystemExit")
