"""syschangemon base controller."""
from cement.core import hook
from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from cli.ext.pluginbase import UnsupportedException
from core.model import Model
from core.sessiondiff import SessionDiff
from html2text import HTML2Text


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

        db = self.app.storage.db
        assert isinstance(db, Model)

        last = None
        try:
            last = db.last_closed_session()
            for sess in db.find_sessions():
                if sess['uuid'] != last['uuid']:
                    sess.delete()
        except:
            pass

        session = db.new_session()
        session.save()

        plugins = {}
        for h in handler.list('state_plugin'):
            plugin = h()
            plugin.setup(self.app)
            plugins[plugin.label]=plugin

        urls = []
        for plugin in plugins.values():
            urls += plugin.list_urls()

        for plugin in plugins.values():
            urls = plugin.process_urls(urls)

        for label, plugin in plugins.items():
            with db.transaction():
                for url in urls:
                    try:
                        statedict = plugin.get_state(url)
                        if statedict is not None:
                            state = session.new_state(url=url, plugin=label, **statedict)
                            #self.app.log.debug("read state: %s" % state)
                            state.save()
                    except UnsupportedException:
                        pass

        with db.transaction():
            for state in session.find_states():
                for plugin in plugins.values():
                    old = state.copy()
                    new = plugin.process_state(state)
                    if old != new:
                        state.save()
                        #self.app.log.debug("updated state: %s" % state)

        for res in hook.run('enumerate', self.app):
            self.app.log.debug('enumerate result: %s' % res)

        session['closed'] = True
        session.save()

        if last is not None:
            diff = SessionDiff(last, session)

            report = self.app.render(diff.__dict__, 'report_txt.html', out=None)
            print(report)

        else:
            print("no previous state - exiting without diff")
        # TODO: implement db cleanup, eg: db.query('VACUUM')

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
