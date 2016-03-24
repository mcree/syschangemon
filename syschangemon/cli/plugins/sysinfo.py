"""SysInfo Plugin for syschangemon."""
import platform
import socket
from urllib.parse import urlparse

import sys

from cement.core import handler
from cement.core.foundation import CementApp
from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface, UnsupportedException

from tzlocal.unix import get_localzone


class SysInfoPlugin(StatePluginBase):
    """
    system information plugin base class
    """
    class Meta:
        label = 'sysinfo'
        interface = StatePluginInterface

    def setup(self, app):
        super().setup(app)

        c = app.config

        self.tz = get_localzone()

    def list_urls(self):
        return ['sysinfo://']

    # noinspection PyBroadException
    def get_state(self, url):
        purl = urlparse(url)
        if purl.scheme != 'sysinfo':
            raise UnsupportedException
        res = {}
        res['platform'] = platform.platform()
        res['hostname'] = socket.gethostbyaddr(socket.gethostname())[0]
        res['system'] = platform.uname().system
        res['version'] = platform.uname().version
        res['node'] = platform.uname().node
        res['release'] = platform.uname().release
        res['machine'] = platform.uname().machine
        res['processor'] = platform.uname().processor
        res['linux_distname'] = platform.linux_distribution()[0]
        res['linux_version'] = platform.linux_distribution()[1]
        res['linuxid'] = platform.linux_distribution()[2]
        return res


def load(app):
    app.log.debug('in load')
    handler.register(SysInfoPlugin)
