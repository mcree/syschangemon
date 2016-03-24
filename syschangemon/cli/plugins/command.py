import shlex
import subprocess
from subprocess import PIPE

import sys
from cement.core import handler
from cement.core.foundation import CementApp

from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface, UnsupportedException


class CommandPlugin(StatePluginBase):
    """
    external command plugin base class
    """
    class Meta:
        label = 'command'
        interface = StatePluginInterface

    def __init__(self):
        super(CommandPlugin, self).__init__()
        self.commands = {}

    def setup(self, app_obj):
        super(CommandPlugin, self).setup(app_obj)
        c = self.app.config
        for k, v in c.get_section_dict(self.Meta.label).items():
            if str(k).startswith('command.'):
                url = self.Meta.label + "://" + str(k)[8:]
                self.commands[url] = str(v)

    def list_urls(self):
        return list(self.commands.keys())

    def get_state(self, url):
        if url in self.commands.keys():
            res = {}
            cmd = self.commands[url]
            #args = shlex.split(cmd) # not for shell=True
            self.app.log.debug("running %s" % cmd)
            args = [cmd]
            with subprocess.Popen(args, shell=True, bufsize=-1, close_fds=True, stderr=PIPE, stdout=PIPE, universal_newlines=True) as proc:
                if sys.version_info < (3, 3):  # no timeout parameter under python 3.3
                    stdout, stderr = proc.communicate()
                else:
                    stdout, stderr = proc.communicate(timeout=30)
                res['stdout'] = stdout
                res['stderr'] = stderr
                res['return_code'] = proc.returncode
            return res
        else:
            raise UnsupportedException


def load(app):
    handler.register(CommandPlugin)
