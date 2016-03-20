import textwrap
from time import strftime

from cement.core import output
from cement.core.output import TemplateOutputHandler
from cement.utils.misc import minimal_logger
from jinja2 import Template
from jinja2.environment import Environment
from jinja2.loaders import BaseLoader
from parsedatetime import Calendar

LOG = minimal_logger(__name__)


def format3(val: str, *a, **kw):
    return val.format(*a, **kw)


def _tr(*args, separator, cols):
    rargs = []
    i = 0
    for arg in args:
        if len(cols) > i:
            c = str(cols[i])
            f = "{:"+c+"."+c+"}"
            rargs.append(f.format(arg))
        else:
            rargs.append(arg)
        i += 1
    return separator.join(rargs)


def tr(*args, separator=" | ", cols=[], wrap=True):
    if wrap:
        res = []
        wargs = []
        i = 0
        maxlen = 0
        for arg in args:
            if len(cols) > i:
                c = int(cols[i])
                w = []
                if isinstance(arg, str):
                    for a in arg.split('\n'):
                        w += textwrap.wrap(a, c)
                else:
                    w = [str(arg)]
            else:
                w = [arg]
            if len(w) > maxlen:
                maxlen = len(w)
            wargs.append(w)
            i += 1
        for i in range(0, maxlen):
            row = []
            for warg in wargs:
                if i < len(warg):
                    row.append(warg[i])
                else:
                    row.append("")
            res.append(_tr(*row, separator=separator, cols=cols))
        return "\n".join(res)
    else:
        return _tr(*args, separator=separator, cols=cols)


def hr(*args, char="-", separator="-+-", cols=[]):
    res = []
    for col in cols:
        res.append(char * col)
    return separator.join(res)


def is_multiline(arg: str):
    return str(arg).find('\n') > 0


def str_ftime(arg, format):
    cal = Calendar()
    return strftime(format, cal.parse(str(arg))[0])


class CementLoader(BaseLoader):
    def __init__(self, handler):
        self.handler = handler

    def get_source(self, environment, template):
        tpl = self.handler.load_template(template)
        if isinstance(tpl, bytes):
            source = tpl.decode('utf-8')
        else:
            source = tpl
        return source, template, lambda: False


class JinjaOutputHandler(TemplateOutputHandler):
    class Meta:
        interface = output.IOutput
        label = 'jinja2'

    def _setup(self, app):
        super()._setup(app)
        self.env = Environment(loader=CementLoader(self), extensions=['jinja2.ext.do'])
        self.env.filters['format3'] = format3
        self.env.globals['tr'] = tr
        self.env.globals['hr'] = hr
        self.env.globals['is_multiline'] = is_multiline
        self.env.filters['strftime'] = str_ftime

    def render(self, data_dict, **kw):
        template = kw.get('template', None)

        LOG.debug("rendering output using '%s' as a template." % template)
        jt = self.env.get_template(template)
        return jt.render(data_dict, **kw)


