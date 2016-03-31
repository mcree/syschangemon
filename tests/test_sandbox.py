import csv
import re
from io import StringIO
from unittest.case import TestCase

from cement.utils.misc import init_defaults

from syschangemon.cli.main import SysChangeMonApp
import os
import sys

uuidregex='[0-9a-f]+-[0-9a-f]+-[0-9a-f]+-[0-9a-f]+-[0-9a-f]+'

sandbox = os.path.dirname(os.path.realpath(__file__)) + "/sandbox"

defaults = init_defaults('syschangemon')


def capture(f):
    """
    Decorator to capture standard output
    """
    def captured(*args, **kwargs):

        # setup the environment
        backup = sys.stdout

        try:
            sys.stdout = StringIO()     # capture output
            f(*args, **kwargs)
            out = sys.stdout.getvalue() # release output
        finally:
            sys.stdout.close()  # close the stream
            sys.stdout = backup # restore original stdout

        return out # captured output wrapped in a string

    return captured


class SysChangeMonSandboxApp(SysChangeMonApp):
    class Meta:
        config_defaults = defaults
        label = 'syschangemon'
        exit_on_close = False
        debug = True
        config_section = 'syschangemon'
        plugin_config_dirs = [sandbox + '/etc/plugins.d']
        config_files = [sandbox + '/etc/syschangemon.conf']
        #plugin_dirs = [sandbox + '/var/lib/syschangemon/plugins']
        #tepmplate_dirs = [sandbox + '/var/lib/syschangemon/templates']


