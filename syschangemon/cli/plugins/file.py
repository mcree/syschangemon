"""Filesystem Plugin for syschangemon."""
import binascii
import datetime
import re

import globre
import grp
import hashlib
import os
import pwd
import sys
from stat import *

from syschangemon.core.model import Model, Session
from syschangemon.core.partialhash import compute_from_path

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from cement.core import handler
from tzlocal.unix import get_localzone

from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface, UnsupportedException


def st_mode_repr(mode):
    """
    Calculate textual representation of binary inode mode.

    Sample output for regular file with mode 0644: 'u=rw-,g=r--,o=r--'

    :param mode: st_mode integer returned by os.stat()
    :return: textual representation of st_mode
    """
    res = ""
    if S_ISBLK(mode):
        res += "blk "
    if S_ISCHR(mode):
        res += "chr "
    if S_ISDIR(mode):
        res += "dir "
    if S_ISFIFO(mode):
        res += "fifo "
    if S_ISLNK(mode):
        res += "sym "
    if S_ISSOCK(mode):
        res += "sock "
    if mode | S_ISUID == mode:
        res += "setuid "
    if mode | S_ISGID == mode:
        res += "setgid "
    if mode | S_ISVTX == mode:
        res += "sticky "
    res += "u="
    if mode | S_IRUSR == mode:
        res += "r"
    else:
        res += "-"
    if mode | S_IWUSR == mode:
        res += "w"
    else:
        res += "-"
    if mode | S_IXUSR == mode:
        res += "x"
    else:
        res += "-"
    res += ",g="
    if mode | S_IRGRP == mode:
        res += "r"
    else:
        res += "-"
    if mode | S_IWGRP == mode:
        res += "w"
    else:
        res += "-"
    if mode | S_IXGRP == mode:
        res += "x"
    else:
        res += "-"
    res += ",o="
    if mode | S_IROTH == mode:
        res += "r"
    else:
        res += "-"
    if mode | S_IWOTH == mode:
        res += "w"
    else:
        res += "-"
    if mode | S_IXOTH == mode:
        res += "x"
    else:
        res += "-"

    return res



