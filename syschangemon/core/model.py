""" System Change Data Model Classes """
import pprint
import re
from datetime import datetime, date
from time import strptime, strftime
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from uuid import uuid4
from decimal import Decimal

import sys

import parsedatetime
from dateutil.parser import *
from peewee import BlobField, OperationalError, Field
from playhouse.dataset import DataSet
from playhouse.dataset import Table
from tzlocal.unix import get_localzone


class MyDataSet(DataSet):

    def __getitem__(self, table):
        return MyTable(self, table, self._models.get(table))


class MyTable(Table):

    def _guess_field_type(self, value):
        #print(type(value))
        if isinstance(value, bytes):
            return BlobField
        return super()._guess_field_type(value)

    # def insert(self, **data):
    #     new_keys = set(data) - set(self.model_class._meta.fields)
    #     res = super().insert(**data)
    #     for key in new_keys:
    #         if isinstance(data[key], (str, int, date, datetime, Decimal)) or data[key] is True or data[key] is False:
    #             #print("indexing %s" % key)
    #             try:
    #                 self.create_index([key])
    #             except OperationalError:
    #                 pass
    #     return res

    def upsert(self, columns=None, conjunction=None, **data):
        query = {}
        cols = set(columns) & set(self.model_class._meta.fields)
        if len(cols) != len(set(columns)):
            return self.insert(**data)
        for col in cols:
            query[col] = data[col]
        res = self.find(**query)
        if len(res) > 0:
            return self.update(columns, conjunction, **data)
        else:
            return self.insert(**data)


class State(dict):

    @staticmethod
    def from_dict(model, d):
        res = State(model, None)
        for k, v in d.items():
            try:
                # hack string timestamps back to datetime
                if isinstance(v, str):
                    if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', v):
                        v = parse(v, yearfirst=True, dayfirst=False, fuzzy=True)
                # hack bytes back to utf8 strings
                if isinstance(v, bytes) or isinstance(v, bytearray):
                    v = v.decode('utf-8')
            except ValueError:
                pass
            res[k] = v
        return res

    def __init__(self, model, sessionid, url=None, **kwargs):
        for k, v in kwargs.items():
            self[k] = v
        if url is None:
            url = 'uuid://' + str(uuid4())
        self._model = model
        self['sessionid'] = sessionid
        self['url'] = url

    def save(self):
        if 'sessionid' not in self or self['sessionid'] is None:
            raise ValueError("value for key 'session_id' is required to save state")
        url = urlparse(self['url'])
        if len(url.scheme) == 0:
            raise ValueError("value for key 'url' must have valid format, eg: scheme://path")
        return self._model.states.upsert(columns=['url', 'sessionid'], **self)

    def __repr__(self):
        res = '{'
        for k, v in self.items():
            res += k+':'
            if len(str(v)) > 25:
                res += str(v)[0:25] + "…"
            else:
                res += str(v)
            res += " "
        res += '}'
        return res


class Session(dict):

    @staticmethod
    def from_dict(model, d):
        res = Session(model)
        for k, v in d.items():
            try:
                # hack string timestamps back to datetime
                if isinstance(v, str):
                    if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', v):
                        v = parse(v, yearfirst=True, dayfirst=False, fuzzy=True)
                # hack bytes back to utf8 strings
                if isinstance(v, bytes) or isinstance(v, bytearray):
                    v = v.decode('utf-8')
            except ValueError:
                pass
            res[k] = v
        return res

    def __init__(self, model, uuid=None, stamp=None, closed=False, **kwargs):
        for k, v in kwargs.items():
            self[k] = v
        self._model = model
        if uuid is None:
            uuid = str(uuid4())
        if stamp is None:
            stamp = datetime.now(tz=get_localzone())
        self['uuid'] = uuid
        self['stamp'] = stamp
        self['closed'] = closed

    def save(self):
        return self._model.sessions.upsert(columns=['uuid'], **self)

    def new_state(self, **kwargs):
        return State(self._model, self['uuid'], **kwargs)

    def get_state(self, url):
        res = self._model.states.find_one(url=url, sessionid=self['uuid'])
        if res is not None:
            return State.from_dict(self._model, res)
        else:
            raise KeyError("state with url:"+url+" for session:"+self['uuid']+" not found")

    def all_urls(self):
        res = self._model.query('select url from states where sessionid = ?', [self['uuid']]).fetchall()
        res = [x[0] for x in res]
        return res

    def find_states(self, **kwargs):
        res = []
        for state in self._model.states.find(sessionid=self['uuid'], **kwargs):
            res.append(State.from_dict(self._model, state))
        return res

    def delete(self):
        with self._model.transaction():
            self._model.states.delete(sessionid=self['uuid'])
            self._model.sessions.delete(uuid=self['uuid'])


