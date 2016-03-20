from urllib.parse import urlparse

import sys

from binaryornot.check import is_binary
from cement.core import handler, hook
from cement.core.config import IConfig
from cement.core.controller import CementBaseController
from cement.core.foundation import CementApp
from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface, UnsupportedException
import globre

from syschangemon.core.model import Session, State


class ConffilePlugin(StatePluginBase):
    """
    filesystem plugin base class
    """
    class Meta:
        label = 'conffile'
        interface = StatePluginInterface

    def setup(self, app):
        super().setup(app)

        c = app.config

        # get include and exclude list from config file
        self.exclude = c.get(self._meta.label, 'exclude').split('\n')
        self.exclude[:] = [v.strip() for v in self.exclude]  # strip all elements
        self.exclude[:] = [v for v in self.exclude if len(v) != 0]  # throw out empty elements

        self.excludepats = []
        for pat in self.exclude:
            self.excludepats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        self.size_limit = int(c.get(self._meta.label, 'size_limit'))

    def process_state(self, state: State) -> State:
        purl = urlparse(state['url'])
        path = purl.path
        if purl.scheme != 'file':
            return state
        if 'size' in state.keys() and state['size'] is not None:
            if int(state['size']) > self.size_limit:
                self.app.log.debug("%s is above size limit - skipping" % (path))
                return state
        # filter out excludes
        for pat in self.excludepats:
            if pat.match(path):
                self.app.log.debug("%s excluded by %s" % (path, pat))
                return state
        try:
            if is_binary(path):
                self.app.log.debug("%s seems to be binary - skipping" % (path))
                return state
            with open(path, mode='rb') as file:
                state['content'] = file.read()
                #self.app.log.debug("reading conffile contents: %s" % (path))
        except:
            e = sys.exc_info()[1]
            state['content_error'] = e

        return state


def load(app: CementApp):
    handler.register(ConffilePlugin)
