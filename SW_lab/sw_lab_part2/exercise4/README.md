## LAB Software Part 2 Esercizio 4

Sketch Arduino per un device REST che agisce sia da client (inviando una POST
ogni 60 secondi per registrarsi al catalog), sia da server (ricevendo richieste
di temperatura).

-ATTENZIONE-

Controllare che l'IP usato nella funzione postRequestRegistration corrisponda all'IP
della macchina su cui è attivo il catalog.

### USO

**RICORDARSI DI AVERE ATTIVA ALMENO UN'ISTANZA DEL CATALOG**

**RICORDARSI DI EFFETTUARE LE GET ALL'URL http://arduino.local, SEGUITO
DALL'ENDPOINT**

| Method | Endpoint|
| :-------:|:-------:|
| *GET*  | *"/arduino/temperature"* |

**JSON usato per la registrazione al catalog**
```json
{
    "ID": "randomNumberYUN",
    "PROT": "REST",
    "IP": "ip",
    "P": 80,
    "ED": {
        "S": ["arduino/temperature"]
    },
    "AR": ["Temp"]
}
```
dove randomNumber è generato casualmente durante la fase di boot del device e ip
è anch'esso ottenuto una volta per tutte durante la fase di boot.

**JSON usato per l'invio di informazioni dei sensori**
```json
{
    "n": "nomeRisorsa",
    "v": "valoreLetto",
    "u": "unitàDiMisura"
}
```
