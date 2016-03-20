"""Filesystem Plugin for syschangemon."""
import datetime
import hashlib
from urllib.parse import urlparse

import sys

import binascii

import pwd

import grp

from cement.core import handler, hook
from cement.core.config import IConfig
from cement.core.controller import CementBaseController
from cement.core.foundation import CementApp
from syschangemon.cli.ext.pluginbase import StatePluginBase, StatePluginInterface, UnsupportedException
import os, globre

from partialhash import compute_from_path
from peewee import OperationalError
from pony.orm.core import db_session
from tzlocal.unix import get_localzone


class FilePlugin(StatePluginBase):
    """
    filesystem plugin base class
    """
    class Meta:
        label = 'file'
        interface = StatePluginInterface

    #_meta = Meta

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
    def _find_base_dirs(l) -> (object, object):
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
        super().setup(app)

        c = app.config

        # get include and exclude list from config file
        self.include = self._process_pattern_list(c.get(self._meta.label, 'include').split('\n'))
        self.exclude = self._process_pattern_list(c.get(self._meta.label, 'exclude').split('\n'))

        # compile globre patterns for include and exclude
        self.includepats = []
        for pat in self.include:
            self.includepats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        self.excludepats = []
        for pat in self.exclude:
            self.excludepats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        self.tz = get_localzone()

        os.stat_float_times(True)

    def list_urls(self) -> list:
        filelist = []

        # find base dirs for include
        self.app.log.debug("enumerating using include: %s exclude: %s" % (self.include, self.exclude))
        (flat, deep) = self._find_base_dirs(self.include)

        self.app.log.debug("walk destinations: flat: %s deep: %s" % (flat, deep))

        # collect flat includes
        for f in flat:
            for name in os.listdir(f):
                filename = os.path.join(f, name)
                if os.path.isfile(filename):
                    for pat in self.includepats:
                        if pat.match(filename):
                            filelist.append(filename)

        # collect deep (recursive) includes
        for d in deep:
            for root, dirs, files in os.walk(d):
                for name in files:
                    filename = os.path.join(root, name)
                    for pat in self.includepats:
                        if pat.match(filename):
                            filelist.append(filename)

        # filter out excludes
        filteredlist = []
        for f in filelist:
            is_exclude = False
            for pat in self.excludepats:
                if pat.match(f):
                    self.app.log.debug("%s excluded by %s" % (f, pat))
                    is_exclude = True
                    break
            if is_exclude == False:
                filteredlist.append(self._meta.label+'://'+f)

        filelist = filteredlist

        #self.app.log.debug("filelist: %s" % filelist)

        return filelist

    # noinspection PyBroadException
    def get_state(self, url) -> dir:
        purl = urlparse(url)
        if purl.scheme != 'file':
            raise UnsupportedException
        res = {}
        path = purl.path
        try:
            stat = os.stat(path)
            res['size'] = stat.st_size
            res['ctime'] = datetime.datetime.fromtimestamp(stat.st_ctime, tz=self.tz)
            res['mtime'] = datetime.datetime.fromtimestamp(stat.st_mtime, tz=self.tz)
            res['mode'] = stat.st_mode
            res['uid'] = stat.st_uid
            res['gid'] = stat.st_gid
            res['uid_name'] = pwd.getpwuid(stat.st_uid).pw_name
            res['gid_name'] = grp.getgrgid(stat.st_gid).gr_name
        except:
            e = sys.exc_info()[1]
            res['stat_error'] = e

        try:
            attrs = os.listxattr(path)
            for attr in attrs:
                res['xattr_'+attr] = True
        except:
            e = sys.exc_info()[1]
            res['xattr_error'] = e

        try:
            digest = compute_from_path(path, hash_algorithm=hashlib.sha256)
            res['hash'] = binascii.hexlify(digest)
        except:
            e = sys.exc_info()[1]
            res['hash_error'] = e

        return res


def load(app: CementApp):
    app.log.debug('in load')
    #hook.register('enumerate', enumerate)

    handler.register(FilePlugin)

    # register the plugin class.. this only happens if the plugin is enabled
    #handler.register(ExamplePluginController)
