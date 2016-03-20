"""syschangemon base controller."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from syschangemon.cli.ext.pluginbase import UnsupportedException
from syschangemon.core.model import Model
from syschangemon.core.sessiondiff import SessionDiff
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

    def _setup(self, app):
        super()._setup(app)

        plugins = {}
        for h in handler.list('state_plugin'):
            plugin = h()
            plugin.setup(self.app)
            plugins[plugin.label] = plugin

        self.plugins = plugins

    @expose(help="run collect session, store current system state to database")
    def collect(self):
        self.app.log.debug("Inside SysChangeMonBaseController.collect()")

        db = self.app.storage.db
        assert isinstance(db, Model)

        session = db.new_session()
        session['start_time'] = datetime.now(tz=get_localzone())
        session.save()

        plugins = self.plugins

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
            session_keep = self.app.config.get('syschangemon', 'session_keep')

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
            report_keep = self.app.config.get('syschangemon', 'report_keep')

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

        for plugin in self.plugins.values():
            diff = plugin.process_diff(diff)

        diff_dict = diff.__dict__
        diff_dict['is_empty'] = diff.is_empty
        report = self.app.render(diff_dict, 'report_txt.html', out=None)
        #print(report)

        dbrep = db.new_report()
        dbrep['text'] = report
        dbrep['html'] = "<html><body><pre>"+report+"</pre></body></html>"
        dbrep['is_empty'] = diff.is_empty
        dbrep.save()

        self.app.exit_code = 0
        return

    @expose(help='print last report from database')
    def print_report(self):
        db = self.app.storage.db
        assert isinstance(db, Model)

        try:
            report = db.last_report()
            #print(report['is_empty'])
            print(report['text'])
        except OperationalError:
            print('no recent report')

        self.app.exit_code = 0
        return

    @expose(help='email last report from database')
    def email_report(self):
        db = self.app.storage.db
        assert isinstance(db, Model)

        try:
            report = db.last_report()
            #print(report['is_empty'])
            #print(report['text'])

            params = dict()

            for item in ['from', 'to_addr', 'from_addr', 'cc', 'bcc', 'subject',
                         'ssl', 'tls', 'host', 'port', 'auth', 'username',
                            'password', 'timeout', 'subject_prefix']:
                params[item] = self.app.config.get('mail.smtp', item)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = str(params['subject'])
            msg['From'] = str(params['from'])
            msg['To'] = str(params['to_addr'])

            part1 = MIMEText(str(report['text']), 'plain')
            part2 = MIMEText(str(report['html']), 'html')

            msg.attach(part1)
            msg.attach(part2)

            if params['ssl'] == '1':
                server = smtplib.SMTP_SSL(params['host'], params['port'],
                                          params['timeout'])
                self.app.log.debug("initiating ssl")
                if params['tls'] == '1':
                    self.app.log.debug("initiating tls")
                    server.starttls()

            else:
                server = smtplib.SMTP(params['host'], params['port'],
                                      params['timeout'])

            if params['auth'] == '1':
                server.login(params['username'], params['password'])

            if self.app.debug is True:
                server.set_debuglevel(9)

            #print(msg.as_string())

            server.send_message(msg)

        except OperationalError:
            print('no recent report')

        self.app.exit_code = 0
        return

    @expose(hide=True, help='collect, diff, cleanup, print_report')
    def default(self):
        self.app.log.debug("Inside SysChangeMonBaseController.default()")

        self.collect()
        self.diff()
        self.cleanup()
        self.print_report()
        self.email_report()

        self.app.exit_code = 0
        return
