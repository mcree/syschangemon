

import utmp
from datetime import datetime
from cement.core.foundation import CementApp
from cli.ext.pluginbase import StatePluginBase, StatePluginInterface
from cement.core import handler
from core.dictdiff import DictDiff
from core.sessiondiff import SessionDiff
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
                        'end': datetime.now(self.tz)
                    })
            idx += 1
        return wtmp_sessions

    def process_diff(self, diff: SessionDiff) -> SessionDiff:
     #   pprint.pprint(wtmp_sessions)
    #            if entry.line not in sess.keys():
    #                sess[entry.line] = []
    #            sess[entry.line].append(entry)
    #    pprint.pprint(sess)
        for d in diff.diffs:
            assert isinstance(d, DictDiff)
            if 'mtime' in d.both_neq_tuple.keys():
                mtime = d.both_neq_tuple['mtime'][1]
                for sess in self.wtmp_sessions:
                    print(sess)
                    if sess['start'] < mtime < sess['end']:
                        d.plus_info.append(sess)
                        print(sess)

        return diff

"""

excerpt from last.c:
                case BOOT_TIME:
                        strcpy(ut.ut_line, "system boot");
                        quit = list(&ut, lastdown, R_REBOOT);
                        lastboot = ut.ut_time;
                        down = 1;
                        break;

                case USER_PROCESS:
                        /*
                         *      This was a login - show the first matching
                         *      logout record and delete all records with
                         *      the same ut_line.
                         */
                        c = 0;
                        for (p = utmplist; p; p = next) {
                                next = p->next;
                                if (strncmp(p->ut.ut_line, ut.ut_line,
                                    UT_LINESIZE) == 0) {
                                        /* Show it */
                                        if (c == 0) {
                                                quit = list(&ut, p->ut.ut_time,
                                                        R_NORMAL);
                                                c = 1;
                                        }
                                        if (p->next) p->next->prev = p->prev;
                                        if (p->prev)
                                                p->prev->next = p->next;
                                        else
                                                utmplist = p->next;
                                        free(p);
                                }
                        }
                        /*
                         *      Not found? Then crashed, down, still
                         *      logged in, or missing logout record.
                         */
                        if (c == 0) {
                                if (lastboot == 0) {
                                        c = R_NOW;
                                        /* Is process still alive? */
                                        if (ut.ut_pid > 0 &&
                                            kill(ut.ut_pid, 0) != 0 &&
                                            errno == ESRCH)
                                                c = R_PHANTOM;
                                } else
                                        c = whydown;
                                quit = list(&ut, lastboot, c);
                        }
                        /* FALLTHRU */
        /*
         *      If we saw a shutdown/reboot record we can remove
         *      the entire current utmplist.
         */
        if (down) {
                lastboot = ut.ut_time;
                whydown = (ut.ut_type == SHUTDOWN_TIME) ? R_DOWN : R_CRASH;
                for (p = utmplist; p; p = next) {
                        next = p->next;
                        free(p);
                }
                utmplist = NULL;
                down = 0;
        }

"""

def load(app: CementApp):
    handler.register(WtmpPlugin)
