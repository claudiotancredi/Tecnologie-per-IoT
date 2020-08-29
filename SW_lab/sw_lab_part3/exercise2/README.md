## LAB Software Part 3 Esercizio 2

Codice sorgente contenente un servizio basato su [paho](https://github.com/eclipse/paho.mqtt.python).
Il servizio riceve valori di temperatura e ne calcola la media, inviandola in un JSON sul topic che espone.


### Prerequisiti

Il codice internamente usa il [typing](https://docs.python.org/3/library/typing.html) per creare autodocumentazione per l
'IDE tramite i docstrings, di conseguenza è richiesto **python>3.6+**. Una
volta sicuri di avere la versione corretta di python, installare i
requirements

```bash
$ cd SW_lab/sw_lab_part3/exercise2
$ pip3 install -r requirements.txt
```

il file **requirements.txt** contiene le librerie necessarie al corretto
funzionamento del codice e le rispettive versioni.

### Uso

Per comodità è stato copiato nella directory il catalog sviluppato nel laboratorio Software 2 esercizio 5.
Per far partire l'applicazione basta entrare nella directory del progetto
e far partire  il catalog, l'arduino e/o il fake_device ed il servizio.


**CATALOG**

```bash
$ cd SW_lab/sw_lab_part3/exercise2
$ python3 catalog_main.py
```

**Fake_DEVICE**

```bash
$ cd SW_lab/sw_lab_part3/exercise2
$ python3 fake_device_main.py
```

**SERVIZIO**

```bash
$ cd SW_lab/sw_lab_part3/exercise2
$ python3 exercise2_main.py
```

Tali comandi, eseguiti su più terminali, faranno partire una istanza del
catalog, il servizio richiesto in questo esercizio ed un fake device connesso
ad un broker diverso da quello utilizzato nello sketch Arduino. Il fake device
risulta utile per testare il corretto funzionamento della piattaforma, la quale
è in grado di gestire più device contemporaneamente, anche connessi a broker
diversi, garantendo complessivamente una buona flessibilità del sistema.

**SKETCH ARDUINO**

Sketch Arduino per un device MQTT che periodicamente (ogni minuto) effettua
una publish sul topic catalog/devices per registrarsi al catalog e che periodicamente
(ogni 30 secondi) effettua una publish sul topic temp/{id} per fornire la
temperatura letta. 

JSON usato per la registrazione al catalog
```json
{
    "ID": "randomNumberYUN",
    "PROT": "MQTT",
    "IP": "test.mosquitto.org",
    "P": 1883,
    "ED": {
        "S": ["temp"]
    },
    "AR": ["Temp"]
}
```
dove randomNumber è generato casualmente durante la fase di boot del device.

JSON usato per l'invio di informazioni dei sensori
```json
{
    "n": "nomeRisorsa",
    "v": "valoreLetto",
    "u": "unitàDiMisura"
}
```
Da questo momento in poi si adotterà sempre questo formato per le letture
dei sensori e per i comandi di attuazione ricevuti dai servizi.