from cement.core import hook

import os

from core.model import Model

class Storage():

    def __init__(self, dir, app):
        super().__init__()

        try:
            os.makedirs(dir, 0o700)
        except:
            pass

        Model.db.bind('sqlite', dir+'/db.sqlite', create_db=True)
        Model.db.generate_mapping(check_tables=True, create_tables=True)

        self.db = Model.db

        app.log.debug("opened %s" % (Model.db))


def extend_app(app):
    # get api info from this plugins configuration
    sdir = app.config.get('storage', 'dir')

    # create an api object and authenticate1
    storage = Storage(sdir, app)

    # extend the global app object with an ``storage`` member
    app.extend('storage', storage)


def load(app):
    hook.register('pre_run', extend_app)
