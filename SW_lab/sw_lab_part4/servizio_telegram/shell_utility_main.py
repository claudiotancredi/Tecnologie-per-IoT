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
import json

# Third Party
from paho.mqtt.client import Client
from prompt_toolkit.shortcuts import input_dialog

# -----------------------------------------------------------------------------

SERVICE_BROKER_PORT = {"ip": "test.mosquitto.org", "port": 1883}
SERVICE_TOPIC = "labsw4/telegram/user/chat_id"


def main():
    client = Client(client_id="SHELL/UTILITY")
    client.connect(host=SERVICE_BROKER_PORT["ip"], port=SERVICE_BROKER_PORT["port"])
    client.loop_start()
    chat_id = int(
        input_dialog(
            title='Chat ID',
            text='Please activate the bot on your phone:'
                 ' https://t.me/SmartHome_IoTbot and type here your'
                 ' telegram chat id .. to obtain it go to '
                 'https://telegram.me/get_id_bot:').run()
    )
    client.publish(topic=SERVICE_TOPIC, payload=json.dumps({"chat_id": chat_id}))
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
