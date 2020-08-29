#!/usr/bin/env python3
"""
SmartHome sw_lab3
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
from collections import deque
import json
import time
from typing import Set

# Third Party
from paho.mqtt.client import Client

# ---------------------------------------------------------------

MAX_PWM_FAN_AND_LED = 255
MIN = 0
TIMEOUT_PIR = 30 * 60
TIMEOUT_SOUND = 60 * 60
SOUND_INTERVAL = 10 * 60


class SmartHome:
    set_point_min_max_1 = [22.0, 25.0, 16.0, 20.0]
    """Default set-point to use when people detected"""

    set_point_min_max_0 = [24.0, 28.0, 14.0, 18.0]
    """Default set-point to use when people not detected"""

    set_point = []
    """Set - point in use"""

    def __init__(
        self, led_topics: Set[str], fan_topics: Set[str], lcd_topics: Set[str]
    ):
        """
        Instantiate a Smart Home

        :param led_topics: Topics to control the led
        :param fan_topics: Topic to control the fan
        :param lcd_topics: Topics to control the lcd
        """
        self.time_temperature = time.time()
        self.time_pir = time.time()
        self.time_noise = time.time()
        self.noise_timestamps = deque(maxlen=49)
        self.noise_flag = False
        self.pir_flag = False
        self.temperature = 0
        self.led_topics = led_topics
        self.fan_topics = fan_topics
        self.lcd_topics = lcd_topics
        self.first_time = False

    def parse_message(self, message: dict, publisher: Client):
        """
        Parse the message received to control the smart home
        
        :param message: Data to parse 
        :param publisher: MQTT client used to communicate
        :return: 
        """ ""
        if not self.first_time:
            self.first_time = True
            for topic in self.lcd_topics:
                publisher.publish(
                    topic,
                    payload=json.dumps(
                        {"n": "lcd", "v": "Smart Home Welcome", "u": None}
                    )
                )

        now = time.time()
        if (now - self.time_pir) >= TIMEOUT_PIR and self.pir_flag:
            self.pir_flag = False

        if (now - self.time_noise) >= TIMEOUT_SOUND and self.noise_flag:
            self.noise_flag = False

        if message["n"] == "temperature":
            if now - self.time_temperature < 30:
                return

            self.time_temperature = now
            if self.noise_flag or self.pir_flag:
                self.set_point = self.set_point_min_max_1
            else:
                self.set_point = self.set_point_min_max_0

            self.temperature = message["v"]
            for topic in self.lcd_topics:
                publisher.publish(
                    topic,
                    payload=json.dumps(
                        {
                            "n": "lcd",
                            "v": f"Smart Home {message['v']} {message['u']}",
                            "u": None
                        }
                    )
                )
            self.manage_red_led(publisher)
            self.manage_fan(publisher)
            return

        elif message["n"] == "PIR" and message["v"] == 1:
            self.time_pir = now
            self.pir_flag = True

        elif message["n"] == "noise" and message["v"] == 1:
            if len(self.noise_timestamps) == 49:
                if (time.time() - self.noise_timestamps[0]) < SOUND_INTERVAL:
                    self.noise_flag = True
            self.noise_timestamps.append(time.time())
            return

        elif message["n"] == "sp1":
            self.set_point_min_max_1 = message["v"]
        elif message["n"] == "sp0":
            self.set_point_min_max_0 = message["v"]

    def manage_red_led(self, publisher: Client):
        """
        Control the led (heater)

        :param publisher: MQTT client
        :return:
        """
        if self.set_point[2] < self.temperature < self.set_point[3]:
            for topic in self.led_topics:
                publisher.publish(
                    topic,
                    payload=json.dumps(
                        {
                            "n": "led",
                            "v": int(
                                MAX_PWM_FAN_AND_LED
                                - (
                                    (self.temperature - self.set_point[2])
                                    / (self.set_point[3] - self.set_point[2])
                                    * MAX_PWM_FAN_AND_LED
                                )
                            ),
                            "u": None
                        }
                    )
                )

        elif self.temperature <= self.set_point[2]:
            for topic in self.led_topics:
                publisher.publish(
                    topic,
                    payload=json.dumps(
                        {"n": "led", "v": MAX_PWM_FAN_AND_LED, "u": None}
                    )
                )

        else:
            for topic in self.led_topics:
                publisher.publish(
                    topic, payload=json.dumps({"n": "led", "v": MIN, "u": None})
                )

    def manage_fan(self, publisher: Client):
        """
        Control the fan (Air Conditioning)

        :param publisher: MQTT client
        :return:
        """
        if self.set_point[0] < self.temperature < self.set_point[1]:
            for topic in self.fan_topics:
                publisher.publish(
                    topic,
                    payload=json.dumps(
                        {
                            "n": "FAN",
                            "v": int(
                                (self.temperature - self.set_point[0])
                                / (self.set_point[1] - self.set_point[0])
                                * MAX_PWM_FAN_AND_LED
                            ),
                            "u": None
                        }
                    )
                )
        elif self.temperature <= self.set_point[0]:
            for topic in self.fan_topics:
                publisher.publish(
                    topic, payload=json.dumps({"n": "FAN", "v": MIN, "u": None})
                )

        else:
            for topic in self.fan_topics:
                publisher.publish(
                    topic,
                    payload=json.dumps(
                        {"n": "FAN", "v": MAX_PWM_FAN_AND_LED, "u": None}
                    )
                )
