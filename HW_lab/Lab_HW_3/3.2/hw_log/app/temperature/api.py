#!/usr/bin/env python3
"""
Temperature API

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
from collections import deque

# Third Party
import cherrypy

# --------------------------------------------------------------------------------------


#######
# LOG #
#######


@cherrypy.expose
class Log:
    """
    Class that handles the log of the temperature as required from HW lab 3 exercise2
    Typical JSON format :
        {
            "bn": "Yun"

            "e": [
               {
                "n": "temperature",

                "t": <timestamp>,

                "v": value,

                "u": "Cel"

             }
            ]
    }
    """
    def __init__(self):
        """
        Setup the logger using dequeue from collection cause it has an efficiency of O(1)
        in insertion and deletion of elements.
        Giving a maxlength, the deque will detect the oldest
        element at every insertion done after the one
        that made the deque reach the maxlen size
        """
        self._log = deque(maxlen=50)

    @cherrypy.tools.json_out()
    def GET(self):
        """
        Method to retrieve the temperature logs

        :return: a JSON containing the list of logs
        """
        # Thanks to @cherrypy.tools.json_out() the return value will be converted in a valid JSON
        return list(self._log)

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        """
        Method to save the JSON in input as the last element inserted in the log
        """
        # Extract the JSON thanks the @cherrypy.tools.json_in()
        input_json: dict = cherrypy.request.json

        # Check if the JSON has a correct structure
        if input_json.keys() != {"bn", "e"}:
            raise cherrypy.HTTPError(
                status=400,
                message="json keys wrong"
            )

        # Check if the e key of the JSON has a correct structure
        if not isinstance(input_json["e"], list):
            raise cherrypy.HTTPError(
                status=400,
                message="A list has to be associated to json key"
            )

        if len(input_json["e"]) != 1:
            raise cherrypy.HTTPError(
                status=400,
                message="list associated to json key e has a wrong size, correct size must be 1"
            )

        # Extract the dict containing the information from e key
        e: dict = input_json["e"][0]

        # Check if the dict is correct
        if e.keys() != {"n", "t", "v", "u"}:
            raise cherrypy.HTTPError(
                status=400,
                message="list associated to json key e contains a dict with incorrect keys"
            )
        if e["n"] != "temperature":
            raise cherrypy.HTTPError(
                status=400,
                message="The data must be about temperature in celsius"
            )
        if e["v"] < -273.15:
            raise cherrypy.HTTPError(
                status=409,
                message="Value smaller than absolute zero"
            )
        if e["u"] != "Cel":
            raise cherrypy.HTTPError(
                status=400,
                message="Celsius is the default scale for logging"
            )

        # The JSON is correct, append in the log list
        self._log.append(input_json)

        return "OK"
