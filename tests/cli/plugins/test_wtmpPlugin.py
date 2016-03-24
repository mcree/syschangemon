import pprint
import struct

from syschangemon.cli.plugins.wtmp import WtmpPlugin, utmp_read
from syschangemon.utils import test

class TestSysInfoPlugin(test.SysChangeMonTestCase):

    def setUp(self):
        super().setUp()
        #self.plugin = WtmpPlugin()
        #self.plugin.setup(self.app)

    def test_read_empty(self):
        for entry in utmp_read(b''):
            pass

    def test_read_fail(self):
        with self.assertRaises(struct.error):
            for entry in utmp_read(b'123'):
                pass
