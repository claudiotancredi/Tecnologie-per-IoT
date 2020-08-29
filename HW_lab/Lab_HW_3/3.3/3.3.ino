#include <MQTTclient.h>
#include <Bridge.h>
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

String my_base_topic = "/tiot/3";
DynamicJsonDocument doc_rec(capacity);
/*JSON document for received data*/
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
  Serial.begin(9600);
  Bridge.begin();
  digitalWrite(LED_BUILTIN, HIGH);
  /*Turn on internal LED when connection is enstablished*/
  mqtt.begin("test.mosquitto.org", 1883);
  mqtt.subscribe(my_base_topic + String("/led"), setLedValue);
  /*Subscribe to /tiot/3/led and call setLedValue when new data are available*/
}

/*Function to manage incoming data for subscribed topic. It also check for errors*/
void setLedValue(const String& topic, const String& subtopic, const String& message) {
  bool flagErr = false;
  DeserializationError err = deserializeJson(doc_rec, message);
  if (err) {
    Serial.print(F("deserializeJson() failed with code "));
    Serial.println(err.c_str());
    flagErr = true;
  }
  else {
    if (doc_rec["bn"] != "Yun") {
      Serial.println("Wrong base name, please insert Yun");
      flagErr = true;
    }
    if (doc_rec["e"][0]["n"] != "led") {
      Serial.println("Wrong resource, please select available resource like led");
      flagErr = true;
    }
    if (doc_rec["e"][0]["t"] != (char*)NULL) {
      Serial.println("You cannot specify timestamp, please leave null value");
      flagErr = true;
    }
    if ((doc_rec["e"][0]["v"]) != 1 && (doc_rec["e"][0]["v"]) != 0) {
      Serial.println("Wrong value! Possible values are 0 or 1");
      flagErr = true;
    }
    if (doc_rec["e"][0]["u"] != (char*)NULL) {
      Serial.println("You cannot specify unit of measurement, please leave null value");
      flagErr = true;
    }
  }
  if (flagErr == false) {
    digitalWrite(GREEN_LED_PIN, (doc_rec["e"][0]["v"]));
    Serial.println("Request satisfied");
  }
  doc_rec.clear();
}

/*Function for getting temperature measure.*/
float get_temperature() {
  int a = analogRead(TEMP_PIN);
  float R = ((MAX_ANALOG_TEMP / (float)a) - 1) * R0;
  float T = (1 / ((log(R / R0) / B) + (1 / T0))) - 273.15;
  int temp = T * 100;
  T = (float)temp / 100;
  return T;
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

void loop() {
  mqtt.monitor();
  /*Monitor topic of interest*/
  String message = senMlEncode("temperature", get_temperature(), "Cel");
  mqtt.publish(my_base_topic + String("/temperature"), message);
  /*Publish every second temperature info as JSON to /tiot/3/temperature*/
  delay(1000);
}
