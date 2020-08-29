#!/usr/bin/env python3
"""
Test Converter API

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
import json

# Third Party
import cherrypy
from cherrypy.test import helper

# Internals
from app.temperature.api import Converter
from app.temperature.settings import TEMPERATURE_CONFIG

# ----------------------------------------------------------------------------------------------


class TestConverter(helper.CPWebCase):
    """
    Class that handles the unittest for the Converter API, using
    cherrypy helper test functions
    """

    @classmethod
    def setup_server(cls):
        """
        Setup the Server containing Converter API,
        Mount the Exercise2 and The Converter so the engine starts
        """
        # Mount the Endpoint
        cherrypy.tree.mount(Converter(), "/converter", TEMPERATURE_CONFIG)

    def test_exercise2_get(self):
        """
        Test the Only endpoint described in the exercise2 of the lab
        """
        # Try a correct GET path
        self.getPage("/converter/10/C/K")
        self.assertStatus("200 OK")
        self.assertBody("""{"value": 10.0, "originalUnit": "C", "convertedValue": 283.15, "targetUnit": "K"}""")

        # Try incorrect GET path
        self.getPage("/converter/10/C/L")  # incorrect target unit
        self.assertStatus("422 Unprocessable Entity")

        self.getPage("/converter/10/L/K")  # incorrect origin unit
        self.assertStatus("422 Unprocessable Entity")

        self.getPage("/converter/NOTANUMBER/C/K")  # incorrect value
        self.assertStatus("400 Bad Request")

        self.getPage("/converter/10/C")  # Wrong number of path parameters
        self.assertStatus("400 Bad Request")

        # Try incorrect GET with path values that will generate conflicts
        self.getPage("/converter/-10000000000000000/C/K")  # Value < Absolute 0
        self.assertStatus("409 Conflict")

        self.getPage("/converter/10/C/C")  # Try to convert Celsius in Celsius
        self.assertStatus("409 Conflict")














