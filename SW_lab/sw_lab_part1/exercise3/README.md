## LAB Software Part 1 Esercizio 3

Codice sorgente contenente un server REST basato su [Cherrypy](https://cherrypy.org/)

### Prerequisiti

Il codice internamente usa il [typing](https://docs.python.org/3/library/typing.html) per creare autodocumentazione per l
'IDE tramite i docstrings, di conseguenza è richiesto **python>3.6+**. Una
volta sicuri di avere la versione corretta di python, installare i
requirements

```bash
$ cd SW_lab/sw_lab_part1/exercise3
$ pip3 install -r requirements.txt
```

il file **requirements.txt** contiene le librerie necessarie al corretto
funzionamento del codice e le rispettive versioni.

### Uso

Per far partire l'applicazione basta entrare nella directory del progetto
e far partire  il file main.py.

```bash
$ cd SW_lab/sw_lab_part1/exercise3
$ python3 main.py
```

Tali comandi faranno partire un server REST in ascolto sull'indirizzo ip: 0.0.0.0
e sulla porta 8080.

| Method | Endpoint                   |
| -------|:--------------------------:|
| *PUT*  | *"/converter"* |


### Test

Per testare il codice, si può fare manualmente usando [Postman](https://www.postman.com/)
oppure facendo partire gli unittest all'interno del package tests.
I test possono essere lanciati con nosetest o con pytest, in maniera indifferente
( entrambe le librerie verranno installate in maniera automatica tramite il file requirements.txt)

**pytest**
```bash
$ cd SW_lab/sw_lab_part1/exercise3
$ pytest tests/
```

**nosetests**
```bash
$ cd SW_lab/sw_lab_part1/exercise3
$ nosetests tests/
```
