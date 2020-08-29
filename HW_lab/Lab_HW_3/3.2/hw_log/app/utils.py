#!/usr/bin/env python3
"""
Utilities module for the REST server

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

# --------------------------------------------------------------------------------------


def jsonify_error(status: str, message: str, **traceback: dict) -> str:
    """
    Utility function that turns every exception raised using cherrypy.HTTPError
    in a json. The purpose of this function is to replace the default behavior of cherrypy in case of an error
    (sending an HTML page with the description of the error and the traceback of the exception)

    :param status: HTTP code of the error
    :param message: Description of the error
    :param traceback: Traceback of the error ( it will be ignored by default)
    :return: a JSON containing the error and its description
    """
    # Take the response generation of cherrypy in case of error
    response = cherrypy.response

    # Add the JSON Header
    response.headers['Content-Type'] = 'application/json'

    # Return the JSON with all the informations
    return json.dumps(
        {
            'status': 'Failure',
            'status_details': {
                'message': status,
                'description': message
            }
        }
    )
