# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from nwrsc.api.models.base_model_ import Model
from nwrsc.api.models.run import Run  # noqa: F401,E501
from nwrsc.api import util


class ResultEntry(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, driverid: str=None, carid: str=None, firstname: str=None, lastname: str=None, year: str=None, make: str=None, model: str=None, color: str=None, number: int=None, classcode: str=None, indexcode: str=None, indexstr: str=None, useclsmult: bool=None, indexval: float=None, rungroup: int=None, runs: List[List[Run]]=None, net: float=None, pen: float=None, netall: float=None, penall: float=None, position: int=None, diff1: float=None, diffn: float=None, pospoints: int=None, diffpoints: float=None, points: float=None, trophy: bool=None, modified: datetime=None):  # noqa: E501
        """ResultEntry - a model defined in Swagger

        :param driverid: The driverid of this ResultEntry.  # noqa: E501
        :type driverid: str
        :param carid: The carid of this ResultEntry.  # noqa: E501
        :type carid: str
        :param firstname: The firstname of this ResultEntry.  # noqa: E501
        :type firstname: str
        :param lastname: The lastname of this ResultEntry.  # noqa: E501
        :type lastname: str
        :param year: The year of this ResultEntry.  # noqa: E501
        :type year: str
        :param make: The make of this ResultEntry.  # noqa: E501
        :type make: str
        :param model: The model of this ResultEntry.  # noqa: E501
        :type model: str
        :param color: The color of this ResultEntry.  # noqa: E501
        :type color: str
        :param number: The number of this ResultEntry.  # noqa: E501
        :type number: int
        :param classcode: The classcode of this ResultEntry.  # noqa: E501
        :type classcode: str
        :param indexcode: The indexcode of this ResultEntry.  # noqa: E501
        :type indexcode: str
        :param indexstr: The indexstr of this ResultEntry.  # noqa: E501
        :type indexstr: str
        :param useclsmult: The useclsmult of this ResultEntry.  # noqa: E501
        :type useclsmult: bool
        :param indexval: The indexval of this ResultEntry.  # noqa: E501
        :type indexval: float
        :param rungroup: The rungroup of this ResultEntry.  # noqa: E501
        :type rungroup: int
        :param runs: The runs of this ResultEntry.  # noqa: E501
        :type runs: List[List[Run]]
        :param net: The net of this ResultEntry.  # noqa: E501
        :type net: float
        :param pen: The pen of this ResultEntry.  # noqa: E501
        :type pen: float
        :param netall: The netall of this ResultEntry.  # noqa: E501
        :type netall: float
        :param penall: The penall of this ResultEntry.  # noqa: E501
        :type penall: float
        :param position: The position of this ResultEntry.  # noqa: E501
        :type position: int
        :param diff1: The diff1 of this ResultEntry.  # noqa: E501
        :type diff1: float
        :param diffn: The diffn of this ResultEntry.  # noqa: E501
        :type diffn: float
        :param pospoints: The pospoints of this ResultEntry.  # noqa: E501
        :type pospoints: int
        :param diffpoints: The diffpoints of this ResultEntry.  # noqa: E501
        :type diffpoints: float
        :param points: The points of this ResultEntry.  # noqa: E501
        :type points: float
        :param trophy: The trophy of this ResultEntry.  # noqa: E501
        :type trophy: bool
        :param modified: The modified of this ResultEntry.  # noqa: E501
        :type modified: datetime
        """
        self.swagger_types = {
            'driverid': str,
            'carid': str,
            'firstname': str,
            'lastname': str,
            'year': str,
            'make': str,
            'model': str,
            'color': str,
            'number': int,
            'classcode': str,
            'indexcode': str,
            'indexstr': str,
            'useclsmult': bool,
            'indexval': float,
            'rungroup': int,
            'runs': List[List[Run]],
            'net': float,
            'pen': float,
            'netall': float,
            'penall': float,
            'position': int,
            'diff1': float,
            'diffn': float,
            'pospoints': int,
            'diffpoints': float,
            'points': float,
            'trophy': bool,
            'modified': datetime
        }

        self.attribute_map = {
            'driverid': 'driverid',
            'carid': 'carid',
            'firstname': 'firstname',
            'lastname': 'lastname',
            'year': 'year',
            'make': 'make',
            'model': 'model',
            'color': 'color',
            'number': 'number',
            'classcode': 'classcode',
            'indexcode': 'indexcode',
            'indexstr': 'indexstr',
            'useclsmult': 'useclsmult',
            'indexval': 'indexval',
            'rungroup': 'rungroup',
            'runs': 'runs',
            'net': 'net',
            'pen': 'pen',
            'netall': 'netall',
            'penall': 'penall',
            'position': 'position',
            'diff1': 'diff1',
            'diffn': 'diffn',
            'pospoints': 'pospoints',
            'diffpoints': 'diffpoints',
            'points': 'points',
            'trophy': 'trophy',
            'modified': 'modified'
        }

        self._driverid = driverid
        self._carid = carid
        self._firstname = firstname
        self._lastname = lastname
        self._year = year
        self._make = make
        self._model = model
        self._color = color
        self._number = number
        self._classcode = classcode
        self._indexcode = indexcode
        self._indexstr = indexstr
        self._useclsmult = useclsmult
        self._indexval = indexval
        self._rungroup = rungroup
        self._runs = runs
        self._net = net
        self._pen = pen
        self._netall = netall
        self._penall = penall
        self._position = position
        self._diff1 = diff1
        self._diffn = diffn
        self._pospoints = pospoints
        self._diffpoints = diffpoints
        self._points = points
        self._trophy = trophy
        self._modified = modified

    @classmethod
    def from_dict(cls, dikt) -> 'ResultEntry':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ResultEntry of this ResultEntry.  # noqa: E501
        :rtype: ResultEntry
        """
        return util.deserialize_model(dikt, cls)

    @property
    def driverid(self) -> str:
        """Gets the driverid of this ResultEntry.

        the UUID of the driver  # noqa: E501

        :return: The driverid of this ResultEntry.
        :rtype: str
        """
        return self._driverid

    @driverid.setter
    def driverid(self, driverid: str):
        """Sets the driverid of this ResultEntry.

        the UUID of the driver  # noqa: E501

        :param driverid: The driverid of this ResultEntry.
        :type driverid: str
        """

        self._driverid = driverid

    @property
    def carid(self) -> str:
        """Gets the carid of this ResultEntry.

        the UUID of the car  # noqa: E501

        :return: The carid of this ResultEntry.
        :rtype: str
        """
        return self._carid

    @carid.setter
    def carid(self, carid: str):
        """Sets the carid of this ResultEntry.

        the UUID of the car  # noqa: E501

        :param carid: The carid of this ResultEntry.
        :type carid: str
        """

        self._carid = carid

    @property
    def firstname(self) -> str:
        """Gets the firstname of this ResultEntry.

        the driver firstname  # noqa: E501

        :return: The firstname of this ResultEntry.
        :rtype: str
        """
        return self._firstname

    @firstname.setter
    def firstname(self, firstname: str):
        """Sets the firstname of this ResultEntry.

        the driver firstname  # noqa: E501

        :param firstname: The firstname of this ResultEntry.
        :type firstname: str
        """

        self._firstname = firstname

    @property
    def lastname(self) -> str:
        """Gets the lastname of this ResultEntry.

        the driver lastname  # noqa: E501

        :return: The lastname of this ResultEntry.
        :rtype: str
        """
        return self._lastname

    @lastname.setter
    def lastname(self, lastname: str):
        """Sets the lastname of this ResultEntry.

        the driver lastname  # noqa: E501

        :param lastname: The lastname of this ResultEntry.
        :type lastname: str
        """

        self._lastname = lastname

    @property
    def year(self) -> str:
        """Gets the year of this ResultEntry.

        the car year  # noqa: E501

        :return: The year of this ResultEntry.
        :rtype: str
        """
        return self._year

    @year.setter
    def year(self, year: str):
        """Sets the year of this ResultEntry.

        the car year  # noqa: E501

        :param year: The year of this ResultEntry.
        :type year: str
        """

        self._year = year

    @property
    def make(self) -> str:
        """Gets the make of this ResultEntry.

        the car make  # noqa: E501

        :return: The make of this ResultEntry.
        :rtype: str
        """
        return self._make

    @make.setter
    def make(self, make: str):
        """Sets the make of this ResultEntry.

        the car make  # noqa: E501

        :param make: The make of this ResultEntry.
        :type make: str
        """

        self._make = make

    @property
    def model(self) -> str:
        """Gets the model of this ResultEntry.

        the car model  # noqa: E501

        :return: The model of this ResultEntry.
        :rtype: str
        """
        return self._model

    @model.setter
    def model(self, model: str):
        """Sets the model of this ResultEntry.

        the car model  # noqa: E501

        :param model: The model of this ResultEntry.
        :type model: str
        """

        self._model = model

    @property
    def color(self) -> str:
        """Gets the color of this ResultEntry.

        the car color  # noqa: E501

        :return: The color of this ResultEntry.
        :rtype: str
        """
        return self._color

    @color.setter
    def color(self, color: str):
        """Sets the color of this ResultEntry.

        the car color  # noqa: E501

        :param color: The color of this ResultEntry.
        :type color: str
        """

        self._color = color

    @property
    def number(self) -> int:
        """Gets the number of this ResultEntry.

        the car number  # noqa: E501

        :return: The number of this ResultEntry.
        :rtype: int
        """
        return self._number

    @number.setter
    def number(self, number: int):
        """Sets the number of this ResultEntry.

        the car number  # noqa: E501

        :param number: The number of this ResultEntry.
        :type number: int
        """

        self._number = number

    @property
    def classcode(self) -> str:
        """Gets the classcode of this ResultEntry.

        the car classcode (in series classlist)  # noqa: E501

        :return: The classcode of this ResultEntry.
        :rtype: str
        """
        return self._classcode

    @classcode.setter
    def classcode(self, classcode: str):
        """Sets the classcode of this ResultEntry.

        the car classcode (in series classlist)  # noqa: E501

        :param classcode: The classcode of this ResultEntry.
        :type classcode: str
        """

        self._classcode = classcode

    @property
    def indexcode(self) -> str:
        """Gets the indexcode of this ResultEntry.

        the car indexcode (in series indexlist)  # noqa: E501

        :return: The indexcode of this ResultEntry.
        :rtype: str
        """
        return self._indexcode

    @indexcode.setter
    def indexcode(self, indexcode: str):
        """Sets the indexcode of this ResultEntry.

        the car indexcode (in series indexlist)  # noqa: E501

        :param indexcode: The indexcode of this ResultEntry.
        :type indexcode: str
        """

        self._indexcode = indexcode

    @property
    def indexstr(self) -> str:
        """Gets the indexstr of this ResultEntry.

        the displayed indexcode (may have indentifiers such as * if special handling is provided)  # noqa: E501

        :return: The indexstr of this ResultEntry.
        :rtype: str
        """
        return self._indexstr

    @indexstr.setter
    def indexstr(self, indexstr: str):
        """Sets the indexstr of this ResultEntry.

        the displayed indexcode (may have indentifiers such as * if special handling is provided)  # noqa: E501

        :param indexstr: The indexstr of this ResultEntry.
        :type indexstr: str
        """

        self._indexstr = indexstr

    @property
    def useclsmult(self) -> bool:
        """Gets the useclsmult of this ResultEntry.

        true if the flag is set that will selectively apply the classcode multiplier (not common)  # noqa: E501

        :return: The useclsmult of this ResultEntry.
        :rtype: bool
        """
        return self._useclsmult

    @useclsmult.setter
    def useclsmult(self, useclsmult: bool):
        """Sets the useclsmult of this ResultEntry.

        true if the flag is set that will selectively apply the classcode multiplier (not common)  # noqa: E501

        :param useclsmult: The useclsmult of this ResultEntry.
        :type useclsmult: bool
        """

        self._useclsmult = useclsmult

    @property
    def indexval(self) -> float:
        """Gets the indexval of this ResultEntry.

        the compiled index value to use (includes zero or more of class index, car index and class multiplier)  # noqa: E501

        :return: The indexval of this ResultEntry.
        :rtype: float
        """
        return self._indexval

    @indexval.setter
    def indexval(self, indexval: float):
        """Sets the indexval of this ResultEntry.

        the compiled index value to use (includes zero or more of class index, car index and class multiplier)  # noqa: E501

        :param indexval: The indexval of this ResultEntry.
        :type indexval: float
        """

        self._indexval = indexval

    @property
    def rungroup(self) -> int:
        """Gets the rungroup of this ResultEntry.

        the rungroup this entry ran in  # noqa: E501

        :return: The rungroup of this ResultEntry.
        :rtype: int
        """
        return self._rungroup

    @rungroup.setter
    def rungroup(self, rungroup: int):
        """Sets the rungroup of this ResultEntry.

        the rungroup this entry ran in  # noqa: E501

        :param rungroup: The rungroup of this ResultEntry.
        :type rungroup: int
        """

        self._rungroup = rungroup

    @property
    def runs(self) -> List[List[Run]]:
        """Gets the runs of this ResultEntry.

        a two dimensional array of runs, first by course number, then by run number  # noqa: E501

        :return: The runs of this ResultEntry.
        :rtype: List[List[Run]]
        """
        return self._runs

    @runs.setter
    def runs(self, runs: List[List[Run]]):
        """Sets the runs of this ResultEntry.

        a two dimensional array of runs, first by course number, then by run number  # noqa: E501

        :param runs: The runs of this ResultEntry.
        :type runs: List[List[Run]]
        """

        self._runs = runs

    @property
    def net(self) -> float:
        """Gets the net of this ResultEntry.

        the sum net time of the best COUNTED run from each course  # noqa: E501

        :return: The net of this ResultEntry.
        :rtype: float
        """
        return self._net

    @net.setter
    def net(self, net: float):
        """Sets the net of this ResultEntry.

        the sum net time of the best COUNTED run from each course  # noqa: E501

        :param net: The net of this ResultEntry.
        :type net: float
        """

        self._net = net

    @property
    def pen(self) -> float:
        """Gets the pen of this ResultEntry.

        the sum unindexed time of COUNTED runs from each course (includes penalties)  # noqa: E501

        :return: The pen of this ResultEntry.
        :rtype: float
        """
        return self._pen

    @pen.setter
    def pen(self, pen: float):
        """Sets the pen of this ResultEntry.

        the sum unindexed time of COUNTED runs from each course (includes penalties)  # noqa: E501

        :param pen: The pen of this ResultEntry.
        :type pen: float
        """

        self._pen = pen

    @property
    def netall(self) -> float:
        """Gets the netall of this ResultEntry.

        the sum net time of the best run from each course  # noqa: E501

        :return: The netall of this ResultEntry.
        :rtype: float
        """
        return self._netall

    @netall.setter
    def netall(self, netall: float):
        """Sets the netall of this ResultEntry.

        the sum net time of the best run from each course  # noqa: E501

        :param netall: The netall of this ResultEntry.
        :type netall: float
        """

        self._netall = netall

    @property
    def penall(self) -> float:
        """Gets the penall of this ResultEntry.

        the sum unindexed time of the best run from each course (includes penalties)  # noqa: E501

        :return: The penall of this ResultEntry.
        :rtype: float
        """
        return self._penall

    @penall.setter
    def penall(self, penall: float):
        """Sets the penall of this ResultEntry.

        the sum unindexed time of the best run from each course (includes penalties)  # noqa: E501

        :param penall: The penall of this ResultEntry.
        :type penall: float
        """

        self._penall = penall

    @property
    def position(self) -> int:
        """Gets the position of this ResultEntry.

        the finishing position in class  # noqa: E501

        :return: The position of this ResultEntry.
        :rtype: int
        """
        return self._position

    @position.setter
    def position(self, position: int):
        """Sets the position of this ResultEntry.

        the finishing position in class  # noqa: E501

        :param position: The position of this ResultEntry.
        :type position: int
        """

        self._position = position

    @property
    def diff1(self) -> float:
        """Gets the diff1 of this ResultEntry.

        the difference in time to first place: (net1 - netx)/indexval  # noqa: E501

        :return: The diff1 of this ResultEntry.
        :rtype: float
        """
        return self._diff1

    @diff1.setter
    def diff1(self, diff1: float):
        """Sets the diff1 of this ResultEntry.

        the difference in time to first place: (net1 - netx)/indexval  # noqa: E501

        :param diff1: The diff1 of this ResultEntry.
        :type diff1: float
        """

        self._diff1 = diff1

    @property
    def diffn(self) -> float:
        """Gets the diffn of this ResultEntry.

        the difference in time to the next position: (netn - netx)/indexval  # noqa: E501

        :return: The diffn of this ResultEntry.
        :rtype: float
        """
        return self._diffn

    @diffn.setter
    def diffn(self, diffn: float):
        """Sets the diffn of this ResultEntry.

        the difference in time to the next position: (netn - netx)/indexval  # noqa: E501

        :param diffn: The diffn of this ResultEntry.
        :type diffn: float
        """

        self._diffn = diffn

    @property
    def pospoints(self) -> int:
        """Gets the pospoints of this ResultEntry.

        the championship points for the current position  # noqa: E501

        :return: The pospoints of this ResultEntry.
        :rtype: int
        """
        return self._pospoints

    @pospoints.setter
    def pospoints(self, pospoints: int):
        """Sets the pospoints of this ResultEntry.

        the championship points for the current position  # noqa: E501

        :param pospoints: The pospoints of this ResultEntry.
        :type pospoints: int
        """

        self._pospoints = pospoints

    @property
    def diffpoints(self) -> float:
        """Gets the diffpoints of this ResultEntry.

        the championship points based on difference from first  # noqa: E501

        :return: The diffpoints of this ResultEntry.
        :rtype: float
        """
        return self._diffpoints

    @diffpoints.setter
    def diffpoints(self, diffpoints: float):
        """Sets the diffpoints of this ResultEntry.

        the championship points based on difference from first  # noqa: E501

        :param diffpoints: The diffpoints of this ResultEntry.
        :type diffpoints: float
        """

        self._diffpoints = diffpoints

    @property
    def points(self) -> float:
        """Gets the points of this ResultEntry.

        one of pospoints or diffpoints depending on the series settings  # noqa: E501

        :return: The points of this ResultEntry.
        :rtype: float
        """
        return self._points

    @points.setter
    def points(self, points: float):
        """Sets the points of this ResultEntry.

        one of pospoints or diffpoints depending on the series settings  # noqa: E501

        :param points: The points of this ResultEntry.
        :type points: float
        """

        self._points = points

    @property
    def trophy(self) -> bool:
        """Gets the trophy of this ResultEntry.

        true if this position is awarded a trophy for the event  # noqa: E501

        :return: The trophy of this ResultEntry.
        :rtype: bool
        """
        return self._trophy

    @trophy.setter
    def trophy(self, trophy: bool):
        """Sets the trophy of this ResultEntry.

        true if this position is awarded a trophy for the event  # noqa: E501

        :param trophy: The trophy of this ResultEntry.
        :type trophy: bool
        """

        self._trophy = trophy

    @property
    def modified(self) -> datetime:
        """Gets the modified of this ResultEntry.

        the mod time  # noqa: E501

        :return: The modified of this ResultEntry.
        :rtype: datetime
        """
        return self._modified

    @modified.setter
    def modified(self, modified: datetime):
        """Sets the modified of this ResultEntry.

        the mod time  # noqa: E501

        :param modified: The modified of this ResultEntry.
        :type modified: datetime
        """

        self._modified = modified
