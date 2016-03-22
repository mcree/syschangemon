from time import strftime

import utmp
from datetime import datetime
from cement.core.foundation import CementApp
from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface
from cement.core import handler
from syschangemon.core.dictdiff import DictDiff
from syschangemon.core.sessiondiff import SessionDiff
from tzlocal.unix import get_localzone
from utmp.reader import UTmpRecordType


class WtmpPlugin(StatePluginBase):
    """
    wtmp plugin base class
    """
    class Meta:
        label = 'wtmp'
        interface = StatePluginInterface

    def __init__(self):
        super().__init__()

        self.tz = get_localzone()
        self.wtmp_sessions = []

    def setup(self, app):
        super().setup(app)

        c = app.config

        path = c.get(self._meta.label, 'wtmp_path')
        self.wtmp_sessions = self.parse_wtmp(path)

    def parse_wtmp(self, path):
        entries = []
        with open(path, 'rb') as fd:
            buf = fd.read()
            for entry in utmp.read(buf):
                entries.append(entry)

        wtmp_sessions = []
        idx = 0
        now = datetime.now(self.tz)
        for entry in entries:
            if entry.type == UTmpRecordType.user_process:
                found = False
                for nentry in entries[idx:]:
                    if nentry.type == UTmpRecordType.dead_process and nentry.line == entry.line:
                        found = True
                    if nentry.type == UTmpRecordType.boot_time:
                        found = True
                    if found:
                        wtmp_sessions.append({
                            'user': entry.user,
                            'host': entry.host,
                            'line': entry.line,
                            'start': datetime.fromtimestamp(entry.sec + entry.usec*0.000001, self.tz),
                            'end': datetime.fromtimestamp(nentry.sec + nentry.usec*0.000001, self.tz)
                        })
                        break
                if not found:
                    wtmp_sessions.append({
                        'user': entry.user,
                        'host': entry.host,
                        'line': entry.line,
                        'start': datetime.fromtimestamp(entry.sec + entry.usec*0.000001, self.tz),
                        'end': now
                    })
            idx += 1
        return wtmp_sessions

    @staticmethod
    def wtmp_sess_repr(sess):
        return strftime("%Y-%m-%d %H:%M:%S %Z", sess['start'].timetuple()) + " - " + \
            strftime("%Y-%m-%d %H:%M:%S %Z", sess['end'].timetuple()) + " " + \
            sess['user'] + " " + \
            sess['line'] + "@" + \
            sess['host'] + "\n"

    def process_diff(self, diff: SessionDiff) -> SessionDiff:

        relevant = []

        oldstamp = diff.old_session['stamp']
        newstamp = diff.new_session['stamp']
        for sess in self.wtmp_sessions:
            if sess['start'] < oldstamp < sess['end'] or \
                                    sess['start'] < newstamp < sess['end'] or \
                                    oldstamp < sess['start'] < newstamp or \
                                    oldstamp < sess['end'] < newstamp:
                relevant.append(self.wtmp_sess_repr(sess))

        for d in diff.diffs:
            assert isinstance(d, DictDiff)
            ts = None
            if 'mtime' in d.both_neq_tuple.keys():
                ts = d.both_neq_tuple['mtime'][1]
            if 'ctime' in d.both_neq_tuple.keys():
                ts = d.both_neq_tuple['ctime'][1]
            if ts is not None:
                #print(type(mtime))
                res = ""
                for sess in self.wtmp_sessions:
                    #print(sess)
                    if sess['start'] < ts < sess['end']:
                        relevant.append(self.wtmp_sess_repr(sess))

        if len(relevant) > 0:
            res = "".join(sorted(set(relevant)))
            diff.extra['relevant_wtmp'] = res

        return diff


def load(app: CementApp):
    handler.register(WtmpPlugin)
