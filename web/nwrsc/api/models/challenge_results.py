# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from nwrsc.api.models.base_model_ import Model
from nwrsc.api.models.challenge_round import ChallengeRound  # noqa: F401,E501
from nwrsc.api import util


class ChallengeResults(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, challengeid: str=None, rounds: List[ChallengeRound]=None):  # noqa: E501
        """ChallengeResults - a model defined in Swagger

        :param challengeid: The challengeid of this ChallengeResults.  # noqa: E501
        :type challengeid: str
        :param rounds: The rounds of this ChallengeResults.  # noqa: E501
        :type rounds: List[ChallengeRound]
        """
        self.swagger_types = {
            'challengeid': str,
            'rounds': List[ChallengeRound]
        }

        self.attribute_map = {
            'challengeid': 'challengeid',
            'rounds': 'rounds'
        }

        self._challengeid = challengeid
        self._rounds = rounds

    @classmethod
    def from_dict(cls, dikt) -> 'ChallengeResults':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ChallengeResults of this ChallengeResults.  # noqa: E501
        :rtype: ChallengeResults
        """
        return util.deserialize_model(dikt, cls)

    @property
    def challengeid(self) -> str:
        """Gets the challengeid of this ChallengeResults.

        the challenge id  # noqa: E501

        :return: The challengeid of this ChallengeResults.
        :rtype: str
        """
        return self._challengeid

    @challengeid.setter
    def challengeid(self, challengeid: str):
        """Sets the challengeid of this ChallengeResults.

        the challenge id  # noqa: E501

        :param challengeid: The challengeid of this ChallengeResults.
        :type challengeid: str
        """

        self._challengeid = challengeid

    @property
    def rounds(self) -> List[ChallengeRound]:
        """Gets the rounds of this ChallengeResults.


        :return: The rounds of this ChallengeResults.
        :rtype: List[ChallengeRound]
        """
        return self._rounds

    @rounds.setter
    def rounds(self, rounds: List[ChallengeRound]):
        """Sets the rounds of this ChallengeResults.


        :param rounds: The rounds of this ChallengeResults.
        :type rounds: List[ChallengeRound]
        """

        self._rounds = rounds