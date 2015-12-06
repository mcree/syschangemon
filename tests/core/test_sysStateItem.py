from unittest import TestCase

from SysChangeMon.core.model import SysStateItem


class TestSysStateItem(TestCase):

    def test_init(self):
        i = SysStateItem("file:///etc/passwd")
        self.assertEqual("file", i.scheme)
        self.assertEqual("/etc/passwd", i.path)
