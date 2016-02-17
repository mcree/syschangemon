"""Filesystem Plugin for syschangemon."""

from cement.core import handler, hook
from cement.core.config import IConfig
from cement.core.controller import CementBaseController
from cement.core.foundation import CementApp


def enumerate(app):
    app.log.debug('in enumerate')
    # do something with the ``app`` object here.
    c = app.config
    app.log.debug(c.get_sections())
    app.log.debug(c.keys('files'))
    app.log.debug(c.get('files', 'include'))
    app.log.debug(c.get('files', 'exclude'))
    pass


def load(app: CementApp):
    app.log.debug('in load')
    hook.register('enumerate', enumerate)

    # register the plugin class.. this only happens if the plugin is enabled
    #handler.register(ExamplePluginController)
