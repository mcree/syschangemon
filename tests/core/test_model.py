import pprint
from inspect import getmembers
from unittest import TestCase

import core.model
from pony.orm.core import db_session


class TestModel(TestCase):
    def setUp(self):
        print('setup')
        self.db = core.model.define_model('sqlite', ':memory:', create_db=True)

    @db_session
    def test_set(self):
        print('test_set')
        s = self.db.Session()
        print(s)
        ss = self.db.StoredState(session=s, uri="dummy://")
#        print(ss)
        ss.meta.add(self.db.StateMetaStr(state=ss, key="a", str_value="b"))
        ss.meta.add(self.db.StateMetaStr(state=ss, key="b", str_value="c"))
        print(ss.meta.count())
        for m in ss.meta:
            print(m)
#        print(ss.meta.aaa)