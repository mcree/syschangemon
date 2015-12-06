""" System Change Data Model Classes """
from abc import abstractmethod
from collections import MutableSet, Set
from urllib.parse import urlparse


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
