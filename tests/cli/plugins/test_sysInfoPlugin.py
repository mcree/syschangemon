import pprint

from syschangemon.utils import test


class TestSysInfoPlugin(test.SysChangeMonTestCase):

    def setUp(self):
        super().setUp()
        self.app.setup()
        self.app.plugin.load_plugin('sysinfo')
        plugin = self.app.handler.get('state_plugin', 'sysinfo')()
        plugin.setup(self.app)
        self.plugin = plugin

    def test_list_urls(self):
        self.assertListEqual(self.plugin.list_urls(), ['sysinfo://'])

    def test_get_state(self):
        res = self.plugin.get_state('sysinfo://')
        pprint.pprint(res)