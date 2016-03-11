from unittest import TestCase
from core.model import Model, Session


class TestModel(TestCase):
    def setUp(self):
        self.model = Model('sqlite:///:memory:')

    def dump_db(self):
        for line in self.model.db._database.get_conn().iterdump():
            print(line)

    def test_last_session(self):
        print('begin test_last_session')
        a = self.model.new_session(uuid='a')
        a['custom_a'] = 'val_a'
        a.save()
        b = self.model.new_session(uuid='b')
        b['custom_b'] = 'val_b'
        b.save()
        c = self.model.last_session()
        #self.dump_db()
        self.assertEqual('b', c['uuid'])
        self.assertEqual('val_b', c['custom_b'])
        self.assertIsNone(c['custom_a'])

    def test_state(self):
        print("begin test_state")
        sess = self.model.new_session()
        a = sess.new_state(url='testurl://testurl')
        a['key_a'] = 'val_a'
        sess.save()
        a.save()
        self.assertEqual('val_a', sess.get_state(a['url'])['key_a'])
        with self.assertRaises(KeyError):
            sess.get_state('nonexistent://url')
        with self.assertRaises(ValueError):
            b = sess.new_state()
            b['sessionid'] = None
            b.save()
        with self.assertRaises(ValueError):
            sess.new_state(url='non url').save()
