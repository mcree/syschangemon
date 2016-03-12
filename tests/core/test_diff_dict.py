from unittest import TestCase

from core import dictdiff


class TestDiffDict(TestCase):
    def test_diff_dict(self):
        a = {
          'key1': 'value1',
          'key2': 'line1\nline2\nlinea\nline4',
          'key3': 'asdfasdfasfd%0A',
          'keya': 'valuea',
        }
        b = {
          'key1': 'value1',
          'key2': 'line1\nline2\nlineb\nline4',
          'key3': 'sasdfasdfasfd%0A',
          'keyb': 'valueb',
        }
        diff = dictdiff.DictDiff(a, 'array a', b, 'array b')
        print(diff)
        self.assertFalse(diff.is_empty())

    def test_diff_dict_eq(self):
        a = {
          'key1': 'value1',
          'key2': 'line1\nline2\nlinea\nline4',
          'key3': 'asdfasdfasfd%0A',
          'keya': 'valuea',
        }
        b = {
          'key1': 'value1',
          'key2': 'line1\nline2\nlinea\nline4',
          'key3': 'asdfasdfasfd%0A',
          'keya': 'valuea',
        }
        diff = dictdiff.DictDiff(a, 'array a', b, 'array b')
        self.assertTrue(diff.is_empty())

