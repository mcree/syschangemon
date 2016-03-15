import pprint

import utmp
from cement.core.foundation import CementApp
from cli.ext.pluginbase import StatePluginBase, StatePluginInterface
from cement.core import handler
from core.sessiondiff import SessionDiff


class WtmpPlugin(StatePluginBase):
    """
    wtmp plugin base class
    """
    class Meta:
        label = 'wtmp'
        interface = StatePluginInterface

    def setup(self, app):
        super().setup(app)

        c = app.config

        self.path = c.get(self._meta.label, 'wtmp_path')

    def process_diff(self, diff: SessionDiff) -> SessionDiff:
        sess = {}
        with open(self.path, 'rb') as fd:
            buf = fd.read()
            for entry in utmp.read(buf):
                print(entry.time, entry.type, entry)
                if entry.line not in sess.keys():
                    sess[entry.line] = []
                sess[entry.line].append(entry)
        pprint.pprint(sess)
        return diff

"""

excerpt from last.c:

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
"""

def load(app: CementApp):
    handler.register(WtmpPlugin)
