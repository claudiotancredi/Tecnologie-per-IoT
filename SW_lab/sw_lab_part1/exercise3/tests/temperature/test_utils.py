#!/usr/bin/env python3
"""
Test Converter utilities functions

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
import unittest

# Internals
from app.temperature.utils import celsius, fahrenheit, kelvin

# -------------------------------------------------------------------------


class TestConversion(unittest.TestCase):
    """
    Test if the numeric conversion is done in a correct way
    """
    def test_from_celsius(self):
        """
        Test if the conversion from Celsius to Fahrenheit or Kelvin is correct
        """
        # Try to convert in Fahrenheit
        self.assertEqual(50.0, celsius(10, "F"), "Error converting Celsius to Fahrenheit, 10 C = 50 F")

        # Try to convert in Kelvin
        self.assertEqual(283.15, celsius(10, "K"), "Error converting Celsius to Kelvin, 10 C = 283.15 K")

    def test_from_kelvin(self):
        """
        Test if the conversion from Kelvin to Fahrenheit or Celsius is correct
        """
        # Try to convert in Fahrenheit
        self.assertEqual(50.0, kelvin(283.15, "F"), "Error converting Kelvin to Fahrenheit, 283.15 K = 50 F")

        # Try to convert in Celsius
        self.assertEqual(10.0, kelvin(283.15, "C"), "Error converting Kelvin to Celsius, 283.15 K = 10 C")

    def test_from_fahrenheit(self):
        """
        Test if the conversion from Fahrenheit to Kelvin or Celsius is correct
        """
        # Try to convert in Fahrenheit
        self.assertEqual(10.0, fahrenheit(50, "C"), "Error converting Fahrenheit to Celsius, 50 F = 10 C")

        # Try to convert in Celsius
        self.assertEqual(283.15, fahrenheit(50, "K"), "Error converting Fahrenheit to Kelvin, 50 F = 283.15 K")

# --------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()