class Report(dict):
    @staticmethod
    def from_dict(model, d):
        res = Report(model)
        for k, v in d.items():
            res[k] = v
        return res

    def __init__(self, model, uuid=None, stamp=None, **kwargs):
        for k, v in kwargs.items():
            self[k] = v
        self._model = model
        if uuid is None:
            uuid = str(uuid4())
        if stamp is None:
            stamp = datetime.now(tz=get_localzone())
        self['uuid'] = uuid
        self['stamp'] = stamp

    def save(self):
        return self._model.reports.upsert(columns=['uuid'], **self)

    def delete(self):
        with self._model.transaction():
            self._model.reports.delete(uuid=self['uuid'])


class Model:
    def __init__(self, db_uri="sqlite:///:memory:"):
        self.db = MyDataSet(db_uri)
        self.sessions = self.db['sessions']
        self.states = self.db['states']
        self.reports = self.db['reports']

        # create indexes
        try:
            self.db.query('CREATE UNIQUE INDEX IF NOT EXISTS idx_session_uuid ON sessions(uuid)')
            self.db.query('CREATE INDEX IF NOT EXISTS idx_session_stamp ON sessions(stamp)')
            self.db.query('CREATE INDEX IF NOT EXISTS idx_state_sessionid ON states(sessionid)')
            self.db.query('CREATE INDEX IF NOT EXISTS idx_state_url ON states(url)')
            self.db.query('CREATE INDEX IF NOT EXISTS idx_state_plugin ON states(plugin)')
            self.db.query('CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_uuid ON reports(uuid)')
            self.db.query('CREATE INDEX IF NOT EXISTS idx_reports_stamp ON reports(stamp)')
        except OperationalError:
            pass

    def new_session(self, **kwargs):
        return Session(self, **kwargs)

    def new_report(self, **kwargs):
        return Report(self, **kwargs)

    def last_closed_session(self):
        uuid = self.query('select uuid from sessions where closed=1 order by stamp desc').fetchone()
        return Session.from_dict(self, self.sessions.find_one(uuid=uuid))

    def last_report(self):
        uuid = self.query('select uuid from reports order by stamp desc').fetchone()
        return Report.from_dict(self, self.reports.find_one(uuid=uuid))

    def recent_closed_sessions(self, count):
        uuids = self.query('select uuid from sessions where closed=1 order by stamp desc').fetchall()
        cnt = 0
        res = []
        for uuid in uuids:
            if cnt < int(count):
                res.append(Session.from_dict(self, self.sessions.find_one(uuid=uuid)))
            else:
                break
            cnt += 1
        return res

    def recent_reports(self, count):
        uuids = self.query('select uuid from reports order by stamp desc').fetchall()
        cnt = 0
        res = []
        for uuid in uuids:
            if cnt < int(count):
                res.append(Report.from_dict(self, self.reports.find_one(uuid=uuid)))
            else:
                break
            cnt += 1
        return res

    def find_sessions(self, **kwargs):
        res = []
        for sess in self.sessions.find(**kwargs):
            res.append(Session.from_dict(self, sess))
        return res

    def find_reports(self, **kwargs):
        res = []
        for sess in self.reports.find(**kwargs):
            res.append(Report.from_dict(self, sess))
        return res

    def delete(self):
        with self.transaction():
            self.sessions.delete()
            self.states.delete()
            self.reports.delete()

    def query(self, sql, params=None, commit=None):
        return self.db.query(sql, params, commit)

    def transaction(self):
        return self.db.transaction()
