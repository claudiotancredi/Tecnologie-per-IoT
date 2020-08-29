#!/usr/bin/env python3
"""
Exercise3 sw_lab3
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

# -----------------------------------------------------------------------------

#############
# CONSTANTS #
#############

ARDUINO_UNIQUE_ID = "YUN"

CATALOG_IP_PORT = {"ip": "0.0.0.0", "port": 8080}

SERVICE_BROKER_PORT = {"ip": "test.mosquitto.org", "port": 1883}
SERVICE_INFO = json.dumps(
    {
        "serviceID": "Exercise3/LabSw3",
        "description": "Turn on LED for devices whose temperature is not in expected range of good functioning. "
                       "Publish alarm status for each device",
        "end_points": {
            "MQTT": {
                "broker": SERVICE_BROKER_PORT,
                "subscribe": ["labsw3/arduino/alarm"]
            }
        }
    }
)
RANGE = {
    "min": 0,
    "max": 30
}

# -----------------------------------------------------------------------------

###########
# SERVICE #
###########


def find_arduino(data: dict) -> bool:
    """
    Find arduino devices that offer temperature and led using MQTT
    :param data: device to parse
    """
    if ARDUINO_UNIQUE_ID in data["deviceID"]:
        if "MQTT" in data["available_resources"]:
            if "Temp" in data["available_resources"]["MQTT"] and "Led" in data["available_resources"]["MQTT"]:
                return True
    return False


class Service:
    """
    Service that publish informations about whether or not the devices are in expected range
    of good functioning
    """

    _mqtt_client: Dict[str, Client] = {}
    _device_list: Dict[str, dict] = {}
    _broker: DefaultDict[str, set] = defaultdict(set)
    _broker_port: Dict[str, int] = {}
    _topic: DefaultDict[str, set] = defaultdict(set)
    _update_thread: Timer = None
    alarm_topic = "labsw3/arduino/alarm"

    def __init__(self):
        """
        Instantiate the service
        """
        self.service = Client(client_id=f"AlarmService{randrange(1, 100000)}")
        self.service.on_message = partial(self.my_on_message, led=self.service, service=self.service)
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
                if "temp" in topic
            }
            led_topics = {
                topic
                for topic in arduino["end_points"]["MQTT"]["end_points"]["publish"]
                if "led" in topic
            }

            self._device_list[device] = {
                "ip": broker,
                "temperature_topics": topics,
                "led_topics": led_topics
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

        # Schedule the update of the registration
        self._update_thread = Timer(60, self.update_registration)
        self._update_thread.start()

        try:
            # Run the service forever
            self.service.loop_forever()
        except KeyboardInterrupt:
            self.stop()

    def my_on_message(self, client: Client, userdata: Any, msg: MQTTMessage, led: Client = None, service: Client = None):
        """
        Check if the temperature is good. In case of bad values,
        turn on a led and send the alarm
        :param client: MQTT client
        :param userdata: They could be any type
        :param msg: MQTT message
        :param led: Led Client
        :param service: Service Client
        """
        def _device_led():
            """
            Find the arduino that generates the temperature telemetry
            and the topic to control the led
            """
            with self.device_lock:
                for device in self._device_list:
                    if msg.topic in self._device_list[device]["temperature_topics"]:
                        return device, self._device_list[device]["led_topics"]

        data = json.loads(msg.payload.decode())
        arduino, led_topics = _device_led()

        with self.lock:
            if RANGE["min"] < data["v"] < RANGE["max"]:
                for topic in led_topics:
                    led.publish(
                        topic,
                        payload=json.dumps(
                            {
                                "n": "led",
                                "v": 0,
                                "u": None
                            }
                        )
                    )
                print(
                    f"[{time.ctime()}] PUBLISHING Alarm status on topic: {self.alarm_topic}"
                )
                service.publish(
                    self.alarm_topic,
                    payload=json.dumps(
                        {
                            "device": arduino,
                            "alarm": False
                        }
                    )
                )
            else:
                for topic in led_topics:
                    led.publish(
                        topic,
                        payload=json.dumps(
                            {
                                "n": "led",
                                "v": 1,
                                "u": None
                            }
                        )
                    )
                print(
                    f"[{time.ctime()}] PUBLISHING Alarm status on topic: {self.alarm_topic}"
                )
                service.publish(
                    self.alarm_topic,
                    payload=json.dumps(
                        {
                            "device": arduino,
                            "alarm": True
                        }
                    )
                )

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
            topics = device_list[arduino]["temperature_topics"]

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
                if "temp" in topic
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
                        f"TemperatureMeanService{randrange(1, 1000000)}"
                    )
                    self._mqtt_client[broker].on_message = partial(
                        self.my_on_message, led=self._mqtt_client[broker], service=self.service
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
