import urllib

from diff_match_patch.diff_match_patch import diff_match_patch


class DictDiff:

    def _diff_text(self, t1, t2):
        diff = diff_match_patch()
        diff.Diff_Timeout = 1
        a = diff.diff_linesToChars(t1, t2)
        diffs = diff.diff_main(a[0], a[1], False)
        diff.diff_charsToLines(diffs, a[2])
        diff.diff_cleanupEfficiency(diffs)
        patch = diff.patch_make(diffs)
        return urllib.parse.unquote(diff.patch_toText(patch).replace('%0A', ''))

    def __init__(self, dict1, label1, dict2, label2, ignore_keys=[]):

        self.plus_info = {}
        self.label1 = label1
        self.label2 = label2

        keys1 = set(dict1.keys()) - set(ignore_keys)
        keys2 = set(dict2.keys()) - set(ignore_keys)

        self.only1 = {}
        for key in keys1 - keys2:
            self.only1[key] = dict1[key]

        self.only2 = {}
        for key in keys2 - keys1:
            self.only2[key] = dict2[key]

        self.both_neq_diff = {}
        self.both_neq_tuple = {}
        self.both_eq = {}
        for key in keys1 & keys2:
            val1 = dict1[key]
            val2 = dict2[key]
            if val1 == val2:
                self.both_eq[key] = val1
            else:
                if isinstance(val1, bytes):
                    val1 = val1.decode('utf-8')
                    val2 = val2.decode('utf-8')
                if str(val1).find('\n') > 0:
                    self.both_neq_diff[key] = self._diff_text(str(val1), str(val2))
                else:
                    #if key == 'mtime':
                        #print('dictdiff type(mtime):'+str(type(val1)))
                    self.both_neq_tuple[key] = (val1, val2)

    def is_empty(self):
        return len(self.only1) == 0 and len(self.only2) == 0 \
               and len(self.both_neq_diff) == 0 and len(self.both_neq_tuple) == 0

    def __repr__(self):
        res = ""

        res += "--- %s\n" % self.label1
        for k, v in self.only1.items():
            res += "    %s: %s\n" % (k, str(v).replace('\n', '\n    '))

        res += "+++ %s\n" % self.label2
        for k, v in self.only2.items():
            res += "    %s: %s\n" % (k, str(v).replace('\n', '\n    '))

        #for k, v in self.both_eq.items():
        #    res += "=== %s: %s\n" % (k, str(v).replace('\n', '\n    '))

        for k, v in self.both_neq_tuple.items():
            res += "!!! %s: (-) %s != (+) %s\n" % (k, v[0], v[1])

        for k, v in self.both_neq_diff.items():
            res += "!!! %s: \n    %s\n" % (k, str(v).replace('\n', '\n    '))

        return res
