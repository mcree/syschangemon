"""Testing utilities for syschangemon."""
from cement.core import log
from cement.core.log import CementLogHandler
from cement.ext.ext_configparser import ConfigParserConfigHandler

from syschangemon.cli.main import SysChangeMonTestApp, TestConfigHandler
from cement.utils.test import *

from syschangemon.core.model import Model


class TestStorage:
    db = Model('sqlite:///:memory:')


class TestLogHandler:
    class Meta:
        interface = log.ILog
        label = 'test_log_handler'

    def _setup(self, app_obj):
        pass

    def set_level(self):
        pass

    def get_level(self):
        """Return a string representation of the log level."""
        return "DEBUG"

    def info(self, msg):
        """
        Log to the 'INFO' facility.

        :param msg: The message to log.

        """
        print(msg)

    def warn(self, msg):
        """
        Log to the 'WARN' facility.

        :param msg: The message to log.

        """
        print(msg)

    def error(self, msg):
        """
        Log to the 'ERROR' facility.

        :param msg: The message to log.

        """
        print(msg)

    def fatal(self, msg):
        """
        Log to the 'FATAL' facility.

        :param msg: The message to log.

        """
        print(msg)

    def debug(self, msg):
        """
        Log to the 'DEBUG' facility.

        :param msg: The message to log.

        """
        print(msg)


class SysChangeMonTestCase(CementTestCase):
    app_class = SysChangeMonTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(SysChangeMonTestCase, self).setUp()
        self.app.storage = TestStorage()
        self.app.config = TestConfigHandler()
        self.app.log = TestLogHandler()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(SysChangeMonTestCase, self).tearDown()

