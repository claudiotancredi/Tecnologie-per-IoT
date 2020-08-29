#include <LiquidCrystal_PCF8574.h>
#include <MQTTclient.h>
#include <Bridge.h>
#include <ArduinoJson.h>

LiquidCrystal_PCF8574 lcd(0x27);

/*Utility constants*/
const int FAN_PIN = 6;
const int TEMP_PIN = A0;
const int RED_LED_PIN = 11;
const int PIR_PIN = 4;
const int SOUND_PIN = 7;
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;
const int MAX_ANALOG_TEMP = 1023;
const int capacity = JSON_OBJECT_SIZE(3) + 45;

DynamicJsonDocument doc_rec(capacity);
/*JSON document for received data*/

/*Global variables*/
String id = "";
/*Unique identifier of device*/
unsigned long lastRegistration = 0;
/*Timestamp for last registration to catalog*/

/*Setup function*/
void setup() {
  pinMode(FAN_PIN, OUTPUT);
  pinMode(TEMP_PIN, INPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(SOUND_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  /*Internal LED*/
  digitalWrite(RED_LED_PIN, 0);
  digitalWrite(FAN_PIN, 0);
  digitalWrite(LED_BUILTIN, LOW);
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.clear();
  Serial.begin(9600);
  Bridge.begin();
  digitalWrite(LED_BUILTIN, HIGH);
  /*Turn on internal LED when connection is enstablished*/
  randomSeed(analogRead(5));
  id = String(random(2147483647)) + F("YUN");
  /*Generating the id for the device*/
  mqtt.begin(F("test.mosquitto.org"), 1883);
  while (!Serial);
  Serial.println(F("To update the 4 SP please send 0 or 1 so that I understand which case I have to modify"));
  mqtt.publish(F("catalog/devices"), senMlEncodeRegistration());
  lastRegistration = millis();
  /*First registration to catalog at device booting*/
  delay(10);
  mqtt.subscribe("led/" + id, setled);
  mqtt.subscribe("lcd/" + id, setlcd);
  mqtt.subscribe("FAN/" + id, setFAN);
  /*Subscribe to led/id, lcd/id, FAN/id and link callback functions to manage new available data*/
}

/*Function for encoding info used during registration to catalog into JSON*/
String senMlEncodeRegistration() {
  String output = "{\"ID\":\"" + id + (F("\",\"PROT\":\"MQTT\",\"IP\":\"test.mosquitto.org")) + (F("\",\"P\":1883,\"ED\":{\"S\":[\"temp\",\"PIR\"")) + (F(",\"noise\",\"SP\"],\"A\":[\"FAN\",\"led\",\"lcd\"]}")) + (F(",\"AR\":[\"Temp\",\"FAN\",\"Led\",\"PIR\",\"noise\",\"SM\", \"Lcd\"]}"));
  //Serial.println(output);
  return output;
}

/*Function for encoding sensors info into JSON*/
String senMlEncode(String res, float v, String unit) {
  String output = "{\"n\":" + res + ",\"v\":" + String(v) + ",\"u\":" + unit + "}";
  //Serial.println(output);
  return output;
}

/*Function for encoding set-points info into JSON for set-points update*/
String senMlEncodeSP(String res, float *sp, String unit) {
  String output = "{\"n\":" + res + ",\"v\":[" + String(sp[0]) + "," + String(sp[1]) + "," + String(sp[2]) + "," + String(sp[3]) + "],\"u\":" + unit + "}";
  //Serial.println(output);
  return output;
}

/*Function to manage incoming data for subscribed topic led/id. Warning: apart from deserialization errors, it doesn't check for other types of errors*/
void setled(const String& topic, const String& subtopic, const String& message) {
  DeserializationError err = deserializeJson(doc_rec, message);
  if (err) {
    Serial.println(F("deserializeJson() failed"));
    doc_rec.clear();
    return;
  }
  analogWrite(RED_LED_PIN, doc_rec["v"]);
  Serial.println(F("Request satisfied"));
  doc_rec.clear();
}

/*Function to manage incoming data for subscribed topic FAN/id. Warning: apart from deserialization errors, it doesn't check for other types of errors*/
void setFAN(const String& topic, const String& subtopic, const String& message) {
  DeserializationError err = deserializeJson(doc_rec, message);
  if (err) {
    Serial.println(F("deserializeJson() failed"));
    doc_rec.clear();
    return;
  }
  analogWrite(FAN_PIN, doc_rec["v"]);
  Serial.println(F("Request satisfied"));
  doc_rec.clear();
}

/*Function to manage incoming data for subscribed topic lcd/id. Warning: apart from deserialization errors, it doesn't check for other types of errors*/
void setlcd(const String& topic, const String& subtopic, const String& message) {
  DeserializationError err = deserializeJson(doc_rec, message);
  if (err) {
    Serial.println(F("deserializeJson() failed"));
    doc_rec.clear();
    return;
  }
  lcd.clear();
  for (int i = 0; ((char*)doc_rec["v"])[i] != '\0'; i++) {
    if (i == 16) {
      lcd.setCursor(0, 1);
    }
    lcd.print(((char*)doc_rec["v"])[i]);
  }
  Serial.println(F("Request satisfied"));
  doc_rec.clear();
}

/*Utility function to empty serial buffer*/
void empty_buffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}

/*Function for updating set-points through serial monitor*/
void checkforupdate() {
  int flag_presence_received, i;
  float setp[] = {0, 0, 0, 0};
  if (Serial.available() > 0) {
    flag_presence_received = Serial.parseInt();
    Serial.println(F("Now please send float values for AC min, AC max, HT min and HT max set-points"));
    empty_buffer();
    for (i = 0; i < 4; i++) {
      while (Serial.available() == 0);
      setp[i] = Serial.parseFloat();
      empty_buffer();
    }
    mqtt.publish("SP/" + id, senMlEncodeSP("\"sp" + String(flag_presence_received) + "\"", setp, F("\"Cel\"")));
    Serial.println(F("DONE. To update the 4 SP please send 0 or 1 so that I understand which case I have to modify"));
    empty_buffer();
  }
}

/*Function to check if millis() time register is in overflow (about every 50 days) and to reset variables to keep functioning*/
void checkOverflow() {
  if (millis() <= lastRegistration) {
    /*If in overflow condition => Reset, send registration to catalog*/
    mqtt.publish(F("catalog/devices"), senMlEncodeRegistration());
    lastRegistration = millis();
    delay(10);
  }
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

void loop() {
  bool flagPIRDetection = false;
  checkOverflow();
  if ((millis() - lastRegistration) >= 60000) {
    mqtt.publish(F("catalog/devices"), senMlEncodeRegistration());
    lastRegistration = millis();
    delay(10);
  }
  /*Send registration to catalog about every minute*/
  /*The following cycle allows to listen for about 8-10 seconds (or longer if there are many publish operations) on noise sensor without limiting the entire system.
     The purpose of it is to read multiple times from noise sensor (because a single read is unable to detect a noise if they're not sync) while also reading PIR
     values in order to not miss movements in the room.*/
  for (unsigned long i = 0; i < 500000; i++) {
    if (digitalRead(SOUND_PIN) == 0) {
      mqtt.publish("noise/" + id, senMlEncode(F("\"noise\""), 1, F("null")));
    }
    if (flagPIRDetection == false && digitalRead(PIR_PIN) == 1) {
      flagPIRDetection = true;
      mqtt.publish("PIR/" + id, senMlEncode(F("\"PIR\""), 1, F("null")));
    }
    /*The flag is used to limit the movement detection to a single publish (it's enough considering that, on server side, a single detection is enough to set the flag to true*/
  }
  mqtt.publish("temp/" + id, senMlEncode(F("\"temperature\""), get_temperature(), F("\"Cel\"")));
  /*Send temperature value*/
  mqtt.monitor();
  mqtt.monitor();
  mqtt.monitor();
  /*Monitor topic of interest*/
  checkforupdate();
  /*Check for set-points update on Serial Monitor*/
  delay(10);
}
