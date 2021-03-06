# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from nwrsc.api.models.base_model_ import Model
from nwrsc.api import util


class IndexInfo(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, indexcode: str=None, value: float=None, descrip: str=None, modified: datetime=None):  # noqa: E501
        """IndexInfo - a model defined in Swagger

        :param indexcode: The indexcode of this IndexInfo.  # noqa: E501
        :type indexcode: str
        :param value: The value of this IndexInfo.  # noqa: E501
        :type value: float
        :param descrip: The descrip of this IndexInfo.  # noqa: E501
        :type descrip: str
        :param modified: The modified of this IndexInfo.  # noqa: E501
        :type modified: datetime
        """
        self.swagger_types = {
            'indexcode': str,
            'value': float,
            'descrip': str,
            'modified': datetime
        }

        self.attribute_map = {
            'indexcode': 'indexcode',
            'value': 'value',
            'descrip': 'descrip',
            'modified': 'modified'
        }

        self._indexcode = indexcode
        self._value = value
        self._descrip = descrip
        self._modified = modified

    @classmethod
    def from_dict(cls, dikt) -> 'IndexInfo':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The IndexInfo of this IndexInfo.  # noqa: E501
        :rtype: IndexInfo
        """
        return util.deserialize_model(dikt, cls)

    @property
    def indexcode(self) -> str:
        """Gets the indexcode of this IndexInfo.

        the letter code for the index  # noqa: E501

        :return: The indexcode of this IndexInfo.
        :rtype: str
        """
        return self._indexcode

    @indexcode.setter
    def indexcode(self, indexcode: str):
        """Sets the indexcode of this IndexInfo.

        the letter code for the index  # noqa: E501

        :param indexcode: The indexcode of this IndexInfo.
        :type indexcode: str
        """

        self._indexcode = indexcode

    @property
    def value(self) -> float:
        """Gets the value of this IndexInfo.

        the index value  # noqa: E501

        :return: The value of this IndexInfo.
        :rtype: float
        """
        return self._value

    @value.setter
    def value(self, value: float):
        """Sets the value of this IndexInfo.

        the index value  # noqa: E501

        :param value: The value of this IndexInfo.
        :type value: float
        """

        self._value = value

    @property
    def descrip(self) -> str:
        """Gets the descrip of this IndexInfo.

        the full index description  # noqa: E501

        :return: The descrip of this IndexInfo.
        :rtype: str
        """
        return self._descrip

    @descrip.setter
    def descrip(self, descrip: str):
        """Sets the descrip of this IndexInfo.

        the full index description  # noqa: E501

        :param descrip: The descrip of this IndexInfo.
        :type descrip: str
        """

        self._descrip = descrip

    @property
    def modified(self) -> datetime:
        """Gets the modified of this IndexInfo.

        the mod time  # noqa: E501

        :return: The modified of this IndexInfo.
        :rtype: datetime
        """
        return self._modified

    @modified.setter
    def modified(self, modified: datetime):
        """Sets the modified of this IndexInfo.

        the mod time  # noqa: E501

        :param modified: The modified of this IndexInfo.
        :type modified: datetime
        """

        self._modified = modified
