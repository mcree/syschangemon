"""syschangemon base controller."""
from cement.core import hook
from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook


class SysChangeMonBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = 'System change monitor'
        arguments = [
            (['-f', '--foo'],
             dict(help='the notorious foo option', dest='foo', action='store',
                  metavar='TEXT') ),
            ]

    @expose(hide=True)
    def default(self):
        self.app.log.debug("Inside SysChangeMonBaseController.default().")

        for h in handler.list('scmplugin'):
            print(h)
            n=h()
            print(n)
            n._setup(self.app)
            n.enumerate()

        for res in hook.run('enumerate', self.app):
            self.app.log.debug('enumerate result: %s' % res)


    

        # If using an output handler such as 'mustache', you could also
        # render a data dictionary using a template.  For example:
        #
        #   data = dict(foo='bar')
        #   self.app.render(data, 'default.mustache')
        #
        #
        # The 'default.mustache' file would be loaded from
        # ``SysChangeMon.cli.templates``, or ``/var/lib/SysChangeMon/templates/``.
        #
