"""Testing utilities for syschangemon."""

from syschangemon.cli.main import SysChangeMonTestApp
from cement.utils.test import *

class SysChangeMonTestCase(CementTestCase):
    app_class = SysChangeMonTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(SysChangeMonTestCase, self).setUp()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(SysChangeMonTestCase, self).tearDown()

