import pprint

from syschangemon.cli.plugins.sysinfo import SysInfoPlugin
from syschangemon.utils import test


class TestSysInfoPlugin(test.SysChangeMonTestCase):

    def setUp(self):
        super().setUp()
        self.plugin = SysInfoPlugin()
        self.plugin.setup(self.app)

    def test_list_urls(self):
        self.assertListEqual(self.plugin.list_urls(), ['sysinfo://'])

    def test_get_state(self):
        res = self.plugin.get_state('sysinfo://')
        pprint.pprint(res)