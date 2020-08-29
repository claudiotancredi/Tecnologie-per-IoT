#!/usr/bin/env python3
"""
Settings for the catalog API

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

# Internals
from ..utils import jsonify_error

# --------------------------------------------------------------------------------------------------


CATALOG_CONFIG = {
    "/": {
        "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
        "tools.sessions.on": True,
        # Replace the default error handler
        "error_page.default": jsonify_error
    }
}
"""Configuration of the Catalog API"""

NO_AUTORELOAD = {"global": {"engine.autoreload.on": False}}
