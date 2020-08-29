"""
Fake MQTT Device entry point
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

# Third party
from paho.mqtt.client import Client


# ------------------------------------------------------------------------------------------


#############
# CONSTANTS #
#############

FAKE_DEVICE_ID = "FakeTemperatureDevice"

CATALOG_BROKER_PORT = {"addr": "test.mosquitto.org", "port": 1883}

FAKE_DEVICE_BROKER_PORT = CATALOG_BROKER_PORT

UPDATE_BODY = json.dumps(
    {
        "ID": FAKE_DEVICE_ID,
        "PROT": "MQTT",
        "IP": FAKE_DEVICE_BROKER_PORT["addr"],
        "P": FAKE_DEVICE_BROKER_PORT["port"],
        "ED": {"S": ["temperature/fake_thermometer"]},
        "AR": ["Temp"]
    }
)

# -------------------------------------------------------------------------------------------------------

###############
# FAKE DEVICE #
###############


class Thermometer:
    """Simulate a MQTT thermometer"""

    _update_thread: Timer = None
    _temperature_thread: Timer = None

    def __init__(self, broker: str, port: int):
        """
        Instantiate the device
        :param broker: Mqtt broker
        :param port: Port of the broker
        """
        self.broker = broker
        self.port = port
        self.client = Client(client_id=f"FakeThermometer{randrange(1, 100000)}")

    def start(self):
        """
        Start the fake thermometer
        """

        self.client.connect(host=self.broker, port=self.port)
        print(
            f"[{time.ctime()}] CONNECTED to broker: {self.broker} on port: {self.port}"
        )
        self._temperature_thread = Timer(1, self.send_temperature)
        self._temperature_thread.start()

        self.update_registration()
        # Schedule the publish of the calculated temperature

        try:
            # Run Mqtt Client forever
            self.client.loop_forever()

        finally:
            # Stop the fake device
            self.stop()

    def stop(self):
        """
        Stop the fake thermometer
        """
        # Stop the schedule
        self._update_thread.cancel()
        self._temperature_thread.cancel()

        # Wait for the threads to finish
        if self._update_thread.is_alive():
            self._update_thread.join()
        if self._temperature_thread.is_alive():
            self._temperature_thread.join()

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
            # Ping
            self.client.publish("catalog/devices", payload=UPDATE_BODY)
            print(f"[{time.ctime()}] PING the Catalog on topic: catalog/devices")

            # Schedule the ping 60 seconds later
            self._update_thread = Timer(60, self.update_registration)
            self._update_thread.start()
        finally:
            return

    def send_temperature(self):
        """
        Send fake temperature values
        """
        try:
            self.client.publish(
                f"temperature/fake_thermometer/{FAKE_DEVICE_ID}",
                payload=json.dumps(
                    {
                        "n": "temperature",
                        "v": randrange(20, 30, step=1) + 0.3,
                        "u": "Cel"
                    }
                ),
            )
            print(
                f"[{time.ctime()}] TELEMETRY sent on topic: temperature/fake_thermometer/{FAKE_DEVICE_ID}"
            )

            # Schedule to send temperature again after three seconds
            self._temperature_thread = Timer(3, self.send_temperature)
            self._temperature_thread.start()
        finally:
            return


# ----------------------------------------------------------------------------------------------------


def start_simulation():
    """
    Instantiate a fake thermometer and start the simulation
    """
    thermometer = Thermometer(CATALOG_BROKER_PORT["addr"], CATALOG_BROKER_PORT["port"])
    try:
        thermometer.start()
    finally:
        return


# ----------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    start_simulation()
