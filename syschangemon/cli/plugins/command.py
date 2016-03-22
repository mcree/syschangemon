import shlex
import subprocess
from subprocess import PIPE

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
        super().__init__()
        self.commands = {}

    def setup(self, app_obj):
        super().setup(app_obj)
        c = self.app.config
        for k, v in c.get_section_dict(self.Meta.label).items():
            if str(k).startswith('command.'):
                url = self.Meta.label + "://" + str(k)[8:]
                self.commands[url] = str(v)

    def list_urls(self) -> list:
        return list(self.commands.keys())

    def get_state(self, url) -> dict:
        if url in self.commands.keys():
            res = {}
            cmd = self.commands[url]
            #args = shlex.split(cmd) # not for shell=True
            self.app.log.debug("running %s" % cmd)
            args = [cmd]
            with subprocess.Popen(args, shell=True, bufsize=-1, close_fds=True, stderr=PIPE, stdout=PIPE, universal_newlines=True) as proc:
                stdout, stderr = proc.communicate(timeout=30)
                res['stdout'] = stdout
                res['stderr'] = stderr
                res['return_code'] = proc.returncode
            return res
        else:
            raise UnsupportedException


def load(app: CementApp):
    handler.register(CommandPlugin)
