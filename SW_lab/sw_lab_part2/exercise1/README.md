## LAB Software Part 2 Esercizio 1

Codice sorgente contenente un server REST basato su [Cherrypy](https://cherrypy.org/)

### Prerequisiti

Il codice internamente usa il [typing](https://docs.python.org/3/library/typing.html) per creare autodocumentazione per l
'IDE tramite i docstrings, di conseguenza è richiesto **python>3.6+**. Una
volta sicuri di avere la versione corretta di python, installare i
requirements

```bash
$ cd SW_lab/sw_lab_part2/exercise1
$ pip3 install -r requirements.txt
```

il file **requirements.txt** contiene le librerie necessarie al corretto
funzionamento del codice e le rispettive versioni.

### Uso

Per far partire l'applicazione basta entrare nella directory del progetto
e far partire  il file main.py.

```bash
$ cd SW_lab/sw_lab_part2/exercise1
$ python3 main.py
```

Tali comandi faranno partire un server REST in ascolto sull'indirizzo ip: 0.0.0.0
e sulla porta 8080.

| Broker                  |
|:-----------------------:|
| *GET "/catalog/broker"* |

| Device                               |
|:------------------------------------:|
| *GET  "/catalog/devices/{deviceID}"* |
| *GET  "/catalog/devices/all"*        |
| *POST "/catalog/devices"*            |

**Example of a MQTT Device payload**
```json
{
    "ID": "8151395YUN",
    "PROT": "MQTT",
    "IP": "test.mosquitto.org",
    "P": 1883,
    "ED": {
        "S": ["temp", "PIR", "noise", "SP"],
        "A": ["FAN", "led", "lcd"]
    },
    "AR": ["Temp", "FAN", "Led", "PIR", "noise", "SM", "Lcd"]
}
```
**Example of a REST Device payload**
```json
{
    "ID": "819245YUN",
    "PROT": "REST",
    "IP": "192.168.1.12",
    "P": 8000,
    "ED": {
        "S": ["temp", "PIR", "noise", "SP"],
        "A": ["FAN", "led", "lcd"]
    },
    "AR": ["Temp", "FAN", "Led", "PIR", "noise", "SM", "Lcd"]
}
```
**Example of a Device that supports both MQTT and REST payload**
```json
{
    "ID": "8193255YUN",
    "PROT": "BOTH",
    "MQTT": {
        "IP": "test.mosquitto.org",
        "P": 1883,
        "ED": {
            "S": ["temp", "PIR", "noise", "SP"],
            "A": ["FAN", "led", "lcd"]
        },
        "AR": ["Temp", "FAN", "led", "PIR", "noise", "SM"]
    },
    "REST": {
        "IP": "192.168.1.12",
        "P": 8000,
        "ED":{
            "S": ["temp", "PIR", "noise", "SP"],
            "A": ["FAN", "led", "lcd"]
        },
        "AR": ["Temp", "FAN", "led", "PIR", "noise", "SM"] 
    }
}
```

| User                             |
|:--------------------------------:|
| *GET  "/catalog/users/{userID}"* |
| *GET  "/catalog/users/all"*      |
| *POST "/catalog/users"*          |

**Example of an User POST payload with both mails**
```json
{
    "userID": "GruppoIoT3",
    "name": "Claudio",
    "surname": "Angelo",
    "email_addresses": {
        "PERSONAL": "personal_user_mail@gmail.com",
        "WORK": "work_user_mail@gmail.com"
    }
}
```
**Example of an User POST payload with personal mail**
```json
{
    "userID": "GruppoIoT3",
    "name": "Claudio",
    "surname": "Angelo",
    "email_addresses": {
        "PERSONAL": "personal_user_mail@gmail.com"
    }
}
```
**Example of an User POST payload with work mail**
```json
{
    "userID": "GruppoIoT3",
    "name": "Claudio",
    "surname": "Angelo",
    "email_addresses": {
        "WORK": "personal_user_mail@gmail.com"
    }
}
```

| Service                                |
|:--------------------------------------:|
| *GET  "/catalog/services/{serviceID}"* |
| *GET  "/catalog/services/all"*         |
| *POST "/catalog/services"*             |

**Example of a Service based on MQTT payload**
```json
{
    "serviceID": "ExampleServiceID1",
    "description": "Example description",
        "end_points": {
            "MQTT": {
                "broker": {
                    "ip": "test.mosquitto.org",
                    "port": 1883
                },
                "subscribe": ["iot/service/example"]
            }
        }
    }
```
**Example of a Service based on REST payload**
```json
{
    "serviceID": "ExampleServiceID2",
    "description": "Example description",
    "end_points": {
        "REST": {
            "GET": ["http://192.168.1.12:8000/example"]
       }
    }
}
```
**Example of a Service based on MQTT and REST payload**
```json
{
    "serviceID": "ExampleServiceID3",
    "description": "Example description",
    "end_points": {
        "MQTT": {
            "broker": {
                "ip": "test.mosquitto.org",
                "port": 1883
            },
            "subscribe": ["iot/service/example"]
        },
        "REST": {
            "GET": ["http://192.168.1.12:8000/example"]
        }
    }
}
```
