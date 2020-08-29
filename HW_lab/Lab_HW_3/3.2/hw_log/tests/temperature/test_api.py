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
from app.temperature.api import Log
from app.temperature.settings import TEMPERATURE_CONFIG

# ----------------------------------------------------------------------------------------------


class TestLog(helper.CPWebCase):
    """
    Class that handles the unittest for the Converter API, using
    cherrypy helper test functions
    """

    @classmethod
    def setup_server(cls):
        """
        Setup the Server containing Temperature API
        """
        # Mount the Endpoint
        cherrypy.tree.mount(Log(), "/temperature/log", TEMPERATURE_CONFIG)

    def test_log(self):
        """
        Test the log required from HW lab
        """
        # Try a GET
        self.getPage("/temperature/log")
        self.assertStatus("200 OK")
        self.assertBody("[]")

        # Generate a correct body
        correct_body = json.dumps(
            {
                "bn": "Yun",
                "e": [
                    {
                        "n": "temperature",
                        "t": 110,
                        "v": 10,
                        "u": "Cel"
                    }
                ]
            }
        )

        # Generate the expected_answer
        expected_answer = f"[{correct_body}]"

        # Update the Log
        self.getPage(
            "/temperature/log",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(correct_body)}")
            ],
            method="POST", body=correct_body
        )

        self.assertStatus("200 OK")
        self.assertBody('''"OK"''')

        # Get the Log
        self.getPage("/temperature/log")
        self.assertStatus("200 OK")
        self.assertBody(expected_answer)

        # Generate incorrect body
        incorrect_body = json.dumps(
            {
                "WRONG": "Yun",
                "e":
                    {
                        "Wrong": "temperature",
                        "t": 110,
                        "v": 10,
                        "u": "Cel"
                    }

            }
        )

        self.getPage(
            "/temperature/log",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(incorrect_body)}")
            ],
            method="POST", body=incorrect_body
        )
        self.assertStatus("400 Bad Request")

        # Generate a  absolute_zero_body
        absolute_zero_body = json.dumps(
            {
                "bn": "Yun",
                "e": [
                    {
                        "n": "temperature",
                        "t": 110,
                        "v": -1000000000000,
                        "u": "Cel"
                    }
                ]
            }
        )
        self.getPage(
            "/temperature/log",
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Length", f"{len(absolute_zero_body)}")
            ],
            method="POST", body=absolute_zero_body
        )
        self.assertStatus("409 Conflict")














