const int RLED_PIN = 12;
const int PIR_PIN = 7;
/*GPIO pins are identified by integer constants*/

volatile int tot_count = 0;
int redLedState = LOW;
/*These are global variables to store the current state of the LED and the number of total events.
LOW and HIGH are macros for 0 and 1 respectively*/

void checkPresence(){
  redLedState = !redLedState;
  digitalWrite(RLED_PIN, redLedState);
  if (redLedState==HIGH){
    tot_count++;
  }
}

void serialPrintStatus(){
  Serial.print("Total people count: ");
  Serial.println(tot_count);
}

void setup() {
  pinMode(RLED_PIN, OUTPUT);
  pinMode(PIR_PIN, INPUT);
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Welcome, Lab 1.3 Starting");
  attachInterrupt(digitalPinToInterrupt(PIR_PIN), checkPresence, CHANGE);
}

void loop() {
  delay(30000);
  serialPrintStatus();
}
