"""Filesystem Plugin for syschangemon."""

from cement.core import handler, hook
from cement.core.config import IConfig
from cement.core.controller import CementBaseController
from cement.core.foundation import CementApp
from cli.ext.pluginbase import SCMPluginBase, SCMPluginInterface
import os, globre

class FSPlugin(SCMPluginBase):
    """
    filesystem plugin base class
    """
    class Meta:
        label = 'files'
        interface = SCMPluginInterface

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

    def enumerate(self):
        c = self.app.config

        filelist = []

        # get include and exclude list from config file
        include = self._process_pattern_list(c.get('files', 'include').split('\n'))
        exclude = self._process_pattern_list(c.get('files', 'exclude').split('\n'))

        # compile globre patterns for include and exclude
        includepats = []
        for pat in include:
            includepats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        excludepats = []
        for pat in exclude:
            excludepats.append(globre.compile(pat, flags=globre.EXACT, split_prefix=False))

        # find base dirs for include
        self.app.log.debug("enumerating using include: %s exclude: %s" % (include, exclude))
        (flat, deep) = self._find_base_dirs(include)

        self.app.log.debug("walk destinations: flat: %s deep: %s" % (flat, deep))

        # collect flat includes
        for f in flat:
            for name in os.listdir(f):
                filename = os.path.join(f, name)
                if os.path.isfile(filename):
                    for pat in includepats:
                        if pat.match(filename):
                            filelist.append(filename)

        # collect deep (recursive) includes
        for d in deep:
            for root, dirs, files in os.walk(d):
                for name in files:
                    filename = os.path.join(root, name)
                    for pat in includepats:
                        if pat.match(filename):
                            filelist.append(filename)

        # filter out excludes
        filteredlist = []
        for f in filelist:
            is_exclude = False
            for pat in excludepats:
                if pat.match(f):
                    self.app.log.debug("%s excluded by %s" % (f, pat))
                    is_exclude = True
                    break
            if is_exclude == False:
                filteredlist.append(f)

        filelist = filteredlist

        self.app.log.debug("filelist: %s" % filelist)

        return filelist


def load(app: CementApp):
    app.log.debug('in load')
    #hook.register('enumerate', enumerate)

    handler.register(FSPlugin)

    # register the plugin class.. this only happens if the plugin is enabled
    #handler.register(ExamplePluginController)
