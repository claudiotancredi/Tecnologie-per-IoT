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

# Third Party
import cherrypy

# Internal
from .utils import ConverterUtils

# --------------------------------------------------------------------------------------


#############
# CONVERTER #
#############


@cherrypy.expose
class Converter:
    """
    Class that handles the exercise2 of the lab
    """

    @cherrypy.tools.json_out()
    def GET(self, *uri):
        """
        Endpoint that takes path elements to perform the temperature conversion

        :return: a JSON with the value converted in the desired scale.
        In case of error, a JSON with the error description and its details is provided
        """
        # Check if the path elements number is correct
        if len(uri) != 3:
            # Wrong uri number
            raise cherrypy.HTTPError(
                status=400,
                message=f"Path's elements number not correct. Three parameters are required."
            )

        # Check if the element 0 of the path is a number
        try:
            value = float(uri[0])
        except ValueError:
            # The uri element 'value' isn't a number
            raise cherrypy.HTTPError(
                status=400,
                message=f"Query parameter value: {uri[0]} isn't a number"
            )

        # Extract original unit and target unit from the path
        original_unit = uri[1]
        target_unit = uri[2]

        # Convert the value in the target unit. In case of an error the conversion method will warn the client
        converted_value = ConverterUtils.conversion(value, original_unit, target_unit)

        # Return the JSON to the client
        # the decorator above GET method: @cherrypy.tools.json_out()
        # will automatic convert the dict in a valid JSON
        return {
            "value": value,
            "originalUnit": original_unit,
            "convertedValue": converted_value,
            "targetUnit": target_unit
        }
