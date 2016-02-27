from cement.core.foundation import CementApp
from cement.core.interface import Interface, Attribute
from cement.core.handler import CementBaseHandler


class SCMPluginInterface(Interface):
    class IMeta:
        label = 'scmplugin'

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


class SCMPluginBase(CementBaseHandler):
    class Meta:
        interface = SCMPluginInterface
        label = 'SysChangeMon Plugin Base'

    _meta = Meta

    def __init__(self):
        self.app = None

    def _setup(self, app_obj):
        self.app = app_obj
        print("Doing work @ _setup!")

    def enumerate(self):
        print("Doing work @ enumerate!")
