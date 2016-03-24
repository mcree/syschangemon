#
# Contains code from https://github.com/hjacobs/utmp
#

from time import strftime

from cement.core.foundation import CementApp
from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface
from cement.core import handler
from syschangemon.core.dictdiff import DictDiff
from syschangemon.core.sessiondiff import SessionDiff
from tzlocal.unix import get_localzone

import collections
import datetime
import struct
from enum import Enum


class UTmpRecordType(Enum):
    empty = 0
    run_lvl = 1
    boot_time = 2
    new_time = 3
    old_time = 4
    init_process = 5
    login_process = 6
    user_process = 7
    dead_process = 8
    accounting = 9


def convert_string(val):
    if isinstance(val, bytes):
        return val.rstrip(b'\0').decode()
    return val


class UTmpRecord(collections.namedtuple('UTmpRecord',
                                        'type pid line id user host exit0 exit1 session' +
                                        ' sec usec addr0 addr1 addr2 addr3 unused')):

    @property
    def type(self):
        return UTmpRecordType(self[0])

    @property
    def time(self):
        return datetime.datetime.fromtimestamp(self.sec) + datetime.timedelta(microseconds=self.usec)

STRUCT = struct.Struct('hi32s4s32s256shhiii4i20s')


def utmp_read(buf):
    offset = 0
    while offset < len(buf):
        yield UTmpRecord._make(map(convert_string, STRUCT.unpack_from(buf, offset)))
        offset += STRUCT.size


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
            for entry in utmp_read(buf):
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

    def process_diff(self, diff):

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


def load(app):
    handler.register(WtmpPlugin)
