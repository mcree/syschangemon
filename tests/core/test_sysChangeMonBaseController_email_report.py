import smtplib
from email.mime.multipart import MIMEMultipart

from minimock import Mock

from syschangemon.cli.controllers.base import SysChangeMonBaseController
from syschangemon.cli.main import TestConfigHandler
from syschangemon.core.jinjaoutput import JinjaOutputHandler
from syschangemon.core.model import Model
from syschangemon.utils import test


class TestSysChangeMonBaseController(test.SysChangeMonTestCase):

    def setUp(self):
        super(TestSysChangeMonBaseController, self).setUp()
        self.controller = SysChangeMonBaseController()
        self.controller._setup(self.app)
        self.set_config()
        self.app.handler.register(JinjaOutputHandler)

    def set_config(self):
        cnf = self.app.config
        assert isinstance(cnf, TestConfigHandler)
        cnf.add_section('syschangemon')
        cnf.set('syschangemon', 'mail_handler', 'smtp')
        cnf.add_section('mail.smtp')
        cnf.set('mail.smtp', 'host', 'localhost')
        cnf.set('mail.smtp', 'port', '25')
        cnf.set('mail.smtp', 'from', 'from@example.com')
        cnf.set('mail.smtp', 'from_addr', 'from@example.com')
        cnf.set('mail.smtp', 'to_addr', 'erno@rigo.info')
        cnf.set('mail.smtp', 'cc', 'cc@example.com')
        cnf.set('mail.smtp', 'bcc', 'bcc@example.com')
        cnf.set('mail.smtp', 'subject', 'test subject {{ is_empty }}')
        cnf.set('mail.smtp', 'subject_prefix', 'prefix')
        cnf.set('mail.smtp', 'ssl', '0')
        cnf.set('mail.smtp', 'tls', '0')
        cnf.set('mail.smtp', 'timeout', '30')
        cnf.set('mail.smtp', 'auth', '0')
        cnf.set('mail.smtp', 'username', 'dummy')
        cnf.set('mail.smtp', 'password', 'dummy')

    def fill_db(self):
        db = self.app.storage.db
        assert isinstance(db, Model)
        db.delete()  # reset db
        rep = db.new_report()
        rep['text'] = 'report text'
        rep['html'] = '<html><body>report html</body></html>'
        rep['is_empty'] = False
        rep.save()

    def getmsg(self, msg):
        self.msg = msg

    def test_email_report(self):
        self.fill_db()
        smtplib.SMTP = Mock('smtplib.SMTP')
        conn = Mock('smtp_connection')
        conn.send_message = Mock('send_message', returns_func=self.getmsg)
        smtplib.SMTP.mock_returns = conn
        self.controller.email_report()
        msg = self.msg
        self.assertIsInstance(msg, MIMEMultipart)
        assert isinstance(msg, MIMEMultipart)
        self.assertEqual(msg["Subject"], 'test subject 0')
