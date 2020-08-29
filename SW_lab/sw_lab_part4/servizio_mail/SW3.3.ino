#include <MQTTclient.h>
#include <Bridge.h>
#include <ArduinoJson.h>

/*Utility constants*/
const int GREEN_LED_PIN = 8;
const int TEMP_PIN = A0;
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;
const int MAX_ANALOG_TEMP = 1023;
const int capacity = JSON_OBJECT_SIZE(3) + 40;

DynamicJsonDocument doc_rec(capacity);
/*JSON document for received data*/

/*Global variables*/
String id = "";
/*Unique identifier of device*/
unsigned long lastRegistration = 0;
/*Timestamp for last registration to catalog*/
unsigned long lastDataSent = 0;
/*Timestamp for last temperature value sent*/

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
  randomSeed(analogRead(5));
  id = String(random(2147483647)) + "YUN";
  /*Generating the id for the device*/
  mqtt.begin("test.mosquitto.org", 1883);
  while (!Serial);
  mqtt.publish("catalog/devices", senMlEncodeRegistration());
  lastRegistration = millis();
  /*First registration to catalog at device booting*/
  delay(10);
  mqtt.subscribe("led/" + id, setLedValue);
  /*Subscribe to led/id and call setLedValue when new data are available*/
  delay(10);
}

/*Function for encoding info used during registration to catalog into JSON*/
String senMlEncodeRegistration() {
  String output = "{\"ID\":\"" + id + (F("\",\"PROT\":\"MQTT\",\"IP\":\"test.mosquitto.org\",\"P\":1883,\"ED\":{\"S\":[\"temp\"],\"A\":[\"led\"]},\"AR\":[\"Temp\",\"Led\"]}"));
  //Serial.println(output);
  return output;
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
    if (doc_rec["n"] != "led") {
      Serial.println(F("Wrong resource, please select available resource like led"));
      flagErr = true;
    }
    if ((doc_rec["v"]) != 1 && (doc_rec["v"]) != 0) {
      Serial.println(F("Wrong value! Possible values are 0 or 1"));
      flagErr = true;
    }
    if (doc_rec["u"] != (char*)NULL) {
      Serial.println(F("You cannot specify unit of measurement, please leave null value"));
      flagErr = true;
    }
  }
  if (flagErr == false) {
    digitalWrite(GREEN_LED_PIN, (doc_rec["v"]));
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

/*Function for encoding temperature info into JSON*/
String senMlEncode(String res, float v, String unit) {
  String output = "{\"n\":" + res + ",\"v\":" + String(v) + ",\"u\":" + unit + "}";
  //Serial.println(output);
  return output;
}

/*Function to check if millis() time register is in overflow (about every 50 days) and to reset variables to keep functioning*/
void checkOverflow() {
  if (millis() <= lastRegistration || millis() <= lastDataSent) {
    /*If in overflow condition => Reset, send registration to catalog and temperature info again*/
    mqtt.publish(String("catalog/devices"), senMlEncodeRegistration());
    lastRegistration = millis();
    delay(10);
    mqtt.publish(String("temp/") + id, senMlEncode("\"temperature\"", get_temperature(), "\"Cel\""));
    lastDataSent = millis();
    delay(10);
  }
}

void loop() {
  mqtt.monitor();
  /*Monitor topic of interest*/
  checkOverflow();
  if ((millis() - lastRegistration) >= 60000) {
    mqtt.publish(String("catalog/devices"), senMlEncodeRegistration());
    lastRegistration = millis();
    delay(10);
  }
  /*Send registration to catalog about every minute*/
  if ((millis() - lastDataSent) >= 30000) {
    mqtt.publish(String("temp/") + id, senMlEncode("\"temperature\"", get_temperature(), "\"Cel\""));
    lastDataSent = millis();
    delay(10);
  }
  /*Send temperature value about every 30 seconds*/
}
