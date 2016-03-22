import pprint

from syschangemon.cli.main import TestConfigHandler
from syschangemon.cli.plugins.command import CommandPlugin
from syschangemon.utils import test


class TestCommandPlugin(test.SysChangeMonTestCase):

    def setUp(self):
        super().setUp()
        self.set_config()
        self.plugin = CommandPlugin()
        self.plugin.setup(self.app)

    def set_config(self):
        cnf = self.app.config
        assert isinstance(cnf, TestConfigHandler)
        cnf.add_section('command')
        cnf.set('command', 'command.echo', 'echo "stdout value" > /dev/stdout ; echo "stderr value" > /dev/stderr')

    def test_list_urls(self):
        urls = self.plugin.list_urls()
        self.assertListEqual(urls, ['command://echo'])

    def test_get_state(self):
        res = self.plugin.get_state('command://echo')
        self.assertDictEqual(res, {'return_code': 0, 'stderr': 'stderr value\n', 'stdout': 'stdout value\n'})
