#include <Process.h>
#include <Bridge.h>
#include <BridgeServer.h>
#include <BridgeClient.h>

/*Utility constants*/
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;
const int MAX_ANALOG_TEMP = 1023;
const int TEMP_PIN = A0;

/*Global variables*/
BridgeServer server;
unsigned long lastRegistration = 0;
/*Timestamp for last registration to catalog*/
String IP = "";
/*IP address of device*/
String id = "";
/*Unique identifier of device*/

/*Setup function*/
void setup() {
  pinMode(TEMP_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  /*Internal LED*/
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  Bridge.begin();
  while (!Serial);
  digitalWrite(LED_BUILTIN, HIGH);
  /*Turn on internal LED when connection is enstablished*/
  randomSeed(analogRead(5));
  id = String(random(2147483647)) + "YUN";
  /*Generating the id for the device*/
  Process wifiCheck;
  wifiCheck.runShellCommand(F("/usr/bin/pretty-wifi-info.lua | grep \"IP address\" | cut -f2 -d\":\" | cut -f1 -d\"/\"" ));
  /*Command used to retrieve IP address of device*/
  while (wifiCheck.available() > 0) {
    char c = wifiCheck.read();
    IP += c;
  }
  IP.trim();
  /*IP is now ready to be used*/
  postRequestRegistration(senMlEncodeRegistration());
  lastRegistration = millis();
  /*First registration to catalog at device booting*/
  server.listenOnLocalhost();
  server.begin();
  /*Start the server, it will respond to temperature GET requests*/
}

/*Function for encoding info used during registration to catalog into JSON*/
String senMlEncodeRegistration() {
  String output = "{\"ID\":\"" + id + (F("\",\"PROT\":\"REST\",\"IP\":\"")) + IP + (F("\",\"P\":80,\"ED\":{\"S\":[\"arduino/temperature\"]},\"AR\":[\"Temp\"]}"));
  //Serial.println(output);
  return output;
}

/*Function for encoding temperature info into JSON*/
String senMlEncode(String res, float v, String unit) {
  String output = "{\"n\":" + res + ",\"v\":" + String(v) + ",\"u\":" + unit + "}";
  //Serial.println(output);
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

/*Function for using curl command and send POST request to server for catalog registration*/
void postRequestRegistration(String data) {
  Process p;
  p.begin("curl");
  p.addParameter("-H");
  p.addParameter("Content-Type: application/json");
  p.addParameter("-X");
  p.addParameter("POST");
  p.addParameter("-d");
  p.addParameter(data);
  p.addParameter("http://192.168.8.143:8080/catalog/devices");
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

/*Function used to provide output*/
void printResponse(BridgeClient client, int code, String body) {
  client.println("Status: " + String(code));
  if (code == 200) {
    client.println(F("Content-type: application/json; charset=utf-8"));
    client.println();
    client.println(body);
  }
}

/*Function used to process new GET requests*/
void process(BridgeClient client) {
  String command = client.readStringUntil('/');
  /*Parse 1st URL element*/
  command.trim();
  /*Delete \n or similar*/
  if (command == "temperature") {
    printResponse(client, 200, senMlEncode("\"temperature\"", get_temperature(), "\"Cel\""));
  }
  else {
    printResponse(client, 404, F(""));
  }
}

/*Function to check if millis() time register is in overflow (about every 50 days) and to reset variables to keep functioning*/
void checkOverflow() {
  if (millis() <= lastRegistration) {
    /*If in overflow condition => Reset and send registration to catalog*/
    postRequestRegistration(senMlEncodeRegistration());
    lastRegistration = millis();
    delay(10);
  }
}

void loop() {
  BridgeClient client = server.accept();
  if (client) {
    process(client);
    client.stop();
  }
  /*Check for incoming GET requests and eventually submit temperature info*/
  checkOverflow();
  if ((millis() - lastRegistration) >= 60000) {
    postRequestRegistration(senMlEncodeRegistration());
    lastRegistration = millis();
  }
  /*Send registration to catalog about every minute*/
  delay(10);
}
