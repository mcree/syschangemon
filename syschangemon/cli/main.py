"""syschangemon main application entry point."""
import traceback

from cement.core import hook
from cement.core.foundation import CementApp
from cement.ext.ext_configparser import ConfigParserConfigHandler
from cement.ext.ext_dummy import DummyOutputHandler
from cement.ext.ext_logging import LoggingLogHandler
from cement.utils.misc import init_defaults
from cement.core.exc import FrameworkError, CaughtSignal
from syschangemon.core import exc

# Application default.  Should update config/syschangemon.conf to reflect any
# changes, or additions here.
from syschangemon.cli.ext.pluginbase import StatePluginInterface
from syschangemon.core.jinjaoutput import JinjaOutputHandler

defaults = init_defaults('syschangemon')

# All internal/external plugin configurations are loaded from here
defaults['syschangemon']['plugin_config_dir'] = '/etc/syschangemon/plugins.d'

# External plugins (generally, do not ship with application code)
defaults['syschangemon']['plugin_dir'] = '/var/lib/syschangemon/plugins'

# External templates (generally, do not ship with application code)
defaults['syschangemon']['template_dir'] = '/var/lib/syschangemon/templates'


class LogHandler(LoggingLogHandler):
    def debug(self, msg, namespace=None, **kw):
        si = traceback.extract_stack(None, 2)[0]
        ns = "%s:%r" % (si[0][-25:], si[1])
        super(LogHandler, self).debug(msg, ns, **kw)

class SysChangeMonApp(CementApp):
    class Meta:
        label = 'syschangemon'
        config_defaults = defaults

        # All built-in application bootstrapping (always run)
        bootstrap = 'syschangemon.cli.bootstrap'

        # Optional plugin bootstrapping (only run if plugin is enabled)
        plugin_bootstrap = 'syschangemon.cli.plugins'

        # Internal templates (ship with application code)
        template_module = 'syschangemon.cli.templates'

        # Internal plugins (ship with application code)
        plugin_bootstrap = 'syschangemon.cli.plugins'

        # Hooks defined for main application logic
        define_hooks = ['enumerate', 'pre_process', 'load_item', 'sync_item', 'diff_item', 'post_process', 'output']

        # Custom log handler
        log_handler = LogHandler

        core_extensions = ['cement.ext.ext_dummy', 'cement.ext.ext_smtp', 'cement.ext.ext_plugin', 'cement.ext.ext_argparse', 'cement.ext.ext_configparser']

        define_handlers = [StatePluginInterface]

        output_handler = JinjaOutputHandler


class TestConfigHandler(ConfigParserConfigHandler):
    def __init__(self, *args, **kw):
        super(TestConfigHandler, self).__init__()


class SysChangeMonTestApp(SysChangeMonApp):
    """A test app that is better suited for testing."""
    class Meta:
        # default argv to empty (don't use sys.argv)
        argv = ['--debug']

        # don't look for config files (could break tests)
        config_files = []
        plugin_config_dir = ['']
        config_defaults = {}
        config_handler = TestConfigHandler

        # plugins enabled for testing
        #plugins = ['file']

        # don't call sys.exit() when app.close() is called in tests
        exit_on_close = False


# Define the applicaiton object outside of main, as some libraries might wish
# to import it as a global (rather than passing it into another class/func)
app = SysChangeMonApp()


def main():
    with app:
        try:
            app.run()

        except exc.SysChangeMonError as e:
            # Catch our application errors and exit 1 (error)
            print('SysChangeMonError > %s' % e)
            app.exit_code = 1
            
        except FrameworkError as e:
            # Catch framework errors and exit 1 (error)
            print('FrameworkError > %s' % e)
            app.exit_code = 1

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('CaughtSignal > %s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
