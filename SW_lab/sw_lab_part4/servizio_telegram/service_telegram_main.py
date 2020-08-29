#!/usr/bin/env python3
"""
Exercise2 sw_lab4
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
import json
from random import randrange
import sys
import time
from threading import Timer, Lock
from typing import Any, Dict, List, DefaultDict

# Third Party
from paho.mqtt.client import Client, MQTTMessage
import requests
from telegram import Bot

# -----------------------------------------------------------------------------

#############
# CONSTANTS #
#############


TELEGRAM_TOKEN = "*******"  #Telegram token of Bot

SIGNATURE = "\n\nBest regards,\n\nSmart Home - IoT distributed platform developers"

SERVICE_UNIQUE_ID = "AlarmTemperature"

CATALOG_IP_PORT = {"ip": "0.0.0.0", "port": 8080}

SERVICE_BROKER_PORT = {"ip": "test.mosquitto.org", "port": 1883}
SERVICE_INFO = json.dumps(
    {
        "serviceID": "TelegramService/LabSw4",
        "description": "Check every service that generates an alarm in case of "
                       "temperature out of range. In case of alarm, send via Telegram Bot the device"
                       "that generated the alarm to each chat_id registered",
        "end_points": {
            "MQTT": {
                "broker": SERVICE_BROKER_PORT,
                "publish": ["labsw4/telegram/user/chat_id"]
            }
        }
    }
)


# -----------------------------------------------------------------------------

###########
# SERVICE #
###########


def find_service(data: dict) -> bool:
    """
    Find alarm service
    :param data: service to parse
    """
    if SERVICE_UNIQUE_ID in data["serviceID"]:
        if "MQTT" in data["end_points"]:
            if "subscribe" in data["end_points"]["MQTT"]:
                return True
    return False


class Service:
    """Service that sends messages via Telegram bot"""

    _mqtt_client: Dict[str, Client] = {}
    _service_list: Dict[str, dict] = {}
    _broker: DefaultDict[str, set] = defaultdict(set)
    _broker_port: Dict[str, int] = {}
    _topic: DefaultDict[str, set] = defaultdict(set)
    _update_thread: Timer = None
    chat_id_topic = "labsw4/telegram/user/chat_id"
    _user_list: Dict[str, dict] = {}
    # Telegram
    bot: Bot = Bot(token=TELEGRAM_TOKEN)
    chat_id_list = set()

    def __init__(self):
        """
        Instantiate the service
        """
        self.service = Client(client_id=f"TelegramService{randrange(1, 100000)}")
        self.service.on_message = self.my_on_message
        self.char_id_lock = Lock()
        self.service_lock = Lock()

    def _update(self, service_list: List[dict]):
        """
        Update reserved dicts
        :param service_list: service list to add
        """
        for alarm in service_list:
            service = alarm["serviceID"]
            broker = alarm["end_points"]["MQTT"]["broker"]["ip"]
            port = alarm["end_points"]["MQTT"]["broker"]["port"]
            topics = {
                topic
                for topic in alarm["end_points"]["MQTT"]["subscribe"]
                if "alarm_temperature" in topic
            }

            self._service_list[service] = {
                "ip": broker,
                "topics": topics
            }

            self._broker_port[broker] = port

            self._broker[broker].update({service})
            self._topic[broker].update(topics)

            print(f"[{time.ctime()}] SERVICE {service} ONLINE")

    def setup(self, first_time: bool = True):
        """
        Setup the service
        """
        try:
            print(f"[{time.ctime()}] EXTRACT info about all the services registered")
            result: requests.Response = requests.get(
                url=f"http://{CATALOG_IP_PORT['ip']}:{CATALOG_IP_PORT['port']}/catalog/services/all"
            )
            while result.status_code != 200:
                print(
                    f"[{time.ctime()}] WARNING no service registered found, retrying after 30 seconds"
                )
                time.sleep(30)
                result: requests.Response = requests.get(
                    url=f"http://{CATALOG_IP_PORT['ip']}:{CATALOG_IP_PORT['port']}"
                    f"/catalog/services/all"
                )
            print(f"[{time.ctime()}] SERVICES found")
            data = json.loads(result.content.decode())

            print(
                f"[{time.ctime()}] EXTRACT from the services list info about Alarm_Temperature"
            )
            service_list = [alarm for alarm in data if find_service(alarm)]
            if len(service_list) == 0:
                print(f"[{time.ctime()}] No ServiceTemperatureAlarm found... retrying in 10 seconds")
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
            self.service.subscribe(self.chat_id_topic)

        # Update registered services and subscribe to all the topics
        with self.service_lock:
            self._update(service_list)
            self.subscribe(service_list)

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

    def my_on_message(self, client: Client, userdata: Any, msg: MQTTMessage):
        """
        Receive new chat ids. Receive alarm status and check if it is true. If so, send messages
        via Telegram Bot.
        :param client: MQTT client
        :param userdata: They could be any type
        :param msg: MQTT message
        """
        data = json.loads(msg.payload.decode())
        if msg.topic == self.chat_id_topic:
            with self.char_id_lock:
                self.chat_id_list.add(data["chat_id"])
            return

        if data["alarm"]:
            message_body = f"{data['device']} is out of range of good functioning{SIGNATURE}"
            with self.char_id_lock:
                for chat_id in self.chat_id_list:
                    self.bot.sendMessage(chat_id=chat_id, text=message_body)
                    print(f"[{time.ctime()}] TELEGRAM MESSAGE SENT TO CHAT_ID: {chat_id}")
        else:
            return

    def update_registration(self):
        """
        Update service registration to the catalog
        """
        print(f"[{time.ctime()}] EXTRACT info about all the services registered")
        result: requests.Response = requests.get(
            url=f"http://{CATALOG_IP_PORT['ip']}:{CATALOG_IP_PORT['port']}/catalog/services/all"
        )

        # No device found
        if result.status_code != 200:
            self.reset()
            return

        data = json.loads(result.content.decode())
        service_list = [alarm for alarm in data if find_service(alarm)]
        if len(service_list) == 0:
            self.reset()
            return

        # New Devices Found
        new_services = {alarm["serviceID"] for alarm in service_list}
        # Old devices list
        old_services = set(self._service_list.keys())

        # Check if there are update to do
        if old_services == new_services:
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

        with self.service_lock:
            # Delete inactive devices
            delete_list = {
                alarm: self._service_list[alarm]
                for alarm in self._service_list
                if alarm not in new_services
            }
            # Unsubscribe from devices
            self.unsubscribe(delete_list)

            # Update registered devices and subscribe
            new_services = [
                alarm
                for alarm in service_list
                if alarm["serviceID"] not in old_services
            ]

            self._update(new_services)
            self.subscribe(new_services)

        self._update_thread = Timer(60, self.update_registration)
        self._update_thread.start()

    def reset(self):
        """
        Reset the service
        """
        with self.service_lock:
            self._clear()
        self.setup(first_time=False)
        # Start all the external mqtt_clients
        for broker in self._mqtt_client:
            self._mqtt_client[broker].loop_start()
        self._update_thread = Timer(60, self.update_registration)
        self._update_thread.start()

    def unsubscribe(self, service_list: dict):
        """
        Unsubscribe from services
        :param service_list: service list
        """
        for alarm in service_list:
            print(f"[{time.ctime()}] SERVICE {alarm} OFFLINE")
            broker = service_list[alarm]["ip"]
            topics = service_list[alarm]["topics"]

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
            del self._service_list[alarm]
            self._broker[broker].discard(alarm)

    def subscribe(self, service_list: List[dict]):
        """
        Subscribe to services
        :param service_list: list of services
        """
        for alarm in service_list:
            broker = alarm["end_points"]["MQTT"]["broker"]["ip"]
            topics = {
                topic
                for topic in alarm["end_points"]["MQTT"]["subscribe"]
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
                        f"EmailAlarmService{randrange(1, 1000000)}"
                    )
                    self._mqtt_client[broker].on_message = self.my_on_message

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
        self.unsubscribe(self._service_list.copy())

        # Disconnect from all the external brokers
        for broker in self._mqtt_client:
            self._mqtt_client[broker].disconnect()
            self._mqtt_client[broker].loop_stop()
            print(f"[{time.ctime()}] DISCONNECTED from broker: {broker}")

        # Clear
        self._mqtt_client.clear()
        self._service_list.clear()
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
