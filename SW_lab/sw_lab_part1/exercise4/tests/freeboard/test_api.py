#!/usr/bin/env python3
"""
Test Freeboard API

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
from urllib.parse import urlencode

# Third Party
import cherrypy
from cherrypy.test import helper

# Internals
from app.server import FreeBoard
from app.settings import FREEBOARD_CONFIG, DASHBOARD_PATH

# ----------------------------------------------------------------------------------------------


class TestFreeboard(helper.CPWebCase):
    """
    Class that handles the unittest for the FreeBoard API, using
    cherrypy helper test functions
    """

    @classmethod
    def setup_server(cls):
        """
        Setup the Server containing Freeboard API,
        Mount Freeboard so the engine starts
        """
        # Mount the Endpoints
        cherrypy.tree.mount(FreeBoard(), "/", FREEBOARD_CONFIG)

    def test_get(self):
        """
        Test the first part of exercise4
        """
        # Open the index.html file and store it
        with open("".join((FREEBOARD_CONFIG["/"]["tools.staticdir.dir"], "/index.html")), "r") as fp:
            index_html = fp.read()

        # Try to GET the index
        self.getPage("/")
        self.assertStatus("200 OK")
        # Check if the body is correct
        self.assertBody(index_html, "Error getting index.html from freeboard directory")

    def test_saveDashboard(self):
        """
        Test the second part of exercise4
        """
        # Open the index.html file and store it
        with open(DASHBOARD_PATH, "r") as fp:
            dashboard = fp.read()

        body = urlencode({"json_string": dashboard})
        # Try save the page
        self.getPage(
            "/saveDashboard",
            headers=[
                ("Content-Type", "application/x-www-form-urlencoded"),
                ("Content-Length", f"{len(body)}")
            ],
            method="POST", body=body
        )
        self.assertStatus("200 OK")
        # Check if the body is correct
        self.assertBody('''"STORED"''')


