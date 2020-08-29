#!/usr/bin/env python3
"""
Exercise1 sw_lab4
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
from typing import Tuple

# Third Party
from prompt_toolkit.shortcuts import input_dialog
import requests

# -----------------------------------------------------------------------------


def gui() -> Tuple[str, int, str, str, str, str, str]:
    ip = input_dialog(
        title='Catalog IP',
        text='Please type catalog IP:').run()
    port = int(
        input_dialog(
            title='Catalog PORT',
            text='Please type catalog PORT:').run()
    )

    user_id = input_dialog(
        title='UserID',
        text='Please type UserID:',
        password=True
    ).run()

    name = input_dialog(
        title='Name',
        text='Please type user Name:',
    ).run()

    surname = input_dialog(
        title='Surname',
        text='Please type user Surname:',
    ).run()

    work_email = input_dialog(
        title='Work Email',
        text='Please type Work email:',
    ).run()

    personal_email = input_dialog(
        title='Personal Email',
        text='Please type Personal email:',
    ).run()

    return ip, port, user_id, name, surname, work_email, personal_email


def main():
    ip, port, user_id, name, surname, work_email, personal_email = gui()
    if ip is "" or user_id is "" or name is "" or surname is "" or work_email is "" or personal_email is "":
        print("WARNING, all fields must be entered. User not registered")
        return
    requests.post(
        f"http://{ip}:{port}/catalog/users",
        data=json.dumps(
            {
                "userID": user_id,
                "name": name,
                "surname": surname,
                "email_addresses": {
                    "WORK": work_email,
                    "PERSONAL": personal_email
                }
            }
        ),
        headers={"Content-Type": "application/json"}
    )


if __name__ == "__main__":
    main()
