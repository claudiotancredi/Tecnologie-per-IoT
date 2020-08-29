#!/usr/bin/env python3
"""
Database api

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
import sqlite3
import time
from typing import List, Dict, Optional

# --------------------------------------------------------------------------------------

############
# DATABASE #
############


class DataBase:
    """
    Class that handles the interaction with the sqlite db
    """

    __db__ = "catalog.db"
    """Database name"""

    @classmethod
    def setup_database(cls):
        """
        Create the tables : `device`, `user` and `service` in the database
        """
        # Register the adapter
        sqlite3.register_adapter(dict, json.dumps)
        # Register the converter
        sqlite3.register_converter("dict", json.loads)

        with sqlite3.connect(cls.__db__) as con:
            try:
                # Try to create the device table
                con.execute(
                    f"""CREATE TABLE device (
                    deviceID text, 
                    end_points dict, 
                    available_resources dict, 
                    insert_timestamp bigint
                    );"""
                )
                # Create index
                con.execute(
                    f"""CREATE UNIQUE INDEX device_index on device(deviceID);"""
                )
            except sqlite3.OperationalError:
                # The table already exist
                pass
            try:
                # Try to create the user table
                con.execute(
                    f"""CREATE TABLE user (
                    userID text, 
                    name text,
                    surname text,
                    email dict);"""
                )
                # Create index
                con.execute(f"""CREATE UNIQUE INDEX user_index on user(userID);""")
            except sqlite3.OperationalError:
                # The table already exist
                pass
            try:
                # Try to create the service table
                con.execute(
                    f"""CREATE TABLE service (
                    serviceID text, 
                    description text, 
                    end_points dict, 
                    insert_timestamp bigint);"""
                )
                # Create index
                con.execute(
                    f"""CREATE UNIQUE INDEX service_index on service(serviceID);"""
                )
            except sqlite3.OperationalError:
                # The table already exist
                pass

    @classmethod
    def _get_item(cls, item_type: str, item_id: str) -> tuple:
        """
        Retrieve an item from the database

        :param item_type: Typology of the item to retrieve
        :param item_id: Unique identifier of the item to retrieve
        :return: item informations
        """

        with sqlite3.connect(cls.__db__, detect_types=sqlite3.PARSE_DECLTYPES) as con:
            result = con.execute(
                f"SELECT * FROM {item_type} WHERE {item_type}ID = '{item_id}';"
            )
        return result.fetchone()

    @classmethod
    def _get_all_items(cls, item_type: str) -> List[tuple]:
        """
        Extract all items from a table of the database

        :param item_type: Type of items to retrieve, it could be "device", "user" or "service"
        :return: list of items
        """
        with sqlite3.connect(cls.__db__, detect_types=sqlite3.PARSE_DECLTYPES) as con:
            result = con.execute(f"SELECT * FROM {item_type}")
        return result.fetchall()

    @classmethod
    def delete_old_entries(cls) -> None:
        """
        Delete all the devices and services that were inserted
        more than two minutes ago
        """
        now = int(time.time())
        with sqlite3.connect(cls.__db__) as con:
            for table in ("service", "device"):
                # Delete all the devices and services
                con.execute(
                    f"DELETE FROM {table} where insert_timestamp <= {now - 120};"
                )

    @classmethod
    def insert_device(
        cls, deviceID: str, end_points: dict, available_resources: dict
    ) -> None:
        """
        Insert a device in the db,
        if the device is already present, update its insertion time

        :param deviceID: Unique identifier of the device
        :param end_points: Endpoints to communicate with the device
        :param available_resources: e.g. Temperature, Humidity and Motion sensor
        """
        with sqlite3.connect(cls.__db__) as con:
            try:
                # Try to insert the device
                con.execute(
                    f"""INSERT INTO device (
                    deviceID, 
                    end_points, 
                    available_resources, 
                    insert_timestamp
                    ) VALUES ($1, $2, $3, $4);""",
                    (deviceID, end_points, available_resources, int(time.time())),
                )
            except sqlite3.IntegrityError:
                # Update Device
                con.execute(
                    f"""update device 
                    set insert_timestamp = ? 
                    where deviceID = ?;""",
                    (int(time.time()), deviceID),
                )
        return

    @classmethod
    def get_device(cls, deviceID: str) -> Optional[dict]:
        """
        Retrieve a device from the database

        :param deviceID: Unique identifier of the device
        :return: dictionary containing device info, or none
        """
        device = cls._get_item("device", deviceID)
        if device:
            return {
                "deviceID": device[0],
                "end_points": device[1],
                "available_resources": device[2],
                "last_update": device[3],
            }
        return None

    @classmethod
    def get_all_devices(cls) -> Optional[list]:
        """
        Retrieve all the devices from the database

        :return: list containing all the devices info, or none
        """
        devices = cls._get_all_items("device")
        if len(devices) == 0:
            return None
        return [
            {
                "deviceID": device[0],
                "end_points": device[1],
                "available_resources": device[2],
                "last_update": device[3],
            }
            for device in devices
        ]

    @classmethod
    def insert_user(
        cls, userID: str, name: str, surname: str, email: Dict[str, str]
    ) -> None:
        """
        Insert a user in the db,
        if the user is already present, update its email addresses

        :param userID: Unique identifier of the user
        :param name: Name of the user
        :param surname: Surname of the user
        :param email: Email addresses of the user
        """
        # Register the adapter
        sqlite3.register_adapter(dict, json.dumps)
        # Register the converter
        sqlite3.register_converter("dict", json.loads)
        with sqlite3.connect(cls.__db__) as con:
            try:
                # Try to insert the device
                con.execute(
                    f"""INSERT INTO user (
                        userID, 
                        name, 
                        surname, 
                        email
                        ) VALUES ($1, $2, $3, $4);""",
                    (userID, name, surname, email),
                )
            except sqlite3.IntegrityError:
                # Update Device
                con.execute(
                    f"""update user 
                        set email = ? 
                        where userID = ?;""",
                    (email, userID),
                )
        return

    @classmethod
    def get_user(cls, userID: str) -> Optional[dict]:
        """
        Retrieve a user from the database

        :param userID: Unique identifier of the user
        :return: dictionary containing user info, or none
        """
        user = cls._get_item("user", userID)
        if user:
            return {
                "userID": user[0],
                "name": user[1],
                "surname": user[2],
                "email_addresses": user[3],
            }
        return None

    @classmethod
    def get_all_users(cls) -> Optional[list]:
        """
        Retrieve all the users from the database

        :return: list containing all the users info, or none
        """
        users = cls._get_all_items("user")
        if len(users) == 0:
            return None
        return [
            {
                "userID": user[0],
                "name": user[1],
                "surname": user[2],
                "email_addresses": user[3],
            }
            for user in users
        ]

    @classmethod
    def insert_service(
        cls, serviceID: str, description: str, end_points: Dict[str, List[str]],
    ) -> None:
        """
        Insert a service in the db,
        if the service is already present, update its insertion time

        :param serviceID: Unique identifier of the service
        :param description: Description of the service
        :param end_points: Endpoints to communicate with the service
        :return:
        """
        with sqlite3.connect(cls.__db__) as con:
            try:
                # Try to insert the service
                con.execute(
                    f"""INSERT INTO service (
                        serviceID, 
                        description, 
                        end_points, 
                        insert_timestamp
                        ) VALUES ($1, $2, $3, $4);""",
                    (serviceID, description, end_points, int(time.time())),
                )
            except sqlite3.IntegrityError:
                # Update service
                con.execute(
                    f"""update service 
                        set insert_timestamp = ? 
                        where serviceID = ?;""",
                    (int(time.time()), serviceID),
                )
        return

    @classmethod
    def get_service(cls, serviceID: str) -> Optional[dict]:
        """
        Retrieve a service from the database

        :param serviceID: Unique identifier of the service
        :return: dictionary containing service info, or none
        """
        service = cls._get_item("service", serviceID)
        if service:
            return {
                "serviceID": service[0],
                "description": service[1],
                "end_points": service[2],
                "last_update": service[3],
            }
        return None

    @classmethod
    def get_all_services(cls) -> Optional[list]:
        """
        Retrieve all the services from the database

        :return: list containing all the services info, or none
        """
        services = cls._get_all_items("service")
        if len(services) == 0:
            return None
        return [
            {
                "serviceID": service[0],
                "description": service[1],
                "end_points": service[2],
                "last_update": service[3],
            }
            for service in services
        ]
