"""
Client entry point

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
import cmd
import sys

# Third party
import requests

# ------------------------------------------------------------------------------


# #######
# SHELL #
#########


class Client(cmd.Cmd):
    """Shell utility for debugging the Catalog of exercise 1"""

    intro = "Catalog's debugger shell.   Type help or ? to list commands.\n"
    prompt = "(Catalog) "

    # ----- basic debugger commands -----
    def do_broker(self, arg):
        """
        Ask to the Catalog the ip and the port of the broker.
        You have to put the address and the port of the Catalog.
        Command  example: broker 0.0.0.0:8080
        """
        command = parse(arg)
        if len(command) != 1:
            print("Wrong number of parameters...")
            print("Command  example: broker 0.0.0.0:8080")
            return

        ip = str(command[0])
        url = f"http://{ip}/catalog/broker"
        print(f"Asking Broker info at {url}")
        try:
            result = requests.get(url, timeout=2.0).content.decode()
            print("Result:")
            print(result)
        except requests.exceptions.ConnectionError as error:
            print("Error making the request. Showing the traceback....")
            print(error)
            print("\n")

    def do_devices(self, arg):
        """
        Ask to the Catalog info about a specific device or all the devices registered.
        You have to put the address and the port of the Catalog.
        Command example: devices 0.0.0.0:8080 deviceID
        print("Command example: devices 0.0.0.0:8080 all
        """
        command = parse(arg)
        if len(command) != 2:
            print("Wrong number of parameters...")
            print("Command example: devices 0.0.0.0:8080 deviceID")
            print("Command example: devices 0.0.0.0:8080 all")
            return

        ip = str(command[0])
        path = str(parse(arg)[1])

        url = f"http://{ip}/catalog/devices/{path}"
        print(f"Asking devices info at {url}")
        try:
            result = requests.get(url, timeout=2.0).content.decode()
            print("Result:")
            print(result)
        except requests.exceptions.ConnectionError as error:
            print("Error making the request. Showing the traceback....")
            print(error)

    def do_users(self, arg):
        """
        Ask to the Catalog info about a specific user or all the users registered.
        You have to put the address and the port of the Catalog.
        Command example: users 0.0.0.0:8080 userID
        Command example: users 0.0.0.0:8080 all
        """
        command = parse(arg)
        if len(command) != 2:
            print("Wrong number of parameters...")
            print("Command example: users 0.0.0.0:8080 userID")
            print("Command example: users 0.0.0.0:8080 all")
            return

        ip = str(command[0])
        path = str(parse(arg)[1])

        url = f"http://{ip}/catalog/users/{path}"
        print(f"Asking devices info at {url}")
        try:
            result = requests.get(url, timeout=2.0).content.decode()
            print("Result:")
            print(result)
        except requests.exceptions.ConnectionError as error:
            print("Error making the request. Showing the traceback....")
            print(error)

    def do_exit(self, arg):
        """
        Exit from the prompt
        """
        sys.exit()


def parse(arg):
    """Convert a series of zero or more numbers to an argument tuple"""
    return tuple(map(str, arg.split()))


if __name__ == "__main__":
    try:
        Client().cmdloop()
    except KeyboardInterrupt:
        print("exit")
