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
    Class that handles the exercise3 of the lab
    """

    _valid_json_keys = {"values", "originalUnit", "targetUnit"}
    """Store the keys for valid JSON input"""

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        """
        Endpoint that takes a JSON body sent by the client to perform the temperature conversion
        for a list of values

        :return: a JSON with the values converted in the desired scale.
            In case of error, a JSON with the error description and its details is provided
        """
        # The decorator @cherrypy.tools.json_in()
        # automatically convert the JSON sent by the client
        # In case the body sent by the client isn't a JSON it will reply automatically with a code 400
        input_json: dict = cherrypy.request.json

        # Check if the input_json has correct keys
        if not self._valid_json_keys == input_json.keys():
            # Wrong keys
            raise cherrypy.HTTPError(
                status=400,
                message=f"Json keys are not correct. Those keys are required: "
                        f"values, originalUnit, targetUnit"
            )

        # Extract the scales
        original_unit = input_json["originalUnit"]
        target_unit = input_json["targetUnit"]

        # Extract the list of values to convert
        values_list = input_json["values"]

        # Check if the values to convert are well formatted
        if not isinstance(values_list, list):
            raise cherrypy.HTTPError(
                status=400,
                message=f"The values to convert must be a list of numbers."
            )

        # Check if every element in the list of values is a number
        for element in values_list:
            if not isinstance(element, (int, float)):
                # This element to convert isn't a number
                raise cherrypy.HTTPError(
                    status=400,
                    message=f"List of values incorrect, not every element to convert is a number. "
                            f"Only numbers can be converted between scales"
                )

        # Return the JSON to the client
        # the decorator above PUT method: @cherrypy.tools.json_out()
        # will automatic convert the dict in a valid JSON
        return {
            "values": values_list,
            "originalUnit": original_unit,

            # Using list comprehension for performance purposes and to not repeat code
            "convertedValues": [
                ConverterUtils.conversion(value, original_unit, target_unit)
                for value in values_list
            ],
            "targetUnit": target_unit
        }