class TestSandbox(TestCase):

    def reset_sandbox(self):
        print("resetting sandbox: " + sandbox)
        if os.path.isfile(sandbox + "/storage/db.sqlite"):
            os.remove(sandbox + "/storage/db.sqlite")

        if os.path.isfile(sandbox + "/files/testfile"):
            os.remove(sandbox + "/files/testfile")

    @capture
    def command(self, argv):
        """
        run syschangemon command

        :param argv: command line
        :return: command stdout
        """
        os.chdir(sandbox)
        app = SysChangeMonSandboxApp(argv=argv)
        try:
            with app:
                app.run()
        except SystemExit:
            pass

    def query_export_column(self, export, column):
        """
        Get list of values for a named export column

        :param export: CSV export returned by the export command
        :param column: column name
        :return: list of column values from export
        """
        r = csv.reader(export.split('\n'))
        head = next(r)
        res = []
        for row in r:
            idx = head.index(column)
            if len(row) >= idx:
                res.append(row[idx])
        return res

    def assertExportQuery(self, export, selector_column, selector_value, query_column, query_value):
        r = csv.reader(export.split('\n'))
        head = next(r)
        res = []
        for row in r:
            sel_idx = head.index(selector_column)
            qry_idx = head.index(query_column)
            if len(row) >= sel_idx and len(row) >= qry_idx:
                if row[sel_idx] == selector_value and row[qry_idx] == query_value:
                    return
        raise AssertionError("value not found")

    def assertExportContains(self, export, column, value):
        vals = self.query_export_column(export, column)
        if value in vals:
            return
        else:
            raise AssertionError("value not found")

    def assertExportNotContains(self, export, column, value):
        vals = self.query_export_column(export, column)
        if value in vals:
            raise AssertionError("unexpected value found")
        else:
            return

    def test_sandbox_collect_and_cleanup(self):
        self.reset_sandbox()

        self.command(['cleanup'])  # should not fail
        self.command(['collect'])
        self.command(['cleanup'])  # should not fail
        self.command(['collect'])
        self.command(['collect'])
        self.command(['cleanup'])  # should not fail

        self.command(['collect'])
        e = self.command(['export'])

        e = e.replace('\x00', '')

        # test command plugin
        self.assertExportContains(e, 'url', 'command://echo')
        self.assertExportQuery(e, 'url', 'command://echo', 'return_code', '0')
        self.assertExportQuery(e, 'url', 'command://echo', 'stdout', 'stdout value')
        self.assertExportQuery(e, 'url', 'command://echo', 'stderr', 'stderr value')

        # test file plugin
        self.assertExportContains(e, 'url', 'file://files/passwd')
        self.assertExportQuery(e, 'url', 'file://files/passwd', 'size', '117')
        self.assertExportQuery(e, 'url', 'file://files/passwd', 'hash', 'd3ac21fe5a2a30c3e8a5608cb0a00179df0c4baf95d2a6755b401aeb0ba50028')
        self.assertExportNotContains(e, 'url', 'file://files/passwd.bak')

        # test conffile plugin
        self.assertExportContains(e, 'url', 'file://files/conffile')
        self.assertExportQuery(e, 'url', 'file://files/conffile', 'content', "conffile content")

        # test sysinfo plugin
        self.assertExportContains(e, 'url', 'sysinfo://')

    def test_sandbox_diff(self):
        self.reset_sandbox()
        self.command(['collect'])
        with open(sandbox + "/files/testfile", "w") as file:
            file.write("test file content")
        self.command(['collect'])
        self.command(['diff'])
        rep = self.command(['print-report'])
        #print(rep)

        self.assertRegex(rep, 'item_count.*8.*9')
        self.assertEqual(len(re.findall('found new item', rep)), 1)
        self.assertEqual(len(re.findall('lost old item', rep)), 0)
        self.assertEqual(len(re.findall('changed item', rep)), 0)
        self.assertRegex(rep, 'test file content')

        with open(sandbox + "/files/testfile", "w") as file:
            file.write("changed file content")

        self.command(['collect'])
        self.command(['diff'])
        rep = self.command(['print-report'])
        #print(rep)

        self.assertRegex(rep, 'item_count.*9.*9')
        self.assertEqual(len(re.findall('found new item', rep)), 0)
        self.assertEqual(len(re.findall('lost old item', rep)), 0)
        self.assertEqual(len(re.findall('changed item', rep)), 1)
        self.assertRegex(rep, 'test file content')
        self.assertRegex(rep, 'changed file content')

        os.unlink(sandbox + "/files/testfile")

        self.command(['collect'])
        self.command(['diff'])
        rep = self.command(['print-report'])
        #print(rep)

        self.assertRegex(rep, 'item_count.*9.*8')
        self.assertEqual(len(re.findall('found new item', rep)), 0)
        self.assertEqual(len(re.findall('lost old item', rep)), 1)
        self.assertEqual(len(re.findall('changed item', rep)), 0)
        self.assertRegex(rep, 'changed file content')

    def test_empty_export(self):
        self.reset_sandbox()
        e = self.command(['export'])
        self.assertRegex(e, 'no previous state - exiting without export')

    def test_reset_and_listing(self):
        self.reset_sandbox()
        e = self.command(['print-report'])
        self.assertRegex(e, 'no report found')
        e = self.command(['list-reports'])
        self.assertEqual(e.strip(), '')
        e = self.command(['list-sessions'])
        self.assertEqual(e.strip(), '')
        self.command(['collect'])
        self.command(['diff'])
        e = self.command(['list-sessions'])
        self.assertEqual(len(re.findall(uuidregex, e)), 1)
        e = self.command(['list-reports'])
        self.assertEqual(len(re.findall(uuidregex, e)), 0)
        e = self.command(['print-report'])
        self.assertRegex(e, 'no report found')
        self.command(['collect'])
        self.command(['diff'])
        e = self.command(['list-sessions'])
        self.assertEqual(len(re.findall(uuidregex, e)), 2)
        e = self.command(['list-reports'])
        self.assertEqual(len(re.findall(uuidregex, e)), 1)
        e = self.command(['print-report'])
        self.assertRegex(e, 'no difference')
        self.command(['reset'])
        e = self.command(['list-sessions'])
        self.assertEqual(len(re.findall(uuidregex, e)), 1)
        e = self.command(['list-reports'])
        self.assertEqual(len(re.findall(uuidregex, e)), 1)
        e = self.command(['diff'])
        self.assertRegex(e, 'no previous state')
        e = self.command(['print-report'])
        self.assertRegex(e, 'no difference')
