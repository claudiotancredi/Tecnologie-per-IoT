#!/usr/bin/env python3
"""
Catalog API

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
# Third Parties
import cherrypy

# Internals
from .database import DataBase


# --------------------------------------------------------------------------------------


##########
# BROKER #
##########


@cherrypy.expose
class Broker:
    """Broker endpoint"""

    __ip__ = "test.mosquitto.org"
    __port__ = 1883

    @cherrypy.tools.json_out()
    def GET(self):
        """Get Broker info"""
        return {"ip": self.__ip__, "port": self.__port__}


# --------------------------------------------------------------------------------------


##########
# DEVICE #
##########


@cherrypy.expose
class Device:
    """Device endpoints"""

    __mqtt_and_rest__ = {"ID", "PROT", "MQTT", "REST"}
    __generic_protocol_keys__ = {"IP", "P", "ED", "AR"}

    __generic_device_keys__ = {"ID", "PROT", "IP", "P", "ED", "AR"}

    __protocols_actions__ = {
        "REST": {"S": "GET", "A": "POST"},
        "MQTT": {"S": "subscribe", "A": "publish"}
    }

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri):
        """Insert a device, if already inserted, update it"""

        # The decorator @cherrypy.tools.json_in()
        # automatically convert the JSON sent by the client
        # In case the body sent by the client isn't a JSON it will reply automatically with a code 400
        def _parse(protocols, paths, id, ip, port):
            """
            Inner function used to parse the endpoint and extract info
            """
            if protocols == "REST":
                return [f"http://{ip}:{port}/{path}" for path in paths]

            elif protocols == "MQTT":
                return [f"{path}/{id}" for path in paths]

        if len(uri) != 0:
            raise cherrypy.HTTPError(status=400,)

        input_json: dict = cherrypy.request.json
        # Check if the JSON has correct keys
        if set(input_json.keys()) == self.__mqtt_and_rest__:
            if input_json["PROT"] != "BOTH":
                # Wrong keys
                raise cherrypy.HTTPError(
                    status=400,
                    message=f"JSON keys are not correct."
                    f"For a device with both MQTT and Rest, these keys are accepted: "
                    f"{self.__mqtt_and_rest__}"
                )

            # Check if the MQTT and REST protocol have inside correct keys
            if (
                set(input_json["MQTT"].keys()) != self.__generic_protocol_keys__
                or set(input_json["REST"].keys()) != self.__generic_protocol_keys__
            ):
                # Wrong keys
                raise cherrypy.HTTPError(
                    status=400,
                    message=f"JSON keys are not correct."
                    f"For a device with both MQTT and Rest, these inner keys are accepted: "
                    f"{self.__generic_protocol_keys__}"
                )

            # Check if the data of the available resources are well formatted
            for protocol in {"MQTT", "REST"}:
                if type(input_json[protocol]["AR"]) != list:
                    raise cherrypy.HTTPError(
                        status=400,
                        message="Available Resources must be a list of strings",
                    )
            for resource in input_json[protocol]["AR"]:
                if type(resource) != str:
                    raise cherrypy.HTTPError(
                        status=400,
                        message="Available Resources must be a list of strings",
                    )

            # Check if the end_points are well formatted
            if type(input_json[protocol]["ED"]) != dict:
                raise cherrypy.HTTPError(
                    status=400,
                    message="End_points must be a dict with values of type list of strings",
                )
            for end_point in input_json[protocol]["ED"]:
                if type(input_json[protocol]["ED"][end_point]) != list:
                    raise cherrypy.HTTPError(
                        status=400, message="End_points must be a list of strings"
                    )
                for element in input_json[protocol]["ED"][end_point]:
                    if type(element) != str:
                        raise cherrypy.HTTPError(
                            status=400, message="End_points must be a list of strings"
                        )

            # Data correct, extract them and add the device to the database
            try:
                DataBase.insert_device(
                    str(input_json["ID"]),
                    end_points={
                        protocol: {
                            "ip": str(input_json[protocol]["IP"]),
                            "port": int(input_json[protocol]["P"]),
                            "end_points": {
                                self.__protocols_actions__[protocol][end_point]: _parse(
                                    protocol,
                                    input_json[protocol]["ED"][end_point],
                                    str(input_json["ID"]),
                                    str(input_json[protocol]["IP"]),
                                    int(input_json[protocol]["P"])
                                )
                                for end_point in input_json[protocol]["ED"]
                            },
                        }
                        for protocol in {"MQTT", "REST"}
                    },
                    available_resources={
                        protocol: input_json[protocol]["AR"]
                        for protocol in {"MQTT", "REST"}
                    }
                )
                return {"device": "added"}
            except Exception:
                #  Something went wrong
                raise cherrypy.HTTPError(
                    status=400, message="Something went wrong while adding the device"
                )

        # Check if the JSON has correct keys
        elif set(input_json.keys()) != self.__generic_device_keys__:
            # Wrong keys
            raise cherrypy.HTTPError(
                status=400,
                message=f"JSON keys are not correct."
                f"For a device these keys are accepted: "
                f"{self.__generic_device_keys__}"
            )

        # Check if the protocol is REST or MQTT
        if not input_json["PROT"] in {"MQTT", "REST"}:
            # Wrong protocol
            raise cherrypy.HTTPError(
                status=400, message="Only MQTT and REST protocols are supported"
            )

        # Check if the data of the available resources are well formatted
        if type(input_json["AR"]) != list:
            raise cherrypy.HTTPError(
                status=400, message="Available Resources must be a list of strings"
            )
        for resource in input_json["AR"]:
            if type(resource) != str:
                raise cherrypy.HTTPError(
                    status=400, message="Available Resources must be a list of strings"
                )

        # Check if the data of the end_points are well formatted
        if type(input_json["ED"]) != dict:
            raise cherrypy.HTTPError(
                status=400,
                message="End_points must be a dict with values of type list of strings",
            )
        for end_point in input_json["ED"]:
            if type(input_json["ED"][end_point]) != list:
                raise cherrypy.HTTPError(
                    status=400, message="End_points must be a list of strings"
                )
            for value in input_json["ED"][end_point]:
                if type(value) != str:
                    raise cherrypy.HTTPError(
                        status=400, message="End_points must be a list of strings"
                    )
        # Data correct, extract them and add the device to the database
        try:
            DataBase.insert_device(
                deviceID=str(input_json["ID"]),
                end_points={
                    input_json["PROT"]: {
                        "ip": str(input_json["IP"]),
                        "port": int(input_json["P"]),
                        "end_points": {
                            self.__protocols_actions__[input_json["PROT"]][
                                end_point
                            ]: _parse(
                                input_json["PROT"],
                                input_json["ED"][end_point],
                                str(input_json["ID"]),
                                str(input_json["IP"]),
                                int(input_json["P"])
                            )
                            for end_point in input_json["ED"]
                        }
                    }
                },
                available_resources={input_json["PROT"]: input_json["AR"]},
            )
            return {"device": "added"}
        except Exception:
            # Wrong values
            raise cherrypy.HTTPError(
                status=400, message="Something went wrong while adding the device"
            )

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        """
        Get device, or devices list

        :param uri: path
        :param params: body, must be None
        :return: Device or devices info
        """
        if len(uri) != 1 or params:
            # Wrong uri number or body inside the request
            raise cherrypy.HTTPError(
                status=400,
                message=f"Path's elements number not correct or body inside the request. "
                f"One parameter is required, no body is allowed.",
            )
        if uri[0] == "all":
            # Extract all the registered devices
            devices = DataBase.get_all_devices()
            if devices:
                return devices
            else:
                # No devices found
                raise cherrypy.HTTPError(status=404, message=f"No devices found. ")
        else:
            # Extract the device with id = uri[0]
            device = DataBase.get_device(uri[0])
            if device:
                return device
            else:
                # No device with such ID found
                raise cherrypy.HTTPError(
                    status=404, message=f"No device with deviceID = {uri[0]} found. "
                )


# --------------------------------------------------------------------------------------


########
# USER #
########


@cherrypy.expose
class User:
    """User Endpoints"""

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri):
        """Insert a user, if already inserted, update it"""

        # The decorator @cherrypy.tools.json_in()
        # automatically convert the JSON sent by the client
        # In case the body sent by the client isn't a JSON it will reply automatically with a code 400
        if len(uri) != 0:
            raise cherrypy.HTTPError(status=400)

        input_json: dict = cherrypy.request.json
        # Check if the json is well formatted
        if set(input_json.keys()) != {"userID", "name", "surname", "email_addresses"}:
            raise cherrypy.HTTPError(status=400, message="Wrong JSON keys")

        # Check if the email format is correct
        if type(input_json["email_addresses"]) != dict and not set(
            input_json["email_addresses"].keys()
        ).issubset({"WORK", "PERSONAL"}):
            raise cherrypy.HTTPError(
                status=400,
                message="Email addresses must be a dict with keys: 'WORK', 'PERSONAL' or both",
            )
        for key in input_json["email_addresses"]:
            if type(input_json["email_addresses"][key]) != str:
                raise cherrypy.HTTPError(
                    status=400, message="Wrong values of the JSON keys."
                )
        # Insert user
        try:
            DataBase.insert_user(
                str(input_json["userID"]),
                str(input_json["name"]),
                str(input_json["surname"]),
                input_json["email_addresses"]
            )
            return {"user": "added"}

        except Exception:
            raise cherrypy.HTTPError(
                status=400, message="Something went wrong while adding the user"
            )

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        """
        Get user, or users list

        :param uri: path
        :param params: body, must be None
        :return: User or users info
        """
        if len(uri) != 1 or params:
            # Wrong uri number or body inside the request
            raise cherrypy.HTTPError(
                status=400,
                message=f"Path's elements number not correct or body inside the request. "
                f"One parameter is required, no body is allowed.",
            )
        if uri[0] == "all":
            # Extract all the registered users
            users = DataBase.get_all_users()
            if users:
                return users
            else:
                # No user found
                raise cherrypy.HTTPError(status=404, message=f"No user found. ")
        else:
            # Extract the user with id = uri[0]
            user = DataBase.get_user(uri[0])
            if user:
                return user
            else:
                # No user with such ID found
                raise cherrypy.HTTPError(
                    status=404, message=f"No user with userID = {uri[0]} found. "
                )


# --------------------------------------------------------------------------------------


###########
# SERVICE #
###########


@cherrypy.expose
class Service:
    """Service Endpoints"""

    _end_points_ = {
        "MQTT": {"broker", "subscribe", "publish"},
        "REST": {"GET", "POST", "PUT", "PATCH", "HEAD", "DELETE"}
    }

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri):
        """Insert a service, if already inserted, update it"""

        # The decorator @cherrypy.tools.json_in()
        # automatically convert the JSON sent by the client
        # In case the body sent by the client isn't a JSON it will reply automatically with a code 400
        if len(uri) != 0:
            raise cherrypy.HTTPError(status=400)

        input_json: dict = cherrypy.request.json
        # Check if the JSON is well formatted
        if set(input_json.keys()) != {"serviceID", "description", "end_points"}:
            raise cherrypy.HTTPError(status=400, message="Wrong json keys")

        # Check if the end_points are well formatted
        end_points = input_json["end_points"]
        if type(end_points) != dict:
            raise cherrypy.HTTPError(status=400, message="End_points bad formatted")
        # Check if the end_points are MQTT, REST or both
        if not set(end_points.keys()).issubset({"MQTT", "REST"}):
            raise cherrypy.HTTPError(
                status=400, message="End_points keys must be: 'MQTT', 'REST' or both"
            )

        # Check if the MQTT and REST end_points are formatted well
        for protocol in {"MQTT", "REST"}:
            if protocol in end_points:
                if not set(end_points[protocol].keys()).issubset(
                    self._end_points_[protocol]
                ):
                    raise cherrypy.HTTPError(
                        status=400, message="End_points bad formatted"
                    )
                for key in end_points[protocol]:
                    if key == "broker":
                        if type(end_points[protocol][key]) != dict:
                            raise cherrypy.HTTPError(
                                status=400, message="End_points bad formatted"
                            )
                        if set(end_points[protocol][key].keys()) != {"ip", "port"}:
                            raise cherrypy.HTTPError(
                                status=400, message="End_points bad formatted"
                            )

                    if type(end_points[protocol][key]) != list and key != "broker":
                        raise cherrypy.HTTPError(
                            status=400, message="End_points bad formatted"
                        )
        # Try to insert the service informations in the database
        try:
            DataBase.insert_service(
                str(input_json["serviceID"]),
                str(input_json["description"]),
                input_json["end_points"]
            )
            return {"service": "added"}

        except Exception:
            raise cherrypy.HTTPError(status=400, message="Something went wrong while adding service")

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        """
        Get service, or services list

        :param uri: path
        :param params: body, must be None
        :return: Service or services info
        """
        if len(uri) != 1 or params:
            # Wrong uri number or body inside the request
            raise cherrypy.HTTPError(
                status=400,
                message=f"Path's elements number not correct or body inside the request. "
                f"One parameter is required, no body is allowed.",
            )
        if uri[0] == "all":
            # Extract all the registered services
            services = DataBase.get_all_services()
            if services:
                return services
            else:
                # No service found
                raise cherrypy.HTTPError(status=404, message=f"No service found. ")
        else:
            # Extract the service with id = uri[0]
            service = DataBase.get_service(uri[0])
            if service:
                return service
            else:
                # No service with such ID found
                raise cherrypy.HTTPError(
                    status=404, message=f"No device with serviceID = {uri[0]} found. "
                )
