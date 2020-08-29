#include <math.h>
#include <LiquidCrystal_PCF8574.h>

LiquidCrystal_PCF8574 lcd(0x27);

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

void printStatus(float T){
  lcd.setCursor(12, 0);
  lcd.print(T,1);
}

void setup() {
  pinMode(TEMP_PIN, INPUT);
  lcd.begin(16,2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();
  lcd.print("Temperature:");
}

void loop() {
  delay(10000);
  float R = getResistenceStep1();
  float T = getTemperatureStep2(R);
  T = T-273.15;
  printStatus(T);
}
