#include <MQTTclient.h>
#include <Bridge.h>

/*Utility constants*/
const int TEMP_PIN = A0;
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;
const int MAX_ANALOG_TEMP = 1023;

/*Global variables*/
String id = "";
/*Unique identifier of device*/
unsigned long lastRegistration = 0;
/*Timestamp for last registration to catalog*/
unsigned long lastDataSent = 0;
/*Timestamp for last temperature value sent*/

/*Setup function*/
void setup() {
  pinMode(TEMP_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  /*Internal LED*/
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
}

/*Function for encoding info used during registration to catalog into JSON*/
String senMlEncodeRegistration() {
  String output = "{\"ID\":\"" + id + (F("\",\"PROT\": \"MQTT\",\"IP\":\"test.mosquitto.org\",\"P\":1883,\"ED\":{\"S\":[\"temp\"]},\"AR\":[\"Temp\"]}"));
  //Serial.println(output);
  return output;
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
