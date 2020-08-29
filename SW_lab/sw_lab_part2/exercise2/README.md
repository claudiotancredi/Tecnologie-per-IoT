## LAB Software Part 2 Esercizio 2

Codice sorgente contenente una shell interattiva che comunica
con il catalog tramite la libreria [requests](https://requests.readthedocs.io/en/master/)

### Prerequisiti

Il codice internamente usa il [typing](https://docs.python.org/3/library/typing.html) per creare autodocumentazione per l
'IDE tramite i docstrings, di conseguenza è richiesto **python>3.6+**. Una
volta sicuri di avere la versione corretta di python, installare i
requirements

```bash
$ cd SW_lab/sw_lab_part2/exercise2
$ pip3 install -r requirements.txt
```

il file **requirements.txt** contiene le librerie necessarie al corretto
funzionamento del codice e le rispettive versioni.

### Uso

Per far partire l'applicazione basta entrare nella directory del progetto
e far partire  il file client.py.

**RICORDARSI DI AVERE ATTIVA ALMENO UN'ISTANZA DEL CATALOG**

```bash
$ cd SW_lab/sw_lab_part2/exercise2
$ python3 client.py
```

Tali comandi faranno partire una shell interattiva, la quale serve da tool
per effettuare il debug del catalog come richiesto dall'esercizio.

| Commands | Description |
|----------|:-----------:|
| *help* | "list commands"|
| *?* | "list commands"|
| *broker* | "Ask to the Catalog the ip and the port of the broker"|
| *devices* | "Ask to the Catalog info about a specific device or all the devices registered"|
| *users* | "Ask to the Catalog info about a specific user or all the users signed"|
