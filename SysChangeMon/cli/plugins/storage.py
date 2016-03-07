from cement.core import hook

import os

import core.model
from peewee import BlobField
from playhouse.dataset import DataSet
from playhouse.dataset import Table

class MyDataSet(DataSet):
    def __getitem__(self, table):
        return MyTable(self, table, self._models.get(table))

class MyTable(Table):
    def _guess_field_type(self, value):
        print(type(value))
        if isinstance(value, bytes):
            return BlobField
        return super()._guess_field_type(value)

    def upsert(self, columns=None, conjunction=None, **data):
        # TODO
        pass


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
