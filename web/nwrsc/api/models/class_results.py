# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from nwrsc.api.models.base_model_ import Model
from nwrsc.api.models.result_entry import ResultEntry  # noqa: F401,E501
from nwrsc.api import util


class ClassResults(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, classcode: str=None, entries: List[ResultEntry]=None):  # noqa: E501
        """ClassResults - a model defined in Swagger

        :param classcode: The classcode of this ClassResults.  # noqa: E501
        :type classcode: str
        :param entries: The entries of this ClassResults.  # noqa: E501
        :type entries: List[ResultEntry]
        """
        self.swagger_types = {
            'classcode': str,
            'entries': List[ResultEntry]
        }

        self.attribute_map = {
            'classcode': 'classcode',
            'entries': 'entries'
        }

        self._classcode = classcode
        self._entries = entries

    @classmethod
    def from_dict(cls, dikt) -> 'ClassResults':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ClassResults of this ClassResults.  # noqa: E501
        :rtype: ClassResults
        """
        return util.deserialize_model(dikt, cls)

    @property
    def classcode(self) -> str:
        """Gets the classcode of this ClassResults.


        :return: The classcode of this ClassResults.
        :rtype: str
        """
        return self._classcode

    @classcode.setter
    def classcode(self, classcode: str):
        """Sets the classcode of this ClassResults.


        :param classcode: The classcode of this ClassResults.
        :type classcode: str
        """

        self._classcode = classcode

    @property
    def entries(self) -> List[ResultEntry]:
        """Gets the entries of this ClassResults.

        a list of result entries  # noqa: E501

        :return: The entries of this ClassResults.
        :rtype: List[ResultEntry]
        """
        return self._entries

    @entries.setter
    def entries(self, entries: List[ResultEntry]):
        """Sets the entries of this ClassResults.

        a list of result entries  # noqa: E501

        :param entries: The entries of this ClassResults.
        :type entries: List[ResultEntry]
        """

        self._entries = entries
