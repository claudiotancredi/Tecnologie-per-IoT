#!/usr/bin/env python3
"""
MQTT plugin

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
from random import randrange
from typing import Any, Union, List

# Third Party
import cherrypy
from cherrypy.process import plugins, wspbus
from paho.mqtt.client import Client, MQTTMessage

# Internals
from ..database import DataBase

# -------------------------------------------------------------------------------------------


#######
# BUS #
#######


class Bus:
    """
    Class that handles the communication between the Paho callback of a
    received message, with the cherrypy bus
    """

    def __init__(self, bus: wspbus) -> None:
        """
        Instantiate

        :param bus: Cherrypy internal Bus
        """
        self.bus = bus

    def my_on_message(self, client: Client, userdata: Any, msg: MQTTMessage) -> None:
        """
        Send the data received from MQTT on the CherryPy Bus

        :param client: MQTT client
        :param userdata: They could be any type
        :param msg: Mqtt message
        """
        self.bus.log(f"MQTT Message on topic: {msg.topic}")
        data = json.loads(msg.payload)
        cherrypy.engine.publish(msg.topic, data)


# -------------------------------------------------------------------------------------------


##########
# PLUGIN #
##########


class MqttPlugin(plugins.SimplePlugin):
    """
    Plugin that listens to MQTT topics and publishes the payload
    'unmodified' to a channel on the CherryPy bus. The cherrypy channel name
    is the same as the MQTT topic

    Requires PAHO
    """

    def __init__(
        self, bus: wspbus, broker: str, port: int, topic_list: Union[str, List[str]]
    ) -> None:
        """
        Setup the plugin

        :param bus: Cherrypy internal Bus
        :param broker: Mqtt broker
        :param port: Port of the Mqtt broker
        :param topic_list: topic to subscribe
        """

        # Cherrypy plugins.SimplePlugin doesn't accept the super().__init__()
        # Inside cherrypy's docs it's like this
        # https://docs.cherrypy.org/en/latest/extend.html#create-a-plugin
        plugins.SimplePlugin.__init__(self, bus)

        self.broker = broker
        self.port = port
        self.topic_list = topic_list
        self.client = Client(client_id=f"Catalog{randrange(1, 100000)}")
        self.client.on_message = Bus(bus).my_on_message

    def start(self):
        self.bus.log("Setup mqttcherrypy")
        self.client.connect(self.broker, self.port)
        self.bus.log(f"Connected to broker: {self.broker} port: {self.port})")
        self.client.loop_start()
        self.client.subscribe(self.topic_list)
        self.bus.log(f"Subscribed to {self.topic_list}")

    def stop(self):
        self.bus.log("Shut down mqttcherrypy")
        self.client.unsubscribe(self.topic_list)
        self.bus.log(f"Unsubscribed from {self.topic_list}")
        self.client.loop_stop(force=True)
        self.client.disconnect()
        self.bus.log(f"Disconnected from: {self.broker} port: {self.port}")


# -------------------------------------------------------------------------------------------


##################
# DEVICE UTILITY #
##################


def save_device(data: dict) -> None:
    """
    Function used to parse the device data received from CherryPy Bus
    and save them inside the database.
    Those data are the one obtained thanks to the MQTT plugin

    :param data: Received from the Bus
    """
    __mqtt_and_rest__ = {"ID", "PROT", "MQTT", "REST"}
    __generic_protocol_keys__ = {"IP", "P", "ED", "AR"}

    __generic_device_keys__ = {"ID", "PROT", "IP", "P", "ED", "AR"}

    __protocols_actions__ = {
        "REST": {"S": "GET", "A": "POST"},
        "MQTT": {"S": "subscribe", "A": "publish"}
    }

    def _parse(protocols, paths, id, ip, port):
        """
        Inner function used to parse the endpoint and extract info
        """
        if protocols == "REST":
            return [f"http://{ip}:{port}/{path}" for path in paths]

        elif protocols == "MQTT":
            return [f"{path}/{id}" for path in paths]

    # Check if the device supports both MQTT and REST protocols
    if set(data.keys()) == __mqtt_and_rest__:
        if data["PROT"] != "BOTH":
            return
        if (
            set(data["MQTT"].keys()) != __generic_protocol_keys__
            or set(data["REST"].keys()) != __generic_protocol_keys__
        ):
            return

        # Check if the data of the protocols are well formatted
        for protocol in {"MQTT", "REST"}:
            if type(data[protocol]["AR"]) != list:
                return

            for resource in data[protocol]["AR"]:
                if type(resource) != str:
                    return

            for end_point in data[protocol]["ED"]:
                if type(data[protocol]["ED"][end_point]) != list:
                    return

                for element in data[protocol]["ED"][end_point]:
                    if type(element) != str:
                        return
            # Data correct, extract and put device into database
            try:
                DataBase.insert_device(
                    str(data["ID"]),
                    end_points={
                        protocol: {
                            "ip": str(data[protocol]["IP"]),
                            "port": int(data[protocol]["P"]),
                            "end_points": {
                                __protocols_actions__[protocol][end_point]: _parse(
                                    protocol,
                                    data[protocol]["ED"][end_point],
                                    str(data["ID"]),
                                    str(data[protocol]["IP"]),
                                    int(data[protocol]["P"])
                                )
                                for end_point in data[protocol]["ED"]
                            },
                        }
                        for protocol in {"MQTT", "REST"}
                    },
                    available_resources={
                        protocol: data[protocol]["AR"] for protocol in {"MQTT", "REST"}
                    },
                )
            finally:
                return

    # Check if the device supports MQTT or REST protocol
    elif set(data.keys()) == __generic_device_keys__:
        if data["PROT"] not in {"MQTT", "REST"}:
            return

        # Check if available resources are well formatted
        if type(data["AR"]) != list:
            return
        for resource in data["AR"]:
            if type(resource) != str:
                return

        # Check if end_points are well formatted
        for end_point in data["ED"]:
            if type(data["ED"][end_point]) != list:
                raise cherrypy.HTTPError(
                    status=400, message="JSON values are not correct."
                )
            for value in data["ED"][end_point]:
                if type(value) != str:
                    raise cherrypy.HTTPError(
                        status=400, message="JSON values are not correct."
                    )
        # Try to insert the device
        try:
            DataBase.insert_device(
                deviceID=str(data["ID"]),
                end_points={
                    data["PROT"]: {
                        "ip": str(data["IP"]),
                        "port": int(data["P"]),
                        "end_points": {
                            __protocols_actions__[data["PROT"]][end_point]: _parse(
                                data["PROT"],
                                data["ED"][end_point],
                                str(data["ID"]),
                                str(data["IP"]),
                                int(data["P"])
                            )
                            for end_point in data["ED"]
                        },
                    }
                },
                available_resources={data["PROT"]: data["AR"]},
            )
        finally:
            return
