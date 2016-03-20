from unittest import TestCase
from syschangemon.core.model import Model, Session, State


class TestModel(TestCase):
    def setUp(self):
        self.model = Model('sqlite:///:memory:')

    def dump_db(self):
        for line in self.model.db._database.get_conn().iterdump():
            print(line)

    def test_last_session(self):
        print('begin test_last_session')
        self.model.delete()
        self.model.new_session(uuid='a', custom_a='val_a', closed=1).save()
        b = self.model.new_session(uuid='b', closed=1)
        b['custom_b'] = 'val_b'
        b.save()
        c = self.model.last_closed_session()
        self.assertEqual('b', c['uuid'])
        self.assertEqual('val_b', c['custom_b'])
        self.assertIsNone(c['custom_a'])

    def test_state(self):
        print("begin test_state")
        self.model.delete()
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

    def test_all_urls(self):
        print("begin all_urls")
        self.model.delete()
        sess = self.model.new_session()
        sess.save()
        sess.new_state().save()
        sess.new_state().save()
        sess.new_state().save()
        sess.new_state().save()
        self.assertEqual(4, len(sess.all_urls()))

    def test_model_delete(self):
        print("begin model_delete")
        self.model.delete()
        self.model.new_session().save()
        sess = self.model.new_session()
        sess.save()
        sess.new_state().save()
        sess.new_state().save()
        sess.new_state().save()
        sess.new_state().save()
        self.assertEqual(2, len(self.model.find_sessions()))
        self.assertEqual(4, len(sess.all_urls()))
        self.model.delete()
        self.assertEqual(0, len(self.model.find_sessions()))
        self.assertEqual(0, len(sess.all_urls()))

    def test_session_delete(self):
        print("begin session_delete")
        self.model.delete()
        sess1 = self.model.new_session()
        sess1.save()
        sess2 = self.model.new_session()
        sess2.save()
        sess1.new_state().save()
        sess1.new_state().save()
        sess1.new_state().save()
        sess1.new_state().save()
        sess2.new_state().save()
        sess2.new_state().save()
        sess2.new_state().save()
        sess2.new_state().save()
        self.assertEqual(2, len(self.model.find_sessions()))
        self.assertEqual(4, len(sess1.all_urls()))
        self.assertEqual(4, len(sess2.all_urls()))
        sess1.delete()
        self.assertEqual(1, len(self.model.find_sessions()))
        self.assertEqual(0, len(sess1.all_urls()))
        self.assertEqual(4, len(sess2.all_urls()))

    def test_find_states(self):
        print('begin find_states')
        self.model.delete()
        sess = self.model.new_session()
        sess.save()
        sess.new_state(k='v1').save()
        sess.new_state(k='v1').save()
        sess.new_state(k='v2').save()
        sess.new_state(k='v2').save()
        sess.new_state(k='v3').save()
        sess.new_state(k='v3').save()
        self.assertEqual(6, len(sess.all_urls()))
        self.assertEqual(2, len(sess.find_states(k='v1')))
        self.assertIsInstance(sess.find_states(k='v1')[0], State)
