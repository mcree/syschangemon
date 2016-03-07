""" System Change Data Model Classes """
import datetime
from abc import abstractmethod
from collections import MutableSet
from urllib.parse import urlparse

from datetime import date, time, datetime
from uuid import UUID, uuid4

from pony.orm.core import Database, PrimaryKey, Required, Optional, Set, Discriminator

def define_model(*args, **kwargs):

    db = Database(*args, **kwargs)

    class Session(db.Entity):
        id = PrimaryKey(int, auto=True)
        state = Set("StoredState")
        uuid = Required(UUID, default=uuid4)
        stamp = Required(datetime, default=datetime.now())

        def __str__(self):
            s = super.__str__(self)
            s += "("
            s += "id:%s " % self.id
            s += "uuid:%s " % self.uuid
            s += "stamp:%s " % self.stamp
            s += "state:%s" % self.state
            s += ")"
            return s

    class TypedSet(Set):
        def __setitem__(self, key, value):
            if type(value) is str:
                self.create

    class StoredState(db.Entity):
        session = Required(Session)
        uri = PrimaryKey(str)
        meta = TypedSet("StateMeta")

    class StateMeta(db.Entity):
        state = Required(StoredState)
        key = Required(str)
        PrimaryKey(state, key)
        type = Discriminator(str)

    class StateMetaStr(StateMeta):
        _discriminator_ = 'str'
        str_value = Required(str, index=True)

    class StateMetaInt(StateMeta):
        _discriminator_ = 'int'
        int_value = Required(int, index=True)

    class StateMetaFloat(StateMeta):
        _discriminator_ = 'float'
        float_value = Required(float, index=True)

    class StateMetaDate(StateMeta):
        _discriminator_ = 'date'
        date_value = Required(date, index=True)

    class StateMetaTime(StateMeta):
        _discriminator_ = 'time'
        time_value = Required(time, index=True)

    class StateMetaDateTime(StateMeta):
        _discriminator_ = 'datetime'
        datetime_value = Required(datetime, index=True)

    class StateMetaBool(StateMeta):
        _discriminator_ = 'bool'
        bool_value = Required(bool, index=True)

    class StateMetaBytes(StateMeta):
        _discriminator_ = 'bytes'
        bytes_value = Required(bytes, index=True)

    db.generate_mapping(check_tables=True, create_tables=True)

    return db


class SysStateItem:
    """
    Abstract archetype for system state items. Represents actual state of a system component.
    """

    def __init__(self, uri: str):
        """
        Create instance

        :param uri: URI string identifying system state item
        :return: instance
        """
        urlparse(uri)  # string format check
        self.__uri = uri
        self.__payload = None
        self.__meta = dict()

    @abstractmethod
    def refresh(self):
        """
        Refresh state information from the underlying system component.

        State information consists of:
        *  payload: textual representation of complete system component state (eg: file content)
        *  meta: dictionary of key:value (str:str) pairs representing system component meta information (eg: file size,
           owner, mtime, ctime)

        This method should not be called very frequently to prevent heavy system load.

        :return: None
        """
        pass

    def __str__(self):
        """
        :return: Compact text representation of URI and meta
        """
        res = self.__uri+" "
        for (k, v) in self.__meta.items():
            res += "%15s:%15s " % (k, v)
        return res

    @property
    def payload(self) -> str:
        return self.__payload

    @property
    def meta(self) -> dict:
        return self.__meta

    @property
    def scheme(self):
        return urlparse(self.__uri).scheme

    @property
    def path(self):
        return urlparse(self.__uri).path


class SysState(MutableSet):
    """
    System state container
    """

    def __len__(self):
        return self.__states.__len__()

    def __iter__(self):
        return self.__states.__iter__()

    def discard(self, value: SysStateItem):
        assert isinstance(value, SysStateItem)
        return self.__states.discard(value)

    def add(self, value: SysStateItem):
        assert isinstance(value, SysStateItem)
        return self.__states.add(value)

    def __contains__(self, x):
        return self.__states.__contains__(x)

    def __init__(self, states: Set = set()):
        """
        Create system state container

        :param states: initial values, Set of SysStateItem instances
        :return: System state container instance
        """
        assert isinstance(states, MutableSet)
        self.__states = states
        return
