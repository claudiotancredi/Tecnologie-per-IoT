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
        Mount the Exercise3 and The Converter so the engine starts
        """
        # Mount the Endpoint
        cherrypy.tree.mount(Converter(), "/converter", TEMPERATURE_CONFIG)

    def test_exercise3_put(self):
        """
        Test the Only endpoint described in the exercise3 of the lab
        """
        # Generate a correct body
        correct_body = json.dumps(
            {
                "values": [10, 9, 8, 7, 6, 5, 3, 2, 1],
                "originalUnit": "C",
                "targetUnit": "K"
            }
        )

        # Expected response for the correct_body
        expected_response = json.dumps(
            {
                "values": [10, 9, 8, 7, 6, 5, 3, 2, 1],
                "originalUnit": "C",
                "convertedValues": [283.15, 282.15, 281.15, 280.15, 279.15, 278.15, 276.15, 275.15, 274.15],
                "targetUnit": "K"
            }
        )

        # Try the correct PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(correct_body)}")
            ],
            method="PUT", body=correct_body
        )
        self.assertStatus("200 OK")
        self.assertBody(expected_response)

        # Generate incorrect body
        incorrect_keys = json.dumps(
            {
                "values": [10],
                "WRONG": "C",
                "targetUnit": "K"
            }
        )

        # Try incorrect PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(incorrect_keys)}")
            ],
            method="PUT", body=incorrect_keys
        )
        self.assertStatus("400 Bad Request")

        # Generate incorrect body
        incorrect_keys_number = json.dumps(
            {
                "values": [1],
                "WRONG": "C",
            }
        )

        # Try incorrect PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(incorrect_keys_number)}")
            ],
            method="PUT", body=incorrect_keys_number
        )
        self.assertStatus("400 Bad Request")

        # Generate incorrect body
        incorrect_values = json.dumps(
            {
                "values": "NOTANUMBER",
                "WRONG": "K",
            }
        )
        # Try incorrect PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(incorrect_values)}")
            ],
            method="PUT", body=incorrect_values
        )
        self.assertStatus("400 Bad Request")

        # Generate incorrect body
        small_than_absolute_zero = json.dumps(
            {
                "values": [-100000000000000],
                "originalUnit": "C",
                "targetUnit": "K"
            }
        )

        # Try incorrect PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(small_than_absolute_zero)}")
            ],
            method="PUT", body=small_than_absolute_zero
        )
        self.assertStatus("409 Conflict")

        # Generate incorrect body
        no_sense_conversion = json.dumps(
            {
                "values": [10, 9, 8, 7, 6, 5, 3, 2, 1],
                "originalUnit": "C",
                "targetUnit": "C"
            }
        )

        # Try incorrect PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(no_sense_conversion)}")
            ],
            method="PUT", body=no_sense_conversion
        )
        self.assertStatus("409 Conflict")

        # Generate incorrect body
        wrong_scale = json.dumps(
            {
                "values": [10, 9, 8, 7, 6, 5, 3, 2, 1],
                "originalUnit": "Y",
                "targetUnit": "C"
            }
        )

        # Try incorrect PUT
        self.getPage(
            "/converter",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(wrong_scale)}")
            ],
            method="PUT", body=wrong_scale
        )
        self.assertStatus("422 Unprocessable Entity")
