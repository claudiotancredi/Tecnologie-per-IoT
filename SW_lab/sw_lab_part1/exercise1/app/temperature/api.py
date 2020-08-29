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
# EXERCISE1 #
#############


@cherrypy.expose
class Converter:
    """
    Class that handles only the exercise1 of the lab
    """

    @cherrypy.tools.json_out()
    def GET(self, **params):
        """
        Endpoint that takes query parameters to perform the temperature conversion

        :return: a JSON with the value converted in the desired scale.
        In case of error, a JSON with the error description and its details is provided.
        """

        # Check if the parameters number is correct
        if len(params) != 3:

            # Wrong params number
            raise cherrypy.HTTPError(
                status=400,
                message=f"Query's parameters number not correct. Three parameters are required: "
                        f"value, originalUnit, targetUnit"
            )

        # Extract the parameters keys, in case of the keys aren't the expected ones, raise an exception
        try:

            value = float(params["value"])  # if the value isn't a number it will raise a ValueError
            original_unit = params["originalUnit"]
            target_unit = params["targetUnit"]

        except KeyError:
            # At least one key is incorrect
            raise cherrypy.HTTPError(
                status=400,
                message=f"Query's keys are not correct. These keys are required: "
                        f"value, originalUnit, targetUnit"

            )

        except ValueError:
            # The key value isn't a number
            raise cherrypy.HTTPError(
                status=400,
                message=f"Query parameter value: {params['value']} isn't a number"
            )

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
