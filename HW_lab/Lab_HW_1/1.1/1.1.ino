#include <TimerOne.h>
/*TimerOne.h allows to attach interrupts to the MCU's Timer1*/

const int RLED_PIN = 12;
const int GLED_PIN = 11;
/*GPIO pins are identified by integer constants*/

const float R_HALF_PERIOD = 1.5;
const float G_HALF_PERIOD = 3.5;

int greenLedState = LOW;
int redLedState = LOW;
/*These are global variables to store the current state of the two LEDS. LOW and HIGH are macros for 0 and 1 respectively*/

void blinkGreen(){
  greenLedState = !greenLedState;
  digitalWrite(GLED_PIN, greenLedState);
}

void setup() {
  pinMode(RLED_PIN, OUTPUT);
  pinMode(GLED_PIN, OUTPUT);
  Timer1.initialize(G_HALF_PERIOD * 1e06);
  Timer1.attachInterrupt(blinkGreen);
}

void loop() {
  redLedState = !redLedState;
  digitalWrite(RLED_PIN, redLedState);
  delay(R_HALF_PERIOD * 1e03);
}
