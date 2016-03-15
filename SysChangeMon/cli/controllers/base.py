"""syschangemon base controller."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from cli.ext.pluginbase import UnsupportedException
from core.model import Model
from core.sessiondiff import SessionDiff
from peewee import OperationalError
from tzlocal.unix import get_localzone
from datetime import datetime

class SysChangeMonBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = 'System change monitor'
        arguments = [
            (['-f', '--foo'],
             dict(help='the notorious foo option', dest='foo', action='store',
                  metavar='TEXT') ),
            ]

    @expose(help="run collect session, store current system state to database")
    def collect(self):
        self.app.log.debug("Inside SysChangeMonBaseController.collect()")

        db = self.app.storage.db
        assert isinstance(db, Model)

        session = db.new_session()
        session['start_time'] = datetime.now(tz=get_localzone())
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
        session['end_time'] = datetime.now(tz=get_localzone())
        session.save()
        self.app.exit_code = 0
        return

    @expose(help="clean up database, expunge old sessions")
    def cleanup(self):
        self.app.log.debug("Inside SysChangeMonBaseController.cleanup()")

        db = self.app.storage.db
        assert isinstance(db, Model)

        try:
            session_keep = self.app.config.get('SysChangeMon', 'session_keep')

            recent_sessions = db.recent_closed_sessions(session_keep)
            assert isinstance(recent_sessions, list)
            for sess in db.find_sessions():
                if sess not in recent_sessions:
                    self.app.log.debug("Expunging old session {}".format(sess['uuid']))
                    sess.delete()
        except OperationalError:
            # expected on empty db
            pass

        try:
            report_keep = self.app.config.get('SysChangeMon', 'report_keep')

            recent_reports = db.recent_reports(report_keep)
            assert isinstance(recent_reports, list)
            for report in db.find_reports():
                if report not in recent_reports:
                    self.app.log.debug("Expunging old report {}".format(report['uuid']))
                    report.delete()
        except OperationalError:
            # expected on empty db
            pass

        # TODO: implement low level db cleanup, eg: db.query('VACUUM')

        self.app.exit_code = 0
        return

    @expose(help='diff last two sessions and save report in database')
    def diff(self):
        self.app.log.debug("Inside SysChangeMonBaseController.diff()")

        db = self.app.storage.db
        assert isinstance(db, Model)

        recent = db.recent_closed_sessions(2)
        if len(recent) != 2:
            print("no previous state - exiting without diff")
            self.app.exit_code = 1
            return

        diff = SessionDiff(recent[1], recent[0])
        diff_dict = diff.__dict__
        diff_dict['is_empty'] = diff.is_empty
        report = self.app.render(diff_dict, 'report_txt.html', out=None)
        #print(report)

        dbrep = db.new_report()
        dbrep['text'] = report
        dbrep['is_empty'] = diff.is_empty
        dbrep.save()

        self.app.exit_code = 0
        return

    @expose(help='print last report from database')
    def print_report(self):
        db = self.app.storage.db
        assert isinstance(db, Model)

        report = db.last_report()
        #print(report['is_empty'])
        print(report['text'])

        self.app.exit_code = 0
        return

    @expose(hide=True, help='collect, diff, cleanup, print_report')
    def default(self):
        self.app.log.debug("Inside SysChangeMonBaseController.default()")

        self.collect()
        self.diff()
        self.cleanup()
        self.print_report()

        self.app.exit_code = 0
        return
