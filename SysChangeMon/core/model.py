""" System Change Data Model Classes """

from datetime import datetime, date
from uuid import uuid4
from decimal import Decimal
from peewee import BlobField, OperationalError
from playhouse.dataset import DataSet
from playhouse.dataset import Table


class MyDataSet(DataSet):
    def __getitem__(self, table):
        return MyTable(self, table, self._models.get(table))


class MyTable(Table):
    def _guess_field_type(self, value):
        #print(type(value))
        if isinstance(value, bytes):
            return BlobField
        return super()._guess_field_type(value)

    def insert(self, **data):
        new_keys = set(data) - set(self.model_class._meta.fields)
        res = super().insert(**data)
        for key in new_keys:
            if isinstance(data[key], (str, int, date, datetime, Decimal)) or data[key] is True or data[key] is False:
                #print("indexing %s" % key)
                try:
                    self.create_index([key])
                except OperationalError:
                    pass
        return res

    def upsert(self, columns=None, conjunction=None, **data):
        query = {}
        cols = set(columns) & set(self.model_class._meta.fields)
        if len(cols) != len(set(columns)):
            return self.insert(**data)
        for col in cols:
            query[col] = data[col]
        res = self.find(**query)
        if len(res) > 0:
            return self.update(columns, conjunction, **data)
        else:
            return self.insert(**data)


class Model:
    def __init__(self, db_uri="sqlite:///:memory:"):
        self._db = MyDataSet(db_uri)
        self._sessions = self._db['sessions']

    def create_session(self, uuid=str(uuid4()), stamp=datetime.now()):
        session = {'uuid': uuid, 'stamp': stamp}
        self._sessions.insert(**session)
        return session

    def last_session(self):
        uuid = self._db.query('select uuid from sessions order by stamp desc').fetchone()
        return self._sessions.find_one(uuid = uuid)
