#include <TimerOne.h>
/*TimerOne.h allows to attach interrupts to the MCU's Timer1*/

const int RLED_PIN = 12;
const int GLED_PIN = 11;
/*GPIO pins are identified by integer constants*/

const float R_HALF_PERIOD = 1.5;
const float G_HALF_PERIOD = 3.5;

volatile int greenLedState = LOW;
int redLedState = LOW;
/*These are global variables to store the current state of the two LEDS.
LOW and HIGH are macros for 0 and 1 respectively*/

void blinkGreen(){
  greenLedState = !greenLedState;
  digitalWrite(GLED_PIN, greenLedState);
}

void serialPrintStatus(){
  if (Serial.available()>0){
    int inByte = Serial.read();

    switch(inByte){
      case 'R': Serial.print("LED 12 (R) Status: "); Serial.println(redLedState); break;
      case 'L': Serial.print("LED 11 (G) Status: "); Serial.println(greenLedState);break;
      default: Serial.println("Invalid command");
    }
  }
}

void setup() {
  pinMode(RLED_PIN, OUTPUT);
  pinMode(GLED_PIN, OUTPUT);
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Welcome, Lab 1.2 Starting");
  Timer1.initialize(G_HALF_PERIOD * 1e06);
  Timer1.attachInterrupt(blinkGreen);
}

void loop() {
  serialPrintStatus();
  redLedState = !redLedState;
  digitalWrite(RLED_PIN, redLedState);
  delay(R_HALF_PERIOD * 1e03);
}
