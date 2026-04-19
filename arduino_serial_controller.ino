#include <Servo.h>

Servo servoMotor;
int servoPin = -1;

void setup() {
  Serial.begin(9600);
  Serial.println("Arduino ready");
  Serial.println("Commands: D pin 0|1, P pin 0-255, S pin 0-180, R pin");
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.length() == 0) {
    return;
  }

  handleCommand(command);
}

void handleCommand(String command) {
  char mode = command.charAt(0);

  if (mode == 'D') {
    int pin;
    int value;
    if (sscanf(command.c_str(), "D %d %d", &pin, &value) == 2) {
      pinMode(pin, OUTPUT);
      digitalWrite(pin, value ? HIGH : LOW);
      Serial.print("OK digital pin ");
      Serial.print(pin);
      Serial.print(" = ");
      Serial.println(value ? "HIGH" : "LOW");
    } else {
      Serial.println("ERR usage: D pin 0|1");
    }
  } else if (mode == 'P') {
    int pin;
    int value;
    if (sscanf(command.c_str(), "P %d %d", &pin, &value) == 2) {
      value = constrain(value, 0, 255);
      pinMode(pin, OUTPUT);
      analogWrite(pin, value);
      Serial.print("OK pwm pin ");
      Serial.print(pin);
      Serial.print(" = ");
      Serial.println(value);
    } else {
      Serial.println("ERR usage: P pin 0-255");
    }
  } else if (mode == 'S') {
    int pin;
    int angle;
    if (sscanf(command.c_str(), "S %d %d", &pin, &angle) == 2) {
      angle = constrain(angle, 0, 180);
      if (servoPin != pin) {
        servoMotor.detach();
        servoMotor.attach(pin);
        servoPin = pin;
      }
      servoMotor.write(angle);
      Serial.print("OK servo pin ");
      Serial.print(pin);
      Serial.print(" = ");
      Serial.println(angle);
    } else {
      Serial.println("ERR usage: S pin 0-180");
    }
  } else if (mode == 'R') {
    int pin;
    if (sscanf(command.c_str(), "R %d", &pin) == 1) {
      pinMode(pin, INPUT);
      Serial.print("OK read pin ");
      Serial.print(pin);
      Serial.print(" = ");
      Serial.println(digitalRead(pin));
    } else {
      Serial.println("ERR usage: R pin");
    }
  } else {
    Serial.print("ERR unknown command: ");
    Serial.println(command);
  }
}
