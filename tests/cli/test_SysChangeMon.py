"""CLI tests for SysChangeMon."""
from cement.core.config import IConfig

from SysChangeMon.utils import test


class CliTestCase(test.SysChangeMonTestCase):
    def test_SysChangeMon_cli(self):
        self.app.setup()
        self.app.run()
        self.app.close()
