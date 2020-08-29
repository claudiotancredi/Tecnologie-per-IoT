#include <math.h>
#include <LiquidCrystal_PCF8574.h>
#include <TimerThree.h>

LiquidCrystal_PCF8574 lcd(0x27);

/*GPIO pins*/
const int FAN_PIN = 6;
const int TEMP_PIN = A0;
const int RED_LED_PIN = 13;
const int PIR_PIN = 4;
const int SOUND_PIN = 7;

/*Utility constants*/
const int MAX_PWM_FAN_AND_LED = 255;
const int MAX_ANALOG_TEMP = 1023;
const int MIN = 0;
const float B = 4275.0;
const float R0 = 100000.0;
const float T0 = 298.15;
const float PIR_PERIOD = 0.5; /*0.5 s, period of PIR checking*/
const int TIMEOUT_PIR = 30 * 60;
const int N_SOUND_EVENTS = 50;
const int SOUND_INTERVAL = 10 * 60;
const int TIMEOUT_SOUND = 60 * 60;
const int NUMBER_OF_SET_POINTS = 4;
const int TEMP_PERIOD = 30; /*30 s, period of temperature checking*/

/*Global variables*/
float set_point_min_max_1[] = {22.0, 25.0, 16.0, 20.0}; /*default set-point to use when people detected*/
float set_point_min_max_0[] = {24.0, 28.0, 14.0, 18.0}; /*default set-point to use when people not detected*/
float set_point[] = {0, 0, 0, 0}; /*set-point in use*/
volatile unsigned long time_latest_detection_pir = 0;
volatile bool flag_pir_presence = true;
volatile bool flag_sound_presence = false;
bool flag_presence = false;
unsigned long time_latest_temperature_check = 0;
float T = 0;
volatile unsigned long *timestamps_last_10_minutes;/*dynamically allocated circular vector where 0 is flag for empty entry*/
volatile int tail = 0;
volatile bool flag_circular_vect = false;

/*Utility function to copy vector content into another.*/
void vector_copy(float v1[], float v2[], int n) {
  for (int i = 0; i < n; i++) {
    v1[i] = v2[i];
  }
}

/*ISR for sound sensor. Run when sound is detected.*/
void presence_detected() {
  if (millis() - timestamps_last_10_minutes[(tail - 1 + N_SOUND_EVENTS) % N_SOUND_EVENTS] > 50) {
    if (flag_circular_vect == false && tail + 1 == N_SOUND_EVENTS) {
      flag_circular_vect = true;
    }
    tail = tail % N_SOUND_EVENTS;
    timestamps_last_10_minutes[tail] = millis();
    if (flag_circular_vect == true && timestamps_last_10_minutes[tail] - timestamps_last_10_minutes[(tail + 1) % N_SOUND_EVENTS] < SOUND_INTERVAL * 1000) {
      flag_sound_presence = true;
    }
    tail++;
  }
}

/*ISR associated with Timer3 expiration. It checks for motion detection*/
void check_pir_presence() {
  int a = digitalRead(PIR_PIN);
  if (a == HIGH) {
    flag_pir_presence = true;
    time_latest_detection_pir = millis();
  }
}

