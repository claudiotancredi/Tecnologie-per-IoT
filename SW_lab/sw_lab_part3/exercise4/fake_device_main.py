"""
Fake Smart home device
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
# Standard library
import json
from random import randrange
from threading import Timer
import time
from typing import Any

# Third party
from paho.mqtt.client import Client, MQTTMessage
import requests


# ------------------------------------------------------------------------------------------


#############
# CONSTANTS #
#############

FAKE_DEVICE_ID = f"FakeArduinoYUN{randrange(1, 100000)}"


CATALOG_IP_PORT = {"ip": "0.0.0.0", "port": 8080}

FAKE_DEVICE_BROKER_PORT = {"addr": "broker.hivemq.com", "port": 1883}

UPDATE_BODY = json.dumps(
    {
        "ID": FAKE_DEVICE_ID,
        "PROT": "MQTT",
        "IP": FAKE_DEVICE_BROKER_PORT["addr"],
        "P": FAKE_DEVICE_BROKER_PORT["port"],
        "ED": {
            "S": [
                "fake_smart_home/temperature",
                "fake_smart_home/PIR",
                "fake_smart_home/noise"
            ],
            "A": ["fake_smart_home/FAN", "fake_smart_home/led", "fake_smart_home/lcd"],
        },
        "AR": ["Temp", "Led", "FAN", "PIR", "noise", "SM", "Lcd"],
    }
)

# -------------------------------------------------------------------------------------------------------

###############
# FAKE DEVICE #
###############


class Arduino:
    """Simulate a YUN fake device"""

    _update_thread: Timer = None
    _smart_home_thread: Timer = None

    def __init__(self, broker: str, port: int):
        """
        Instantiate the device
        :param broker: MQTT broker
        :param port: Port of the broker
        """
        self.broker = broker
        self.port = port
        self.client = Client(client_id=f"FakeSmartHome{randrange(1, 100000)}")
        self.client.on_message = self.my_on_message

    def my_on_message(self, client: Client, userdata: Any, msg: MQTTMessage):
        """
        Commands for the Smart Home

        :param client: MQTT client
        :param userdata: They could be any type
        :param msg: Mqtt message
        """

        data = json.loads(msg.payload.decode())
        if data["n"] == "FAN":
            print(f"FAN INTENSITY: {data['v']}")
        elif data["n"] == "led":
            print(f"LED INTENSITY: {data['v']}")

        elif data["n"] == "lcd":
            print(f"LCD MONITOR: {data['v']}")

    def start(self):
        """
        Start the fake device
        """

        self.client.connect(host=self.broker, port=self.port)
        print(
            f"[{time.ctime()}] CONNECTED to broker: {self.broker} on port: {self.port}"
        )
        for topic in {
            f"fake_smart_home/FAN/{FAKE_DEVICE_ID}",
            f"fake_smart_home/led/{FAKE_DEVICE_ID}",
            f"fake_smart_home/lcd/{FAKE_DEVICE_ID}"
        }:
            self.client.subscribe(topic)
            print(f"[{time.ctime()}] SUBSCRIBED to TOPIC: {topic}")
        self._smart_home_thread = Timer(1, self.send_values)
        self._smart_home_thread.start()

        self.update_registration()
        # Schedule the publish of the calculated temperature

        try:
            # Run MQTT Client forever
            self.client.loop_forever()

        finally:
            # Stop the fake device
            self.stop()

    def stop(self):
        """
        Stop the fake device
        """
        # Stop the schedule
        self._update_thread.cancel()
        self._smart_home_thread.cancel()

        # Wait for the threads to finish
        if self._update_thread.is_alive():
            self._update_thread.join()
        if self._smart_home_thread.is_alive():
            self._smart_home_thread.join()

        # Disconnect the client
        self.client.disconnect()
        print(
            f"[{time.ctime()}] DISCONNECTED from broker: {self.broker} on port: {self.port}"
        )
        print(f"[{time.ctime()}] EXIT")

    def update_registration(self):
        """
        Ping the catalog on topic catalog/devices
        """
        try:
            try:
                requests.post(
                    f'http://{CATALOG_IP_PORT["ip"]}:{CATALOG_IP_PORT["port"]}/catalog/devices',
                    data=UPDATE_BODY,
                    headers={"Content-Type": "application/json"},
                )
            except requests.ConnectionError:
                pass

            # Schedule the ping 60 seconds later
            self._update_thread = Timer(60, self.update_registration)
            self._update_thread.start()
        finally:
            return

    def send_values(self):
        """
        Send fake temperature values, PIR values and noise values
        """
        try:
            self.client.publish(
                f"fake_smart_home/temperature/{FAKE_DEVICE_ID}",
                payload=json.dumps(
                    {
                        "n": "temperature",
                        "v": randrange(17, 25, step=1) + 0.3,
                        "u": "Cel",
                    }
                )
            )
            print(
                f"[{time.ctime()}] TELEMETRY sent on topic: fake_smart_home/temperature/{FAKE_DEVICE_ID}"
            )
            self.client.publish(
                f"fake_smart_home/PIR/{FAKE_DEVICE_ID}",
                payload=json.dumps(
                    {
                        "n": "PIR",
                        "v": randrange(0, 2),
                        "u": None
                    }
                )
            )
            print(
                f"[{time.ctime()}] TELEMETRY sent on topic: fake_smart_home/PIR/{FAKE_DEVICE_ID}"
            )

            self.client.publish(
                f"fake_smart_home/noise/{FAKE_DEVICE_ID}",
                payload=json.dumps(
                    {
                        "n": "noise",
                        "v": randrange(0, 2),
                        "u": None
                    }
                )
            )
            print(
                f"[{time.ctime()}] TELEMETRY sent on topic: fake_smart_home/noise/{FAKE_DEVICE_ID}"
            )

            # Schedule to send temperature again after 10 seconds
            self._smart_home_thread = Timer(10, self.send_values)
            self._smart_home_thread.start()
        finally:
            return


# ----------------------------------------------------------------------------------------------------


def start_simulation():
    """
    Instantiate a fake device and start the simulation
    """
    arduino = Arduino(FAKE_DEVICE_BROKER_PORT["addr"], FAKE_DEVICE_BROKER_PORT["port"])
    try:
        arduino.start()
    finally:
        return


# ----------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    start_simulation()
