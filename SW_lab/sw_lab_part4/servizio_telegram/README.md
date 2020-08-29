## LAB Software Part 4 Servizio Telegram

Codice sorgente contenente un servizio basato su [paho](https://github.com/eclipse/paho.mqtt.python).
Il servizio riceve informazioni dal servizio service_alarm_main.py (analogo
a quello sviluppato per il laboratorio SW 3, esercizio 3) e inoltra
l'allarme agli utenti tramite Telegram Bot.


### Prerequisiti

Il codice internamente usa il [typing](https://docs.python.org/3/library/typing.html) per creare autodocumentazione per l
'IDE tramite i docstrings, di conseguenza è richiesto **python>3.6+**. Una
volta sicuri di avere la versione corretta di python, installare i
requirements

```bash
$ cd SW_lab/sw_lab_part4/servizio_telegram
$ pip3 install -r requirements.txt
```

il file **requirements.txt** contiene le librerie necessarie al corretto
funzionamento del codice e le rispettive versioni.

### Uso

Per comodità è stato copiato nella directory il catalog sviluppato nel laboratorio Software 2 esercizio 5.
Per far partire l'applicazione basta entrare nella directory del progetto
e far partire  il catalog, l'arduino e/o il fake_device, il servizio di allarme
ed il servizio Telegram.


**CATALOG**

```bash
$ cd SW_lab/sw_lab_part4/servizio_telegram
$ python3 catalog_main.py
```

**Fake_DEVICE**

```bash
$ cd SW_lab/sw_lab_part4/servizio_telegram
$ python3 fake_device_main.py
```

**SERVIZIO ALLARME**

```bash
$ cd SW_lab/sw_lab_part4/servizio_telegram
$ python3 service_alarm_main.py
```

**SERVIZIO TELEGRAM**

```bash
$ cd SW_lab/sw_lab_part4/servizio_telegram
$ python3 service_telegram_main.py
```

**SHELL UTILITY**

```bash
$ cd SW_lab/sw_lab_part4/servizio_telegram
$ python3 shell_utility_main.py
```


Tali comandi, eseguiti su più terminali, faranno partire una istanza del
catalog, un fake device, un servizio che fornisce un allarme in caso di temperatura
fuori dal range di ottimo funzionamento, un servizio per mandare messaggi agli utenti tramite
Telegram Bot in caso di malfunzionamento ed una interfaccia grafica da terminale per
registrare i chat ids degli utenti.
