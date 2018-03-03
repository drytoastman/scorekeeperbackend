# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from nwrsc.api.models.base_model_ import Model
from nwrsc.api import util


class SeriesSettings(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, minevents: int=None, dropevents: int=None, seriesname: str=None, pospointlist: str=None, usepospoints: bool=None, indexafterpenalties: bool=None):  # noqa: E501
        """SeriesSettings - a model defined in Swagger

        :param minevents: The minevents of this SeriesSettings.  # noqa: E501
        :type minevents: int
        :param dropevents: The dropevents of this SeriesSettings.  # noqa: E501
        :type dropevents: int
        :param seriesname: The seriesname of this SeriesSettings.  # noqa: E501
        :type seriesname: str
        :param pospointlist: The pospointlist of this SeriesSettings.  # noqa: E501
        :type pospointlist: str
        :param usepospoints: The usepospoints of this SeriesSettings.  # noqa: E501
        :type usepospoints: bool
        :param indexafterpenalties: The indexafterpenalties of this SeriesSettings.  # noqa: E501
        :type indexafterpenalties: bool
        """
        self.swagger_types = {
            'minevents': int,
            'dropevents': int,
            'seriesname': str,
            'pospointlist': str,
            'usepospoints': bool,
            'indexafterpenalties': bool
        }

        self.attribute_map = {
            'minevents': 'minevents',
            'dropevents': 'dropevents',
            'seriesname': 'seriesname',
            'pospointlist': 'pospointlist',
            'usepospoints': 'usepospoints',
            'indexafterpenalties': 'indexafterpenalties'
        }

        self._minevents = minevents
        self._dropevents = dropevents
        self._seriesname = seriesname
        self._pospointlist = pospointlist
        self._usepospoints = usepospoints
        self._indexafterpenalties = indexafterpenalties

    @classmethod
    def from_dict(cls, dikt) -> 'SeriesSettings':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The SeriesSettings of this SeriesSettings.  # noqa: E501
        :rtype: SeriesSettings
        """
        return util.deserialize_model(dikt, cls)

    @property
    def minevents(self) -> int:
        """Gets the minevents of this SeriesSettings.

        if > 0, the minimum number of events attended to make the championship list  # noqa: E501

        :return: The minevents of this SeriesSettings.
        :rtype: int
        """
        return self._minevents

    @minevents.setter
    def minevents(self, minevents: int):
        """Sets the minevents of this SeriesSettings.

        if > 0, the minimum number of events attended to make the championship list  # noqa: E501

        :param minevents: The minevents of this SeriesSettings.
        :type minevents: int
        """

        self._minevents = minevents

    @property
    def dropevents(self) -> int:
        """Gets the dropevents of this SeriesSettings.

        the number of events that can dropped for calculating championship points  # noqa: E501

        :return: The dropevents of this SeriesSettings.
        :rtype: int
        """
        return self._dropevents

    @dropevents.setter
    def dropevents(self, dropevents: int):
        """Sets the dropevents of this SeriesSettings.

        the number of events that can dropped for calculating championship points  # noqa: E501

        :param dropevents: The dropevents of this SeriesSettings.
        :type dropevents: int
        """

        self._dropevents = dropevents

    @property
    def seriesname(self) -> str:
        """Gets the seriesname of this SeriesSettings.

        the series name  # noqa: E501

        :return: The seriesname of this SeriesSettings.
        :rtype: str
        """
        return self._seriesname

    @seriesname.setter
    def seriesname(self, seriesname: str):
        """Sets the seriesname of this SeriesSettings.

        the series name  # noqa: E501

        :param seriesname: The seriesname of this SeriesSettings.
        :type seriesname: str
        """

        self._seriesname = seriesname

    @property
    def pospointlist(self) -> str:
        """Gets the pospointlist of this SeriesSettings.

        csv list of points assgined when using position for points  # noqa: E501

        :return: The pospointlist of this SeriesSettings.
        :rtype: str
        """
        return self._pospointlist

    @pospointlist.setter
    def pospointlist(self, pospointlist: str):
        """Sets the pospointlist of this SeriesSettings.

        csv list of points assgined when using position for points  # noqa: E501

        :param pospointlist: The pospointlist of this SeriesSettings.
        :type pospointlist: str
        """

        self._pospointlist = pospointlist

    @property
    def usepospoints(self) -> bool:
        """Gets the usepospoints of this SeriesSettings.

        true if points should be calculated based on position, not difference from first  # noqa: E501

        :return: The usepospoints of this SeriesSettings.
        :rtype: bool
        """
        return self._usepospoints

    @usepospoints.setter
    def usepospoints(self, usepospoints: bool):
        """Sets the usepospoints of this SeriesSettings.

        true if points should be calculated based on position, not difference from first  # noqa: E501

        :param usepospoints: The usepospoints of this SeriesSettings.
        :type usepospoints: bool
        """

        self._usepospoints = usepospoints

    @property
    def indexafterpenalties(self) -> bool:
        """Gets the indexafterpenalties of this SeriesSettings.

        true if any index value should be applied after penalties, rather than before  # noqa: E501

        :return: The indexafterpenalties of this SeriesSettings.
        :rtype: bool
        """
        return self._indexafterpenalties

    @indexafterpenalties.setter
    def indexafterpenalties(self, indexafterpenalties: bool):
        """Sets the indexafterpenalties of this SeriesSettings.

        true if any index value should be applied after penalties, rather than before  # noqa: E501

        :param indexafterpenalties: The indexafterpenalties of this SeriesSettings.
        :type indexafterpenalties: bool
        """

        self._indexafterpenalties = indexafterpenalties