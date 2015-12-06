"""syschangemon bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as SysChangeMonBaseController.

from cement.core import handler
from SysChangeMon.cli.controllers.base import SysChangeMonBaseController

def load(app):
    handler.register(SysChangeMonBaseController)
