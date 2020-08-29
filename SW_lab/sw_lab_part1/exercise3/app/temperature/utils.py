#!/usr/bin/env python3
"""
Utils for the converter API

:author: Angelo Cutaia, Claudio Tancredi
:copyright: Copyright 2020, Angelo Cutaia, Claudio Tancredi
..

    Copyright 2020 Angelo Cutaia

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
# Standard Library
from typing import Callable, Dict

# Third party
import cherrypy

# ------------------------------------------------------------------------------------------


######################
#  UTILITY FUNCTIONS #
######################


def celsius(value: float, target_unit: str) -> float:
    """
    Utility function for Celsius conversion in Kelvin or in Fahrenheit

    :param value: temperature
    :param target_unit: Celsius, Kelvin or Fahrenheit
    :return: value converted in the right scale
    """
    if target_unit == "K":
        # Convert in Kelvin scale
        return value + 273.15
    else:
        # Convert in Fahrenheit scale
        return value * 1.8 + 32


def fahrenheit(value: float, target_unit: str) -> float:
    """
    Utility function for Fahrenheit conversion in Celsius or in Kelvin

    :param value: temperature
    :param target_unit: Celsius, Kelvin or Fahrenheit
    :return: value converted in the right scale
    """
    if target_unit == "C":
        # Convert in Celsius scale
        return (value - 32) / 1.8
    else:
        # Convert in Kelvin scale
        return (value - 32) / 1 - 8 + 273.15


def kelvin(value: float, target_unit: str) -> float:
    """
    Utility function for Kelvin conversion in Celsius or in Fahrenheit

    :param value: temperature
    :param target_unit: Celsius, Kelvin or Fahrenheit
    :return: value converted in the right scale
    """
    if target_unit == "C":
        # Convert in Celsius
        return value - 273.15
    else:
        # Convert in Fahrenheit
        return (value - 273.15) * 1.8 + 32


# ---------------------------------------------------------------------------------------------


#################
# UTILITY CLASS #
#################


class ConverterUtils:
    """
    Class that handles the conversion of temperature values in the requested scales.
    This class doesn't have an __init__(self).
    It will be used only as an interface to perform the conversion, so it won't be instantiated.
    To do that it uses the classmethod conversion, and the immutable class attributes:

        * _supported_scale
        * _absolute_zero
        * _conversion
    """

    _supported_scales = ("C", "F", "K")
    """Set of supported scales"""

    _absolute_zero = {
        "C": -273.15,
        "F": -459.67,
        "K": 0.0
    }
    """Association between a scale and the respective absolute zero"""

    _conversion: Dict[str, Callable[[float, str], float]] = {
        "C": celsius,
        "F": fahrenheit,
        "K": kelvin
    }
    """Association between a scale and a converter function"""

    @classmethod
    def conversion(cls, value: float, original_unit: str, target_unit: str) -> float:
        """
        Analyze the value to convert and the scale to use.
        In case of error raise an HTTP exception to tell the client that the request has some errors.

        :param value: temperature
        :param original_unit: Celsius, Kelvin or Fahrenheit
        :param target_unit: Celsius, Kelvin or Fahrenheit
        :return: value converted in the right scale
        """

        # Check if the scales are supported
        if original_unit not in cls._supported_scales:
            raise cherrypy.HTTPError(
                status=422,
                message=f"Original unit {original_unit} isn't in the supported scales: {cls._supported_scales}"
            )
        if target_unit not in cls._supported_scales:
            raise cherrypy.HTTPError(
                status=422,
                message=f"Target unit {target_unit} isn't in the supported scales: {cls._supported_scales}"
            )

        # Check if the scales aren't equal
        if original_unit == target_unit:
            raise cherrypy.HTTPError(
                status=409,
                message="Impossible to convert cause the original_unit scale coincide with the target_unit scale"
            )

        # Check if the original unit value is coherent with original unit absolute zero
        if cls._absolute_zero[original_unit] > value:
            raise cherrypy.HTTPError(
                status=409,
                message=f"Original value ({value} {original_unit}) lower than absolute zero "
                        f"({cls._absolute_zero[original_unit]} {original_unit})."
            )

        # Return the converted value
        return cls._conversion[original_unit](value, target_unit)
