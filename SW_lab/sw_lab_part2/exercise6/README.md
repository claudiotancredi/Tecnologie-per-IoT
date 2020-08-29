## LAB Software Part 2 Esercizio 6

Codice sorgente contenente un fake_device basato su [paho](https://github.com/eclipse/paho.mqtt.python)


### Prerequisiti

Il codice internamente usa il [typing](https://docs.python.org/3/library/typing.html) per creare autodocumentazione per l
'IDE tramite i docstrings, di conseguenza è richiesto **python>3.6+**. Una
volta sicuri di avere la versione corretta di python, installare i
requirements

```bash
$ cd SW_lab/sw_lab_part2/exercise6
$ pip3 install -r requirements.txt
```

il file **requirements.txt** contiene le librerie necessarie al corretto
funzionamento del codice e le rispettive versioni.

### Uso

Per far partire l'applicazione basta entrare nella directory del progetto
e far partire  il file main.py.

**RICORDARSI DI AVERE ATTIVA ALMENO UN'ISTANZA DEL CATALOG DELL'ESERCIZIO 5**

```bash
$ cd SW_lab/sw_lab_part2/exercise6
$ python3 fake_device.py
```

Tali comandi faranno partire un fake_device che simulerà il funzionamento di un device
che interagisce con il catalog tramite MQTT.
