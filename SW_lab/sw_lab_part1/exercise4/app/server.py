#!/usr/bin/env python3
"""
Server module
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
# Third Party
import cherrypy

# Setting
from .settings import FREEBOARD_CONFIG, DASHBOARD_PATH
# -----------------------------------------------------------------------------

#############
# FREEBOARD #
#############


class FreeBoard:
    """
    Class that handles FreeBoard dashboard.
    This class  doesn't have a GET method for the index cause its configuration dict has an option to
    export the entire freeboard directory containing the index.html.
    (Look at FREEBOARD_CONFIG in .settings module)
    """
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def saveDashboard(self, **params):
        """
        This endpoint handles the storing of the dashboard in the path
        specified by the exercise4 of the lab.
        The decorator @cherrypy.tools.json_in() wasn't used cause it doesn't support headers with
        "Content-Type" : "application/x-www-form-urlencoded"
        Unfortunately freeboard send the POT request with the url encoded so we must use **params

        :param params: New Configuration of the dashboard to store
        """
        # Check if the Request on server.ip:8080/saveDashboard is a POST
        if cherrypy.request.method != "POST":
            # This endpoint supports only POST Request
            raise cherrypy.HTTPError(status=405, message="Specified method is invalid for this resource")

        # Store the Dashboard in the requested path
        with open(DASHBOARD_PATH, "w") as fp:
            # "json_string" is the key used by Freeboard to store the data in the url
            # there aren't controls about the **params cause this endpoint is called
            # directly by the javascript code of freeboard
            fp.write(params["json_string"])

        # The decorator @cherrypy.tools.json_out() will convert the return in a JSON
        return "STORED"

# ---------------------------------------------------------------------------------------------


def start():
    """
    Start the REST server
    """

    # Mount the Endpoints
    cherrypy.tree.mount(FreeBoard(), "/", FREEBOARD_CONFIG)

    # Update Server Config
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update({"server.socket_port": 8080})
    cherrypy.config.update({"request.show_tracebacks": False})

    # Start the Server
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()
