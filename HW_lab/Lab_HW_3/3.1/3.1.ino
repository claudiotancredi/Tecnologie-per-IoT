#include <Bridge.h>
#include <BridgeServer.h>
#include <BridgeClient.h>
#include <ArduinoJson.h>

const int GREEN_LED_PIN = 8;
const int TEMP_PIN = A0;
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;
const int MAX_ANALOG_TEMP = 1023;
const int capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 40;
/*Capacity is the maximum dimension of JSON to encode/decode
  JSON contains two object ("bn" and "e"), of which "e" is an array
  with 1 element and the element contains 4 fields. Plus, 40 additional
  chars to store string characters (example: temperature, led, Cel, ecc.)*/
BridgeServer server;
DynamicJsonDocument doc_snd(capacity);
/*JSON document for sent data*/

/*Setup function*/
void setup() {
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(TEMP_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  /*Internal LED*/
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Bridge.begin();
  digitalWrite(LED_BUILTIN, HIGH);
  /*Turn on internal LED when connection is enstablished*/
  server.listenOnLocalhost();
  server.begin();
}

/*Function for encoding temperature/LED info in JSON*/
String senMlEncode(String res, float v, String unit) {
  doc_snd.clear();
  doc_snd["bn"] = "Yun";
  doc_snd["e"][0]["n"] = res;
  doc_snd["e"][0]["t"] = (millis() / 1000);
  doc_snd["e"][0]["v"] = v;
  if (unit != "") {
    doc_snd["e"][0]["u"] = unit;
  }
  else {
    doc_snd["e"][0]["u"] = (char*)NULL;
  }
  String output;
  serializeJson(doc_snd, output);
  return output;
}

/*Function for getting temperature measure*/
float get_temperature() {
  int a = analogRead(TEMP_PIN);
  float R = ((MAX_ANALOG_TEMP / (float)a) - 1) * R0;
  float T = (1 / ((log(R / R0) / B) + (1 / T0))) - 273.15;
  int temp = T * 100;
  T = (float)temp / 100;
  return T;
}

/*Function used to process new GET requests*/
void process(BridgeClient client) {
  String command = client.readStringUntil('/');
  /*Parse 1st URL element*/
  command.trim();
  /*Delete \n or similar*/
  if (command == "led") {
    int val = client.parseInt();
    /*Parse 2nd URL element*/
    if (val == 0 || val == 1) {
      digitalWrite(GREEN_LED_PIN, val);
      printResponse(client, 200, senMlEncode(F("led"), val, F("")));
    }
    else {
      printResponse(client, 400, F(""));
    }
  }
  else if (command == "temperature") {
    printResponse(client, 200, senMlEncode(F("temperature"), get_temperature(), F("Cel")));
  }
  else {
    printResponse(client, 404, F(""));
  }
}

/*Function used to provide output*/
void printResponse(BridgeClient client, int code, String body) {
  client.println("Status: " + String(code));
  if (code == 200) {
    client.println(F("Content-type: application/json; charset=utf-8"));
    client.println();
    client.println(body);
  }
}

void loop() {
  BridgeClient client = server.accept();
  if (client) {
    process(client);
    client.stop();
  }
  delay(50);
}
