from unittest import TestCase
from core.model import Model


class TestModel(TestCase):
    def setUp(self):
        self.model = Model('sqlite:///:memory:')

    def dump_db(self):
        for line in self.model._db._database.get_conn().iterdump():
            print(line)

    def test_set(self):
        print('begin test_set')
        a = self.model.create_session(uuid='a')
        b = self.model.create_session(uuid='b')
        c = self.model.last_session()
        self.assertEqual('b', c['uuid'])