class FilePlugin(StatePluginBase):
    """
    filesystem plugin base class
    """
    class Meta:
        label = 'file'
        interface = StatePluginInterface

    def __init__(self, **kw):
        super().__init__(**kw)
        self.include = []
        self.exclude = []
        self.include_pats = []
        self.exclude_pats = []
        self.assume_nochange = []
        self.assume_change = []
        self.last_session = None
        self.tz = get_localzone()

    @staticmethod
    def _process_pattern_list(l):
        """
        process include/exclude pattern list to remove whitespace and empty elements

        :param l: list of string patterns
        :return: processed list of string patterns
        """

        l[:] = [v.strip() for v in l]  # strip all elements
        l[:] = [v for v in l if len(v) != 0]  # throw out empty elements

        return l

    @staticmethod
    def _find_base_dirs(l):
        """
        find base dirs in include pattern list to be included in filesystem walking

        :param l: include pattern list
        :return: tuple of two lists (flat, deep) - flat means no recursion, deep means recursion is needed
        """

        flat = []
        deep = []
        for e in l:
            item = []
            is_deep = False
            if re.match('.*[*].*[/].*', e):
                is_deep = True
            if e.find('**') >= 0:
                is_deep = True
            if e.find('{') >= 0:
                is_deep = True

            for i in e.split(os.sep):
                if i[-1:] == '\\':
                    is_deep = True
                    break
                if i.find('**') >= 0:
                    break
                if i.find('{') >= 0:
                    break
                if i.find('*') >= 0:
                    break
                if i.find('[') >= 0:
                    break

                item.append(i)

            it = os.sep.join(item)
            if len(it) == 0:
                it = '.'
            if is_deep:
                deep.append(it)
            else:
                flat.append(it)

        return list(set(flat)), list(set(deep))

    def setup(self, app):
        super(FilePlugin, self).setup(app)

        c = app.config

        conf_keys = c.keys(self._meta.label)

        # get include and exclude list from config file
        if 'include' in conf_keys:
            self.include = self._process_pattern_list(c.get(self._meta.label, 'include').split('\n'))
        if 'exclude' in conf_keys:
            self.exclude = self._process_pattern_list(c.get(self._meta.label, 'exclude').split('\n'))
        if 'no_assume_nochange' in conf_keys:
            self.assume_change = self._process_pattern_list(c.get(self._meta.label, 'no_assume_nochange').split('\n'))

        # compile globre patterns for include and exclude
        self.include_pats = []
        for pat in self.include:
            self.include_pats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        self.exclude_pats = []
        for pat in self.exclude:
            self.exclude_pats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        os.stat_float_times(True)

        if 'assume_nochange' in conf_keys:
            self.assume_nochange = [x.strip() for x in c.get(self._meta.label, 'assume_nochange').split(',')]

    @staticmethod
    def _matches_pat_list(path, pat_list):
        for pat in pat_list:
            if pat.match(path):
                return True
        return False

    def list_urls(self):
        res = []

        # find base dirs for include
        self.app.log.debug("enumerating using include: %s exclude: %s" % (self.include, self.exclude))
        (flat, deep) = self._find_base_dirs(self.include)

        self.app.log.debug("walk destinations: flat: %s deep: %s" % (flat, deep))

        # collect flat includes
        for f in flat:
            for name in os.listdir(f):
                filename = os.path.join(f, name)
                if os.path.isfile(filename) and self._matches_pat_list(filename, self.include_pats):
                        res.append(filename)

        # collect deep (recursive) includes
        for d in deep:
            for root, dirs, files in os.walk(d):
                for name in files:
                    filename = os.path.join(root, name)
                    if os.path.isfile(filename) and self._matches_pat_list(filename, self.include_pats):
                            res.append(filename)

        # filter out excludes
        filtered_res = []
        for f in res:
            if not self._matches_pat_list(f, self.exclude_pats):
                filtered_res.append(self._meta.label+'://'+f)

        res = filtered_res

        #self.app.log.debug("filelist: %s" % filelist)

        # we cannot run this piece of code in setup() since storage is not set up there
        db = self.app.storage.db
        assert isinstance(db, Model)
        self.last_session = db.last_closed_session()

        return res

    # noinspection PyBroadException
    def get_state(self, url):
        if str(url).startswith("file://"):
            path = url[7:]
        else:
            raise UnsupportedException
        res = {}
        try:
            stat = os.stat(path)
            res['size'] = stat.st_size
            res['ctime'] = datetime.datetime.fromtimestamp(stat.st_ctime, tz=self.tz)
            res['mtime'] = datetime.datetime.fromtimestamp(stat.st_mtime, tz=self.tz)
            res['mode'] = st_mode_repr(stat.st_mode)
            res['uid'] = str(stat.st_uid)
            res['gid'] = str(stat.st_gid)
            uidname = pwd.getpwuid(stat.st_uid).pw_name
            if uidname is not None and len(uidname) > 0:
                res['uid'] = res['uid'] + " (" + uidname + ")"
            gidname = grp.getgrgid(stat.st_gid).gr_name
            if gidname is not None and len(gidname) > 0:
                res['gid'] = res['gid'] + " (" + gidname + ")"
        except:
            e = sys.exc_info()[1]
            res['stat_error'] = e

        # todo: backport listxattr for python 3.2
        #try:
        #    attrs = os.listxattr(path)
        #    for attr in attrs:
        #        res['xattr_'+attr] = True
        #except:
        #    e = sys.exc_info()[1]
        #    res['xattr_error'] = e

        compute_hash = True
        if not self._matches_pat_list(path, self.assume_change) \
                and self.last_session is not None \
                and len(self.assume_nochange) > 0:
            try:
                prev = self.last_session.get_state(url)
                no_change = True
                for attr in self.assume_nochange:
                    if res[attr] != prev[attr]:
                        no_change = False
                if no_change:
                    for k, v in prev.items():
                        # copy all 'non special' values from previous state record
                        if k not in res.keys() and k not in ['url', 'plugin', 'sessionid', 'id']:
                            res[k] = v
                    res['assume_nochange'] = True
                    compute_hash = False
            except KeyError:
                pass  # expected if previous session contains no such url

        if compute_hash:
            res['assume_nochange'] = False
            try:
                digest = compute_from_path(path, hash_algorithm=hashlib.sha256)
                res['hash'] = binascii.hexlify(digest).decode('utf-8', 'ignore')
            except:
                e = sys.exc_info()[1]
                res['hash_error'] = e

        return res


def load(app):
    app.log.debug('in load')
    #hook.register('enumerate', enumerate)

    handler.register(FilePlugin)

    # register the plugin class.. this only happens if the plugin is enabled
    #handler.register(ExamplePluginController)
