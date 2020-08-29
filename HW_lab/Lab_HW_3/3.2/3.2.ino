#include <Process.h>
#include <Bridge.h>
#include <ArduinoJson.h>

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
DynamicJsonDocument doc_snd(capacity);
/*JSON document for sent data*/

/*Setup function*/
void setup() {
  pinMode(TEMP_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  /*Internal LED*/
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  Bridge.begin();
  digitalWrite(LED_BUILTIN, HIGH);
}

/*Function for encoding temperature info in JSON*/
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

/*Function for using curl command and send POST request to server*/
void postRequest(String data) {
  Process p;
  p.begin("curl");
  p.addParameter("-H");
  p.addParameter("Content-Type: application/json");
  p.addParameter("-X");
  p.addParameter("POST");
  p.addParameter("-d");
  p.addParameter(data);
  p.addParameter("http://192.168.8.143:8080/temperature/log");
  /*IP address of server is needed here*/
  p.run();
  if (p.exitValue() != 0) {
    Serial.print("Error! Exit value: ");
    Serial.print(p.exitValue());
    Serial.println("  Check curl exit value references for more informations.");
  }
  else {
    Serial.println("DATA SENT.");
  }
}

void loop() {
  postRequest(senMlEncode(F("temperature"), get_temperature(), F("Cel")));
  delay(10000);
}
