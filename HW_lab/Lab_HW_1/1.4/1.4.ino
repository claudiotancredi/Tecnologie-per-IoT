const int FAN_PIN = 10;

/*GPIO pins are identified by integer constants*/

const int MAX = 255;
const float STEP = 25.5;
const int MIN = 0;

float current_speed = MIN;
/*This is a global variable to store the current speed of the module.*/

void serialPrintStatus(){
  if (Serial.available()>0){
    int inByte = Serial.read();

    switch(inByte){
      case '+':
        if (current_speed+STEP>MAX){
          Serial.println("Already at max speed");
        }
        else{
          Serial.print("Increasing speed: ");
          current_speed+=STEP;
          float perc = current_speed/MAX*100;
          Serial.print(perc);
          Serial.println("%");
          analogWrite(FAN_PIN, (int)current_speed);
        }
        break;
      case '-': 
        if (current_speed-STEP<MIN){
          Serial.println("Already at min speed");
        }
        else{
          Serial.print("Decreasing speed: ");
          current_speed-=STEP;
          int perc = current_speed/MAX*100;
          Serial.print(perc);
          Serial.println("%");
          analogWrite(FAN_PIN, (int)current_speed);
        }
        break;
      default: 
        Serial.println("Invalid command");
        break;
    }
  }
}

void setup() {
  pinMode(FAN_PIN, OUTPUT);
  analogWrite(FAN_PIN, (int)current_speed);
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Welcome, Lab 1.4 Starting");
}

void loop() {
  serialPrintStatus();
}
