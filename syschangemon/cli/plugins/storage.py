import datetime

from decimal import Decimal

from cement.core import hook

import os

from syschangemon.core.model import Model


class Storage():

    def __init__(self, dir, app):
        super(Storage, self).__init__()

        try:
            os.makedirs(dir, 0o700)
        except:
            pass

        dburl = 'sqlite:///'+dir+"/db.sqlite?cache_size=-2000&journal_mode=WAL"

        app.log.debug("opening %s" % (dburl))

        self.db = Model(dburl)


def extend_app(app):
    # get api info from this plugins configuration
    sdir = app.config.get('storage', 'dir')

    # create an api object and authenticate1
    storage = Storage(sdir, app)

    # extend the global app object with an ``storage`` member
    app.extend('storage', storage)


def load(app):
    hook.register('pre_run', extend_app)
