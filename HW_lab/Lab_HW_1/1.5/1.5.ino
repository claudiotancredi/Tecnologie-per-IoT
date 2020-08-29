#include <math.h>
const int TEMP_PIN = A0;

const float MAX = 1023.0;
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;

float getResistenceStep1(){
  int a = analogRead(TEMP_PIN);
  return (((MAX/a)-1)*R0);
}

float getTemperatureStep2(float R){
  return (1/((log(R/R0)/B)+(1/T0)));
}

void serialPrintStatus(float T){
  Serial.print("Temperature = ");
  Serial.println(T);
}

void setup() {
  pinMode(TEMP_PIN, INPUT);
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Welcome, Lab 1.5 Starting");
}

void loop() {
  delay(10000);
  float R = getResistenceStep1();
  float T = getTemperatureStep2(R);
  T = T-273.15;
  serialPrintStatus(T);
}
