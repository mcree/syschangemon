"""syschangemon base controller."""
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cement.core.controller import CementBaseController, expose
from cement.core import hook
from syschangemon.cli.ext.pluginbase import UnsupportedException
from syschangemon.core.jinjaoutput import JinjaOutputHandler
from syschangemon.core.model import Model
from syschangemon.core.sessiondiff import SessionDiff
from peewee import OperationalError
from tzlocal.unix import get_localzone
from datetime import datetime

from syschangemon.core.version import SYSCHANGEMON_VERSION


class SysChangeMonBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = 'System change monitor'
        arguments = [
            (['-s', '--skip-empty-mail'],
             dict(help='skip email sending if report contains no differences', dest='skip_empty_mail', action='store_true')),
            (['-t', '--html'],
             dict(help='prefer HTML output when possible', dest='prefer_html', action='store_true')),
            (['-r', '--report-uuid'],
             dict(help='choose report by uuid (instead of most recent)', dest='report_uuid', metavar='UUID', action='store')),
            (['-o', '--old-session-uuid'],
             dict(help='choose old session by uuid (instead of second most recent)', dest='old_session_uuid', metavar='UUID', action='store')),
            (['-u', '--session-uuid'],
             dict(help='choose session by uuid (instead of most recent)', dest='session_uuid', metavar='UUID', action='store')),
            (['-V', '--version'],
             dict(help='show version information and exit', dest='version', action='store_true')),
            ]

    def _setup(self, app):
        super(SysChangeMonBaseController, self)._setup(app)

        plugins = {}
        for h in app.handler.list('state_plugin'):
            plugin = h()
            plugin.setup(self.app)
            plugins[plugin.label] = plugin

        self.plugins = plugins

    @expose(help='export system state stored in session as CSV (default: most recent session)')
    def export(self):
        self.app.log.debug("Inside SysChangeMonBaseController.export()")

        db = self.app.storage.db
        assert isinstance(db, Model)

        recent = db.recent_closed_sessions(1)
        if len(recent) != 1:
            print("no previous state - exiting without export")
            self.app.exit_code = 1
            return

        sess = None

        if self.app.pargs.session_uuid is not None:
            new = db.find_sessions(uuid=self.app.pargs.session_uuid)
            if len(new) > 0:
                sess = new[0]

        if sess is None:
            sess = recent[0]

        q = db.states.find(sessionid=sess['uuid'])
        db.db.freeze(q, format='csv', filename='/dev/stdout')

        self.app.exit_code = 0
        return


    @expose(help="list sessions stored in database")
    def list_sessions(self):
        self.app.log.debug("Inside SysChangeMonBaseController.list_sessions()")
        db = self.app.storage.db
        assert isinstance(db, Model)

        for sess in db.find_sessions():
            print(sess['uuid']+" "+str(sess['stamp']))

        self.app.exit_code = 0
        return

    @expose(help="list reports stored in database")
    def list_reports(self):
        self.app.log.debug("Inside SysChangeMonBaseController.list_reports()")
        db = self.app.storage.db
        assert isinstance(db, Model)

        for report in db.find_reports():
            print(report['uuid']+" "+str(report['stamp']))

        self.app.exit_code = 0
        return

    @expose(help="reset database - drop all sessions then run initial collect phase")
    def reset(self):
        self.app.log.debug("Inside SysChangeMonBaseController.reset()")
        db = self.app.storage.db
        assert isinstance(db, Model)

        for sess in db.find_sessions():
            sess.delete()

        self.collect()

        print('database reset done, new session collected:')

        self.list_sessions()

        self.app.exit_code = 0
        return

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

        session['hostname'] = socket.gethostbyaddr(socket.gethostname())[0]
        session['item_count'] = len(urls)
        session['closed'] = True
        session['end_time'] = datetime.now(tz=get_localzone())
        session.save()

        print("session " + session['uuid'] + " saved")

        self.app.exit_code = 0
        return

    @expose(help="clean up database, expunge old sessions and reports")
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

    @expose(help='diff two sessions and save report in database (default: most recent sessions)')
    def diff(self):
        self.app.log.debug("Inside SysChangeMonBaseController.diff()")

        db = self.app.storage.db
        assert isinstance(db, Model)

        recent = db.recent_closed_sessions(2)
        if len(recent) != 2:
            print("no previous state - exiting without diff")
            self.app.exit_code = 1
            return

        new_sess = None
        old_sess = None

        if self.app.pargs.old_session_uuid is not None:
            old = db.find_sessions(uuid=self.app.pargs.old_session_uuid)
            if len(old) > 0:
                new_sess = old[0]

        if self.app.pargs.session_uuid is not None:
            new = db.find_sessions(uuid=self.app.pargs.session_uuid)
            if len(new) > 0:
                new_sess = new[0]

        if old_sess is None:
            old_sess = recent[1]

        if new_sess is None:
            new_sess = recent[0]

        diff = SessionDiff(old_sess, new_sess)

        for plugin in self.plugins.values():
            diff = plugin.process_diff(diff)

        #pprint.pprint(diff.__dict__)

        diff_dict = diff.__dict__
        diff_dict['is_empty'] = diff.is_empty
        report_txt = self.app.render(diff_dict, 'report_txt.html', out=None)
        report_html = self.app.render(diff_dict, 'report_html.html', out=None)
        #print(report)

        dbrep = db.new_report()
        dbrep['text'] = report_txt
        dbrep['html'] = report_html
        dbrep['hostname'] = new_sess['hostname']
        dbrep['is_empty'] = diff.is_empty
        dbrep.save()

        print('report ' + dbrep['uuid'] + " saved")

        self.app.exit_code = 0
        return

    @expose(help='print report from database (default: last report)')
    def print_report(self):
        db = self.app.storage.db
        assert isinstance(db, Model)

        try:
            report = None
            if self.app.pargs.report_uuid is not None:
                reports = db.find_reports(uuid=self.app.pargs.report_uuid)
                if len(reports) > 0:
                    report = reports[0]
                else:
                    print('no report found')
                    self.app.exit_code = 2
                    return

            # default
            if report is None:
                report = db.last_report()

            if self.app.pargs.prefer_html:
                print(report['html'])
            else:
                print(report['text'])
        except OperationalError:
            print('no report found')
            self.app.exit_code = 2

        self.app.exit_code = 0
        return

    @expose(help='email report from database (default: last report)')
    def email_report(self):
        db = self.app.storage.db
        assert isinstance(db, Model)

        try:
            report = None
            if self.app.pargs is not None and self.app.pargs.report_uuid is not None:
                reports = db.find_reports(uuid=self.app.pargs.report_uuid)
                if len(reports) > 0:
                    report = reports[0]
                else:
                    print('no report found')
                    self.app.exit_code = 2
                    return

            # default
            if report is None:
                report = db.last_report()

            if report['is_empty'] and self.app.pargs.skip_empty_mail:
                print("skipping email sending because report is empty")
                return
            #print(report['is_empty'])
            #print(report['text'])

            params = dict()

            for item in ['from', 'to_addr', 'from_addr', 'cc', 'bcc', 'subject',
                         'ssl', 'tls', 'host', 'port', 'auth', 'username',
                            'password', 'timeout', 'subject_prefix']:
                params[item] = self.app.config.get('mail.smtp', item)

            outh = JinjaOutputHandler()
            outh._setup(self.app)
            subj = outh.render_from_string(str(params['subject']), report)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subj
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

            print('report sent')

        except OperationalError:
            print('no recent report')

        self.app.exit_code = 0
        return

    @expose(help='run collect, diff, cleanup, print-report, email-report in this order')
    def run(self):
        self.app.log.debug("Inside SysChangeMonBaseController.run()")

        self.collect()
        self.diff()
        self.cleanup()
        self.print_report()
        self.email_report()

        self.app.exit_code = 0
        return


    @expose(help='display usage information and exit', hide=True)
    def default(self):
        self.app.log.debug("Inside SysChangeMonBaseController.default()")

        if self.app.pargs.version:
            print('syschangemon version ' + SYSCHANGEMON_VERSION)
            self.app.close()
        else:
            self.app.args.print_usage()

        self.app.exit_code = 0
        return
