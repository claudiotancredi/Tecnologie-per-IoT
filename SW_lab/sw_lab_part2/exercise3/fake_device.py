"""
Fake Rest Device entry point

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

# Third party
import cherrypy
import requests

# ------------------------------------------------------------------------------------------


###########
# UTILITY #
###########


def jsonify_error(status: str, message: str, **traceback: dict) -> str:
    """
    Utility function that turns every exception raised using cherrypy.HTTPError
    in a JSON. The purpose of this function is to replace the default behavior of cherrypy in case of an error
    (sending an HTML page with the description of the error and the traceback of the exception)

    :param status: HTTP code of the error
    :param message: Description of the error
    :param traceback: Traceback of the error ( it will be ignored by default)
    :return: a JSON containing the error and its description
    """
    # Take the response generation of cherrypy in case of error
    response = cherrypy.response

    # Add the JSON Header
    response.headers["Content-Type"] = "application/json"

    # Return the JSON with all the information
    return json.dumps(
        {
            "status": "Failure",
            "status_details": {"message": status, "description": message},
        }
    )


# -----------------------------------------------------------------------------------


#############
# CONSTANTS #
#############


CATALOG_IP_PORT = {"ip": "0.0.0.0", "port": 8080}

FAKE_DEVICE_IP_PORT = {"ip": "0.0.0.0", "port": 8081}

UPDATE_BODY = json.dumps(
    {
        "ID": "FakeTemperatureDevice",
        "PROT": "REST",
        "IP": FAKE_DEVICE_IP_PORT["ip"],
        "P": FAKE_DEVICE_IP_PORT["port"],
        "ED": {"S": ["temperature"]},
        "AR": ["Temp"]
    }
)


FAKE_DEVICE_CONFIG = {
    "/": {
        "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
        "tools.sessions.on": True,
        # Replace the default error handler
        "error_page.default": jsonify_error
    }
}
"""Configuration of the FakeDevice API"""

NO_AUTORELOAD = {"global": {"engine.autoreload.on": False}}

# -----------------------------------------------------------------------------


###################
# BACKGROUND TASK #
###################


def update_registration():
    """
    Update registration of the fake device to the catalog
    """
    try:
        requests.post(
            f'http://{CATALOG_IP_PORT["ip"]}:{CATALOG_IP_PORT["port"]}/catalog/devices',
            data=UPDATE_BODY,
            headers={"Content-Type": "application/json"}
        )
    except requests.ConnectionError:
        pass


BAKGROUND_TASK = cherrypy.process.plugins.BackgroundTask(60, update_registration)
"""Cherrypy utility that schedules a periodic action using a thread"""

# -------------------------------------------------------------------------------------------------------

###############
# FAKE DEVICE #
###############


@cherrypy.expose
class Temperature:
    """Fake device endpoints"""

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        """
        Return a random temperature
        """
        if len(uri) != 0 or params:
            # Wrong uri number or body inside the request
            raise cherrypy.HTTPError(
                status=400,
                message=f"Path's elements number not correct or body inside the request. "
                f"No parameter is required, no body is allowed."
            )
        return {"n": "temperature", "v": randrange(20, 30, step=1) + 0.3, "u": "Cel"}


# ------------------------------------------------------------------------------------


#########
# START #
#########


def setup_device():
    url = f'http://{CATALOG_IP_PORT["ip"]}:{CATALOG_IP_PORT["port"]}/catalog/devices'
    try:
        result = requests.post(
            f'http://{CATALOG_IP_PORT["ip"]}:{CATALOG_IP_PORT["port"]}/catalog/devices',
            data=UPDATE_BODY,
            headers={"Content-Type": "application/json"}
        )

    except requests.ConnectionError:
        pass
    BAKGROUND_TASK.start()


def start_simulation():
    """
    Start the simulation of the IoT device
    """
    # Mount the Endpoints
    cherrypy.tree.mount(Temperature(), "/temperature", FAKE_DEVICE_CONFIG)

    # Update Server Config
    cherrypy.config.update(NO_AUTORELOAD)
    cherrypy.config.update({"server.socket_host": FAKE_DEVICE_IP_PORT["ip"]})
    cherrypy.config.update({"server.socket_port": FAKE_DEVICE_IP_PORT["port"]})
    cherrypy.config.update({"request.show_tracebacks": False})

    # Start the Server
    cherrypy.engine.subscribe("start", setup_device)
    cherrypy.engine.subscribe("stop", BAKGROUND_TASK.cancel)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


# -----------------------------------------------------------------------------------------


if __name__ == "__main__":
    start_simulation()
