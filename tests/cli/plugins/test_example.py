"""Tests for Example Plugin."""

from SysChangeMon.utils import test

class ExamplePluginTestCase(test.SysChangeMonTestCase):
    def test_load_example_plugin(self):
        self.app.setup()
        self.app.plugin.load_plugin('example')
