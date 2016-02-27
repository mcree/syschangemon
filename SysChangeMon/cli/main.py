"""syschangemon main application entry point."""
import traceback

from cement.core import hook
from cement.core.foundation import CementApp
from cement.ext.ext_configparser import ConfigParserConfigHandler
from cement.ext.ext_logging import LoggingLogHandler
from cement.utils.misc import init_defaults
from cement.core.exc import FrameworkError, CaughtSignal
from SysChangeMon.core import exc

# Application default.  Should update config/SysChangeMon.conf to reflect any
# changes, or additions here.
from cli.ext.pluginbase import SCMPluginInterface

defaults = init_defaults('SysChangeMon')

# All internal/external plugin configurations are loaded from here
defaults['SysChangeMon']['plugin_config_dir'] = '/etc/SysChangeMon/plugins.d'

# External plugins (generally, do not ship with application code)
defaults['SysChangeMon']['plugin_dir'] = '/var/lib/SysChangeMon/plugins'

# External templates (generally, do not ship with application code)
defaults['SysChangeMon']['template_dir'] = '/var/lib/SysChangeMon/templates'


class LogHandler(LoggingLogHandler):
    def debug(self, msg, namespace=None, **kw):
        si = traceback.extract_stack(None, 2)[0]
        ns = "%s:%r" % (si[0][-25:], si[1])
        super().debug(msg, ns, **kw)


class ConfigHandler(ConfigParserConfigHandler):
    def __init__(self, *args, **kw):
        super().__init__(strict=False)
        self._strict = False
        #print('in custom ConfigHandler')


ch = ConfigHandler()

class SysChangeMonApp(CementApp):
    class Meta:
        label = 'SysChangeMon'
        config_defaults = defaults

        # All built-in application bootstrapping (always run)
        bootstrap = 'SysChangeMon.cli.bootstrap'

        # Optional plugin bootstrapping (only run if plugin is enabled)
        plugin_bootstrap = 'SysChangeMon.cli.plugins'

        # Internal templates (ship with application code)
        template_module = 'SysChangeMon.cli.templates'

        # Internal plugins (ship with application code)
        plugin_bootstrap = 'SysChangeMon.cli.plugins'

        # Hooks defined for main application logic
        define_hooks = ['enumerate', 'pre_process', 'load_item', 'sync_item', 'diff_item', 'post_process', 'output']

        # Custom log handler
        log_handler = LogHandler

        # Custom config handler
        config_handler = ConfigHandler

        core_extensions = ['cement.ext.ext_dummy', 'cement.ext.ext_smtp', 'cement.ext.ext_plugin', 'cement.ext.ext_argparse']

        define_handlers = [SCMPluginInterface]


class SysChangeMonTestApp(SysChangeMonApp):
    """A test app that is better suited for testing."""
    class Meta:
        # default argv to empty (don't use sys.argv)
        argv = ['--debug']

        # don't look for config files (could break tests)
        #config_files = []
        #plugin_config_dir = ['/home/mcree/PycharmProjects/syschangemon/config/plugins.d']

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
