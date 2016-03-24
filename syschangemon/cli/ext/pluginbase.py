from abc import abstractmethod
from urllib.parse import urlparse

from cement.core.foundation import CementApp
from cement.core.interface import Interface, Attribute
from cement.core.handler import CementBaseHandler
from syschangemon.core.model import State
from syschangemon.core.sessiondiff import SessionDiff


class UnsupportedException(BaseException):
    pass


class StatePluginInterface(Interface):
    class IMeta:
        label = 'state_plugin'

    Meta = Attribute('Handler Meta-data')

    def _setup(app_obj):
        """
        The setup function is called during application initialization and
        must 'setup' the handler object making it ready for the framework
        or the application to make further calls to it.

        Required Arguments:

            app_obj
                The application object.

        Returns: n/a

        """

    def enumerate():
        """
        Enumerate system attributes

        """


class StatePluginBase(CementBaseHandler):
    class Meta:
        interface = StatePluginInterface
        label = 'base'

#    _meta = Meta

    def __init__(self):
        self._meta = self.Meta
        self.app = None

    def setup(self, app_obj):
        self.app = app_obj
        #print("Doing work @ _setup!")

    def list_urls(self):
        return []

    def get_state(self, url):
        raise UnsupportedException

    def process_urls(self, urls):
        return urls

    def process_state(self, state):
        return state

    def process_diff(self, diff):
        return diff

    @property
    def label(self):
        return self._meta.label
