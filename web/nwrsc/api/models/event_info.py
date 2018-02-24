# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from nwrsc.api.models.base_model_ import Model
from nwrsc.api import util


class EventInfo(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, eventdate: date=None, modified: datetime=None, name: str=None, runs: int=None, ispro: bool=None, conepen: float=None, courses: int=None, eventid: str=None, gatepen: float=None, location: str=None, segments: int=None, ispractice: bool=None, countedruns: int=None):  # noqa: E501
        """EventInfo - a model defined in Swagger

        :param eventdate: The eventdate of this EventInfo.  # noqa: E501
        :type eventdate: date
        :param modified: The modified of this EventInfo.  # noqa: E501
        :type modified: datetime
        :param name: The name of this EventInfo.  # noqa: E501
        :type name: str
        :param runs: The runs of this EventInfo.  # noqa: E501
        :type runs: int
        :param ispro: The ispro of this EventInfo.  # noqa: E501
        :type ispro: bool
        :param conepen: The conepen of this EventInfo.  # noqa: E501
        :type conepen: float
        :param courses: The courses of this EventInfo.  # noqa: E501
        :type courses: int
        :param eventid: The eventid of this EventInfo.  # noqa: E501
        :type eventid: str
        :param gatepen: The gatepen of this EventInfo.  # noqa: E501
        :type gatepen: float
        :param location: The location of this EventInfo.  # noqa: E501
        :type location: str
        :param segments: The segments of this EventInfo.  # noqa: E501
        :type segments: int
        :param ispractice: The ispractice of this EventInfo.  # noqa: E501
        :type ispractice: bool
        :param countedruns: The countedruns of this EventInfo.  # noqa: E501
        :type countedruns: int
        """
        self.swagger_types = {
            'eventdate': date,
            'modified': datetime,
            'name': str,
            'runs': int,
            'ispro': bool,
            'conepen': float,
            'courses': int,
            'eventid': str,
            'gatepen': float,
            'location': str,
            'segments': int,
            'ispractice': bool,
            'countedruns': int
        }

        self.attribute_map = {
            'eventdate': 'eventdate',
            'modified': 'modified',
            'name': 'name',
            'runs': 'runs',
            'ispro': 'ispro',
            'conepen': 'conepen',
            'courses': 'courses',
            'eventid': 'eventid',
            'gatepen': 'gatepen',
            'location': 'location',
            'segments': 'segments',
            'ispractice': 'ispractice',
            'countedruns': 'countedruns'
        }

        self._eventdate = eventdate
        self._modified = modified
        self._name = name
        self._runs = runs
        self._ispro = ispro
        self._conepen = conepen
        self._courses = courses
        self._eventid = eventid
        self._gatepen = gatepen
        self._location = location
        self._segments = segments
        self._ispractice = ispractice
        self._countedruns = countedruns

    @classmethod
    def from_dict(cls, dikt) -> 'EventInfo':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The EventInfo of this EventInfo.  # noqa: E501
        :rtype: EventInfo
        """
        return util.deserialize_model(dikt, cls)

    @property
    def eventdate(self) -> date:
        """Gets the eventdate of this EventInfo.

        the date of the event  # noqa: E501

        :return: The eventdate of this EventInfo.
        :rtype: date
        """
        return self._eventdate

    @eventdate.setter
    def eventdate(self, eventdate: date):
        """Sets the eventdate of this EventInfo.

        the date of the event  # noqa: E501

        :param eventdate: The eventdate of this EventInfo.
        :type eventdate: date
        """

        self._eventdate = eventdate

    @property
    def modified(self) -> datetime:
        """Gets the modified of this EventInfo.

        the mod time  # noqa: E501

        :return: The modified of this EventInfo.
        :rtype: datetime
        """
        return self._modified

    @modified.setter
    def modified(self, modified: datetime):
        """Sets the modified of this EventInfo.

        the mod time  # noqa: E501

        :param modified: The modified of this EventInfo.
        :type modified: datetime
        """

        self._modified = modified

    @property
    def name(self) -> str:
        """Gets the name of this EventInfo.

        the event name  # noqa: E501

        :return: The name of this EventInfo.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this EventInfo.

        the event name  # noqa: E501

        :param name: The name of this EventInfo.
        :type name: str
        """

        self._name = name

    @property
    def runs(self) -> int:
        """Gets the runs of this EventInfo.

        number of runs in the event  # noqa: E501

        :return: The runs of this EventInfo.
        :rtype: int
        """
        return self._runs

    @runs.setter
    def runs(self, runs: int):
        """Sets the runs of this EventInfo.

        number of runs in the event  # noqa: E501

        :param runs: The runs of this EventInfo.
        :type runs: int
        """

        self._runs = runs

    @property
    def ispro(self) -> bool:
        """Gets the ispro of this EventInfo.

        true if a ProSolo event  # noqa: E501

        :return: The ispro of this EventInfo.
        :rtype: bool
        """
        return self._ispro

    @ispro.setter
    def ispro(self, ispro: bool):
        """Sets the ispro of this EventInfo.

        true if a ProSolo event  # noqa: E501

        :param ispro: The ispro of this EventInfo.
        :type ispro: bool
        """

        self._ispro = ispro

    @property
    def conepen(self) -> float:
        """Gets the conepen of this EventInfo.

        the penalty for hitting a cone  # noqa: E501

        :return: The conepen of this EventInfo.
        :rtype: float
        """
        return self._conepen

    @conepen.setter
    def conepen(self, conepen: float):
        """Sets the conepen of this EventInfo.

        the penalty for hitting a cone  # noqa: E501

        :param conepen: The conepen of this EventInfo.
        :type conepen: float
        """

        self._conepen = conepen

    @property
    def courses(self) -> int:
        """Gets the courses of this EventInfo.

        the number of courses in the event  # noqa: E501

        :return: The courses of this EventInfo.
        :rtype: int
        """
        return self._courses

    @courses.setter
    def courses(self, courses: int):
        """Sets the courses of this EventInfo.

        the number of courses in the event  # noqa: E501

        :param courses: The courses of this EventInfo.
        :type courses: int
        """

        self._courses = courses

    @property
    def eventid(self) -> str:
        """Gets the eventid of this EventInfo.

        the event id  # noqa: E501

        :return: The eventid of this EventInfo.
        :rtype: str
        """
        return self._eventid

    @eventid.setter
    def eventid(self, eventid: str):
        """Sets the eventid of this EventInfo.

        the event id  # noqa: E501

        :param eventid: The eventid of this EventInfo.
        :type eventid: str
        """

        self._eventid = eventid

    @property
    def gatepen(self) -> float:
        """Gets the gatepen of this EventInfo.

        the penalty for missing a gate  # noqa: E501

        :return: The gatepen of this EventInfo.
        :rtype: float
        """
        return self._gatepen

    @gatepen.setter
    def gatepen(self, gatepen: float):
        """Sets the gatepen of this EventInfo.

        the penalty for missing a gate  # noqa: E501

        :param gatepen: The gatepen of this EventInfo.
        :type gatepen: float
        """

        self._gatepen = gatepen

    @property
    def location(self) -> str:
        """Gets the location of this EventInfo.

        the event location  # noqa: E501

        :return: The location of this EventInfo.
        :rtype: str
        """
        return self._location

    @location.setter
    def location(self, location: str):
        """Sets the location of this EventInfo.

        the event location  # noqa: E501

        :param location: The location of this EventInfo.
        :type location: str
        """

        self._location = location

    @property
    def segments(self) -> int:
        """Gets the segments of this EventInfo.

        the number of segments per course (not used yet)  # noqa: E501

        :return: The segments of this EventInfo.
        :rtype: int
        """
        return self._segments

    @segments.setter
    def segments(self, segments: int):
        """Sets the segments of this EventInfo.

        the number of segments per course (not used yet)  # noqa: E501

        :param segments: The segments of this EventInfo.
        :type segments: int
        """

        self._segments = segments

    @property
    def ispractice(self) -> bool:
        """Gets the ispractice of this EventInfo.

        true if this is a practice and does not count towards championship points  # noqa: E501

        :return: The ispractice of this EventInfo.
        :rtype: bool
        """
        return self._ispractice

    @ispractice.setter
    def ispractice(self, ispractice: bool):
        """Sets the ispractice of this EventInfo.

        true if this is a practice and does not count towards championship points  # noqa: E501

        :param ispractice: The ispractice of this EventInfo.
        :type ispractice: bool
        """

        self._ispractice = ispractice

    @property
    def countedruns(self) -> int:
        """Gets the countedruns of this EventInfo.

        if > 0, the number of runs that count towards class position and points  # noqa: E501

        :return: The countedruns of this EventInfo.
        :rtype: int
        """
        return self._countedruns

    @countedruns.setter
    def countedruns(self, countedruns: int):
        """Sets the countedruns of this EventInfo.

        if > 0, the number of runs that count towards class position and points  # noqa: E501

        :param countedruns: The countedruns of this EventInfo.
        :type countedruns: int
        """

        self._countedruns = countedruns
