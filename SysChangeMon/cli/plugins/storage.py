import datetime

from decimal import Decimal

from cement.core import hook

import os
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
            if isinstance(data[key], (str, int, datetime.date, datetime.datetime, Decimal)) or data[key] is True or data[key] is False:
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


class Storage():

    def __init__(self, dir, app):
        super().__init__()

        try:
            os.makedirs(dir, 0o700)
        except:
            pass

        #core.model.db.bind('sqlite', dir+'/db.sqlite', create_db=True)
        #core.model.db.generate_mapping(check_tables=True, create_tables=True)

        #self.db = core.model.db

        dburl = 'sqlite:///'+dir+"/db.sqlite"
        #dburl = 'sqlite:///:memory:'

        app.log.debug("opening %s" % (dburl))

        self.db = MyDataSet(dburl)

        app.log.debug("opened %s" % (self.db))



def extend_app(app):
    # get api info from this plugins configuration
    sdir = app.config.get('storage', 'dir')

    # create an api object and authenticate1
    storage = Storage(sdir, app)

    # extend the global app object with an ``storage`` member
    app.extend('storage', storage)


def load(app):
    hook.register('pre_run', extend_app)
