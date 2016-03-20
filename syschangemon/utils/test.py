"""Testing utilities for syschangemon."""
from cement.ext.ext_configparser import ConfigParserConfigHandler

from syschangemon.cli.main import SysChangeMonTestApp, TestConfigHandler
from cement.utils.test import *

from syschangemon.core.model import Model


class TestStorage:
    db = Model('sqlite:///:memory:')


class SysChangeMonTestCase(CementTestCase):
    app_class = SysChangeMonTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(SysChangeMonTestCase, self).setUp()
        self.app.storage = TestStorage()
        self.app.config = TestConfigHandler()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(SysChangeMonTestCase, self).tearDown()