/*setup function*/
void setup() {
  pinMode(FAN_PIN, OUTPUT);
  pinMode(TEMP_PIN, INPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(SOUND_PIN, INPUT);
  digitalWrite(RED_LED_PIN, MIN);
  digitalWrite(FAN_PIN, MIN);
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.clear();
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Welcome, in order to update the 4 set-point please send 0 or 1 so that I understand which case I have to modify (presence = 0 or presence=1)");
  Serial.println("Waiting for commands...");
  attachInterrupt(digitalPinToInterrupt(SOUND_PIN), presence_detected, FALLING);
  Timer3.initialize(PIR_PERIOD * 1e06);
  Timer3.attachInterrupt(check_pir_presence);
  timestamps_last_10_minutes = calloc(N_SOUND_EVENTS, sizeof(unsigned long));
}

/*Function to check if millis() time register is in overflow (about every 50 days) and to reset variables to keep functioning*/
void check_overflow() {
  bool flag_overflow = false;
  for (int i = 0; i < N_SOUND_EVENTS; i++) {
    if (millis() < timestamps_last_10_minutes[i]) {
      flag_overflow = true;
      break;
    }
  }
  if (flag_overflow == true || millis() < time_latest_detection_pir || millis() < time_latest_temperature_check) {
    for (int i; i < N_SOUND_EVENTS; i++) {
      timestamps_last_10_minutes[i] = 0;
    }
    time_latest_detection_pir = 0;
    time_latest_temperature_check = 0;
    flag_pir_presence = false;
    flag_sound_presence = false;
    flag_presence = false;
    flag_circular_vect = false;
    tail = 0;
  }
}

/*Function to check if PIR timeout has expired and eventually set PIR flag to false*/
void check_timeout_pir() {
  if (flag_pir_presence == true && (millis() - time_latest_detection_pir) / 1000 >= TIMEOUT_PIR) {
    flag_pir_presence = false;
  }
}

/*Function to check if sound sensor timeout has expired and eventually set sound sensor flag to false*/
void check_timeout_sound() {
  if (flag_sound_presence == true && (millis() - timestamps_last_10_minutes[(tail - 1 + N_SOUND_EVENTS) % N_SOUND_EVENTS]) / 1000 >= TIMEOUT_SOUND) {
    flag_sound_presence = false;
  }
}

/*Function to check if at least one of the two sensors (PIR & sound) detects presence and
   eventually set flag to true/false
*/
void check_presence() {
  if (flag_sound_presence == true || flag_pir_presence == true) {
    flag_presence = true;
  }
  else {
    flag_presence = false;
  }
}

/*Function to choose set-point in use based on flag_presence information*/
void choose_set_point() {
  switch (flag_presence) {
    case false: vector_copy(set_point, set_point_min_max_0, NUMBER_OF_SET_POINTS);
      break;
    case true: vector_copy(set_point, set_point_min_max_1, NUMBER_OF_SET_POINTS);
      break;
  }
}

/*Function for getting temperature measure*/
void set_temperature() {
  int a = analogRead(TEMP_PIN);
  float R = ((MAX_ANALOG_TEMP / (float)a) - 1) * R0;
  T = (1 / ((log(R / R0) / B) + (1 / T0))) - 273.15;
  time_latest_temperature_check = millis();
}

/*Function for checking temperature sensor every 30 s*/
void check_temperature() {
  if (time_latest_temperature_check == 0) {
    set_temperature();
  }
  else if ((millis() - time_latest_temperature_check) / 1000 >= TEMP_PERIOD) {
    set_temperature();
  }
}

/*Function to manage FAN module (AC). It also returns percentage of intensity*/
int manage_FAN() {
  int percentage;
  if (T > set_point[0] && T < set_point[1]) {
    analogWrite(FAN_PIN, (int)((T - set_point[0]) / (set_point[1] - set_point[0])*MAX_PWM_FAN_AND_LED));
    percentage = (T - set_point[0]) / (set_point[1] - set_point[0]) * 100;
  }
  else if (T <= set_point[0]) {
    analogWrite(FAN_PIN, MIN);
    percentage = 0;
  }
  else {
    analogWrite(FAN_PIN, MAX_PWM_FAN_AND_LED);
    percentage = 100;
  }
  return percentage;
}

/*Function to manage LED (HT). It also returns percentage of intensity*/
int manage_RED_LED() {
  int percentage;
  if (T > set_point[2] && T < set_point[3]) {
    analogWrite(RED_LED_PIN, (int)(MAX_PWM_FAN_AND_LED - ((T - set_point[2]) / (set_point[3] - set_point[2])*MAX_PWM_FAN_AND_LED)));
    percentage = 100 - ((T - set_point[2]) / (set_point[3] - set_point[2]) * 100);
  }
  else if (T <= set_point[2]) {
    analogWrite(RED_LED_PIN, MAX_PWM_FAN_AND_LED);
    percentage = 100;
  }
  else {
    analogWrite(RED_LED_PIN, MIN);
    percentage = 0;
  }
  return percentage;
}

/*Function for showing informations on the display*/
void printStatus(int pFAN, int pLED) {
  lcd.clear();
  lcd.print("T:");
  lcd.print(T, 1); /*1 allows to show only a decimal place*/
  lcd.print(" Pres:");
  lcd.print(flag_presence);
  lcd.setCursor(0, 1); /*first parameter is column number, the second one is row number*/
  lcd.print("AC:");
  lcd.print(pFAN);
  lcd.print("% HT:");
  lcd.print(pLED);
  lcd.print("%");
  delay(2000); /*2 s informations on display*/
  lcd.clear();
  lcd.print("AC m:");
  lcd.print(set_point[0], 1);
  lcd.print(" M:");
  lcd.print(set_point[1], 1);
  lcd.setCursor(0, 1);
  lcd.print("HT m:");
  lcd.print(set_point[2], 1);
  lcd.print(" M:");
  lcd.print(set_point[3], 1);
  delay(2000); /*2 s informations on display*/
}

/*Utility function to empty serial buffer*/
void empty_buffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}

/*Function for updating set-point through serial monitor*/
void checkforupdate() {
  bool flag_error = false;
  int flag_presence_received, i;
  float setp[] = {0, 0, 0, 0};
  if (Serial.available() > 0) {
    flag_presence_received = Serial.parseInt();
    Serial.print("Inserted: ");
    Serial.println(flag_presence_received);
    if (flag_presence_received != 0 && flag_presence_received != 1) {
      flag_error = true;
    }
    if (flag_error == false) {
      Serial.println("Now please send float values for AC min set-point, AC max set-point, HT min set-point, HT max set-point (in this order!).");
      Serial.println("You have a 5 seconds timer for each input.");
      empty_buffer();
      for (i = 0; i < 4 && flag_error == false; i++) {
        delay(5000);
        if (Serial.available() > 0) {
          setp[i] = Serial.parseFloat();
          Serial.print("Inserted: ");
          Serial.println(setp[i]);
          empty_buffer();
        }
        else {
          flag_error = true;
        }
      }
    }
    if (flag_error == true) {
      Serial.println("ERROR.");
    }
    else {
      Serial.println("UPDATE WENT WELL.");
      switch (flag_presence_received) {
        case 0: vector_copy(set_point_min_max_0, setp, NUMBER_OF_SET_POINTS);
          break;
        case 1: vector_copy(set_point_min_max_1, setp, NUMBER_OF_SET_POINTS);
          break;
      }
    }
    Serial.println("In order to update the 4 set-point please send 0 or 1 so that I understand which case I have to modify (presence = 0 or presence=1)");
    Serial.println("Waiting for commands...");
    empty_buffer();
  }
}

void loop() {
  int percentageFAN, percentageLED;
  noInterrupts();
  check_overflow();
  check_timeout_pir();
  check_timeout_sound();
  check_presence();
  interrupts();
  choose_set_point();
  check_temperature();
  percentageFAN = manage_FAN();
  percentageLED = manage_RED_LED();
  printStatus(percentageFAN, percentageLED);
  checkforupdate();
}
