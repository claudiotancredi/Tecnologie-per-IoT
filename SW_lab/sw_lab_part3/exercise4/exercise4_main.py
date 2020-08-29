#!/usr/bin/env python3
"""
Exercise4 sw_lab3
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
from collections import defaultdict
from functools import partial
import json
from random import randrange
import sys
import time
from typing import Any, Dict, List, DefaultDict
from threading import Timer, Lock

# Third Party
from paho.mqtt.client import Client, MQTTMessage
import requests

# Internals
from smart_home.smart_home import SmartHome

# -----------------------------------------------------------------------------

#############
# CONSTANTS #
#############

ARDUINO_UNIQUE_ID = "YUN"

CATALOG_IP_PORT = {"ip": "0.0.0.0", "port": 8080}

SERVICE_BROKER_PORT = {"ip": "test.mosquitto.org", "port": 1883}
SERVICE_INFO = json.dumps(
    {
        "serviceID": "Exercise4/LabSw3",
        "description": "Show all the smart homes connected to the service on service topic."
                       "Manage all smart homes.",
        "end_points": {
            "MQTT": {
                "broker": SERVICE_BROKER_PORT,
                "subscribe": ["labsw3/arduino/smarthome"],
            }
        },
    }
)


# -----------------------------------------------------------------------------

###########
# SERVICE #
###########


def find_arduino(data: dict) -> bool:
    """
    Find arduino devices that offer temperature, led, FAN, PIR, noise, SM and lcd using MQTT
    :param data: device to parse
    """
    if ARDUINO_UNIQUE_ID in data["deviceID"]:
        if "MQTT" in data["available_resources"]:
            if (
                "Temp" in data["available_resources"]["MQTT"]
                and "Led" in data["available_resources"]["MQTT"]
                and "FAN" in data["available_resources"]["MQTT"]
                and "PIR" in data["available_resources"]["MQTT"]
                and "noise" in data["available_resources"]["MQTT"]
                and "SM" in data["available_resources"]["MQTT"]
                and "Lcd" in data["available_resources"]["MQTT"]
            ):
                return True
    return False


class Service:
    """Service that manages Smart Homes Devices"""

    _mqtt_client: Dict[str, Client] = {}
    _device_list: Dict[str, dict] = {}
    _broker: DefaultDict[str, set] = defaultdict(set)
    _broker_port: Dict[str, int] = {}
    _topic: DefaultDict[str, set] = defaultdict(set)
    _update_thread: Timer = None
    smart_home_list_topic = "labsw3/arduino/smarthome"

    def __init__(self):
        """
        Instantiate the service
        """
        self.service = Client(client_id=f"SmartHomeService{randrange(1, 100000)}")
        self.service.on_message = partial(self.my_on_message, publisher=self.service)
        self.lock = Lock()
        self.device_lock = Lock()

    def _update(self, device_list: List[dict]):
        """
        Update reserved dicts
        :param device_list: device list to add
        """
        for arduino in device_list:
            device = arduino["deviceID"]
            broker = arduino["end_points"]["MQTT"]["ip"]
            port = arduino["end_points"]["MQTT"]["port"]
            topics = {
                topic
                for topic in arduino["end_points"]["MQTT"]["end_points"]["subscribe"]
            }
            led_topics = {
                topic
                for topic in arduino["end_points"]["MQTT"]["end_points"]["publish"]
                if "led" in topic
            }
            fan_topics = {
                topic
                for topic in arduino["end_points"]["MQTT"]["end_points"]["publish"]
                if "FAN" in topic
            }
            lcd_topics = {
                topic
                for topic in arduino["end_points"]["MQTT"]["end_points"]["publish"]
                if "lcd" in topic
            }

            self._device_list[device] = {
                "ip": broker,
                "topics": topics,
                "smart_home": SmartHome(led_topics, fan_topics, lcd_topics)
            }

            self._broker_port[broker] = port

            self._broker[broker].update({device})
            self._topic[broker].update(topics)

            print(f"[{time.ctime()}] DEVICE {device} CONNECTED")

    def setup(self, first_time: bool = True):
        """
        Setup the service
        """
        try:
            print(f"[{time.ctime()}] EXTRACT info about all the devices registered")
            result: requests.Response = requests.get(
                url=f"http://{CATALOG_IP_PORT['ip']}:{CATALOG_IP_PORT['port']}/catalog/devices/all"
            )
            while result.status_code != 200:
                print(
                    f"[{time.ctime()}] WARNING no device registered found, retrying after 30 seconds"
                )
                time.sleep(30)
                result: requests.Response = requests.get(
                    url=f"http://{CATALOG_IP_PORT['ip']}:{CATALOG_IP_PORT['port']}"
                    f"/catalog/devices/all"
                )
            print(f"[{time.ctime()}] DEVICES found")
            data = json.loads(result.content.decode())

            print(
                f"[{time.ctime()}] EXTRACT from the devices list info about ArduinoYUN"
            )
            device_list = [device for device in data if find_arduino(device)]
            if len(device_list) == 0:
                print(f"[{time.ctime()}] No ArduinoYUN found... retrying in 10 seconds")
                time.sleep(10)
                self.setup(first_time)
                return
        except KeyboardInterrupt:
            print(f"[{time.ctime()}] EXIT")
            if first_time:
                sys.exit()
            return

        if first_time:
            # Connect the service
            self.service.connect(
                host=SERVICE_BROKER_PORT["ip"], port=SERVICE_BROKER_PORT["port"]
            )
            print(
                f"[{time.ctime()}] SERVICE CONNECTED to "
                f"broker: {SERVICE_BROKER_PORT['ip']} "
                f"on port: port={SERVICE_BROKER_PORT['port']}"
            )

        # Update registered devices and subscribe to all the topics
        with self.device_lock:
            self._update(device_list)
            self.subscribe(device_list)

        # Register inside the catalog
        print(f"[{time.ctime()}] PING the Catalog on : {CATALOG_IP_PORT['ip']}")
        requests.post(
            f'http://{CATALOG_IP_PORT["ip"]}:{CATALOG_IP_PORT["port"]}/catalog/services',
            data=SERVICE_INFO,
            headers={"Content-Type": "application/json"}
        )

    def start(self):
        """
        Start the service.
        """
        # Setup the service
        self.setup()

        # Start all the external mqtt_clients
        for broker in self._mqtt_client:
            self._mqtt_client[broker].loop_start()

        # Publish the device list for the first time
        self.service.publish(
            self.smart_home_list_topic,
            payload=json.dumps([arduino for arduino in self._device_list]),
        )

        # Schedule the update of the registration
        self._update_thread = Timer(60, self.update_registration)
        self._update_thread.start()

        try:
            # Run the service forever
            self.service.loop_forever()
        except KeyboardInterrupt:
            self.stop()

    def my_on_message(
        self, client: Client, userdata: Any, msg: MQTTMessage, publisher: Client = None
    ):
        """
        Redirect message
        :param client: MQTT client
        :param userdata: They could be any type
        :param msg: MQTT message
        :param publisher: SmartHome Client
        """

        def _device() -> SmartHome:
            """
            Find the SmartHome that generated this message
            """
            with self.device_lock:
                for device in self._device_list:
                    if msg.topic in self._device_list[device]["topics"]:
                        return self._device_list[device]["smart_home"]

        data = json.loads(msg.payload.decode())
        smart_home = _device()
        smart_home.parse_message(data, publisher)

    def update_registration(self):
        """
        Update service registration to the catalog
        """
        print(f"[{time.ctime()}] EXTRACT info about all the devices registered")
        result: requests.Response = requests.get(
            url=f"http://{CATALOG_IP_PORT['ip']}:{CATALOG_IP_PORT['port']}/catalog/devices/all"
        )

        # No device found
        if result.status_code != 200:
            self.reset()
            return

        data = json.loads(result.content.decode())
        device_list = [device for device in data if find_arduino(device)]
        if len(device_list) == 0:
            self.reset()
            return

        # New Devices Found
        new_devices = {arduino["deviceID"] for arduino in device_list}
        # Old devices list
        old_devices = set(self._device_list.keys())

        # Check if there are updates to do
        if old_devices == new_devices:
            # No update, ping the catalog
            print(f"[{time.ctime()}] PING the Catalog on : {CATALOG_IP_PORT['ip']}")
            requests.post(
                f'http://{CATALOG_IP_PORT["ip"]}:{CATALOG_IP_PORT["port"]}/catalog/services',
                data=SERVICE_INFO,
                headers={"Content-Type": "application/json"}
            )
            self.service.publish(
                self.smart_home_list_topic,
                payload=json.dumps([arduino for arduino in self._device_list]),
            )
            self._update_thread = Timer(60, self.update_registration)
            self._update_thread.start()
            return

        with self.device_lock:
            # Delete inactive devices
            delete_list = {
                arduino: self._device_list[arduino]
                for arduino in self._device_list
                if arduino not in new_devices
            }
            # Unsubscribe from devices
            self.unsubscribe(delete_list)

            # Update registered devices and subscribe
            new_devices = [
                arduino
                for arduino in device_list
                if arduino["deviceID"] not in old_devices
            ]

            self._update(new_devices)
            self.subscribe(new_devices)
            self.service.publish(
                self.smart_home_list_topic,
                payload=json.dumps([arduino for arduino in self._device_list]),
            )

        self._update_thread = Timer(60, self.update_registration)
        self._update_thread.start()

    def reset(self):
        """
        Reset the service
        """
        with self.device_lock:
            self._clear()
        self.setup(first_time=False)
        # Start all the external mqtt_clients
        for broker in self._mqtt_client:
            self._mqtt_client[broker].loop_start()
        self._update_thread = Timer(60, self.update_registration)
        self._update_thread.start()

    def unsubscribe(self, device_list: dict):
        """
        Unsubscribe from devices
        :param device_list: device list
        """
        for arduino in device_list:
            print(f"[{time.ctime()}] DEVICE {arduino} DISCONNECTED")
            broker = device_list[arduino]["ip"]
            topics = device_list[arduino]["topics"]

            if broker == SERVICE_BROKER_PORT["ip"]:
                for topic in topics:
                    self.service.unsubscribe(topic)
                    print(f"[{time.ctime()}] UNSUBSCRIBED from : {topic}")

            else:
                for topic in topics:
                    self._mqtt_client[broker].unsubscribe(topic)
                    print(f"[{time.ctime()}] UNSUBSCRIBED from : {topic}")

            # Update topics
            self._topic[broker] = self._topic[broker].difference(topics)

            # Disconnect from external broker
            if len(self._topic[broker]) == 0:
                if broker != SERVICE_BROKER_PORT["ip"]:
                    self._mqtt_client[broker].disconnect()
                    self._mqtt_client[broker].loop_stop()
                    print(f"[{time.ctime()}] DISCONNECTED from broker: {broker}")
                    del self._mqtt_client[broker]

                # Clean
                del self._topic[broker]
                del self._broker_port[broker]

            # Delete device
            del self._device_list[arduino]
            self._broker[broker].discard(arduino)

    def subscribe(self, device_list: List[dict]):
        """
        Subscribe to all the devices registered
        :param device_list: list of device
        """
        for arduino in device_list:
            broker = arduino["end_points"]["MQTT"]["ip"]
            topics = {
                topic
                for topic in arduino["end_points"]["MQTT"]["end_points"]["subscribe"]
            }
            # Subscribe to topics
            if broker == SERVICE_BROKER_PORT["ip"]:
                for topic in topics:
                    self.service.subscribe(topic)
                    print(f"[{time.ctime()}] SUBSCRIBED to : {topic}")

            # Connect to external brokers
            else:
                if broker in self._mqtt_client:
                    # Connection already made
                    for topic in topics:
                        self._mqtt_client[broker].subscribe(topic)
                        print(f"[{time.ctime()}] SUBSCRIBED to : {topic}")
                else:
                    # Connect to the broker
                    self._mqtt_client[broker] = Client(
                        f"SmartHomeService{randrange(1, 1000000)}"
                    )
                    self._mqtt_client[broker].on_message = partial(
                        self.my_on_message, publisher=self._mqtt_client[broker]
                    )
                    self._mqtt_client[broker].connect(
                        host=broker, port=self._broker_port[broker]
                    )

                    for topic in topics:
                        self._mqtt_client[broker].subscribe(topic)
                        print(f"[{time.ctime()}] SUBSCRIBED to : {topic}")

    def _clear(self):
        """
        Clear all the data stored
        """
        # Unsubscribe from all topics
        self.unsubscribe(self._device_list.copy())

        # Disconnect from all the external brokers
        for broker in self._mqtt_client:
            self._mqtt_client[broker].disconnect()
            self._mqtt_client[broker].loop_stop()
            print(f"[{time.ctime()}] DISCONNECTED from broker: {broker}")

        # Clear
        self._mqtt_client.clear()
        self._device_list.clear()
        self._broker.clear()
        self._broker_port.clear()
        self._topic.clear()

    def stop(self):
        """
        Stop the service
        """
        # Stop the schedule
        self._update_thread.cancel()

        # Wait for the threads to finish
        if self._update_thread.is_alive():
            self._update_thread.join()

        # Disconnect the clients
        print(f"[{time.ctime()}] SHUTTING DOWN")
        for client in self._mqtt_client:
            self._mqtt_client[client].disconnect()
            self._mqtt_client[client].loop_stop()
        # Disconnect the service
        self.service.disconnect()
        print(f"[{time.ctime()}] EXIT")


# -----------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    service = Service()
    service.start()
