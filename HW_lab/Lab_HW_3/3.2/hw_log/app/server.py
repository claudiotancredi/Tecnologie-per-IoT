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

# Internal
from .temperature.api import Log

# Setting
from .temperature.settings import TEMPERATURE_CONFIG

# -----------------------------------------------------------------------------


def start():
    """
    Start the REST server
    """

    # Mount the Endpoints
    cherrypy.tree.mount(Log(), "/temperature/log", TEMPERATURE_CONFIG)

    # Update Server Config
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update({"server.socket_port": 8080})
    cherrypy.config.update({"request.show_tracebacks": False})

    # Start the Server
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()
