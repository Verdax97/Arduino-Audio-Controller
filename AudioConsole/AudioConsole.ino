#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
StaticJsonDocument<24> exitJson;

#define OLED_RESET 4
Adafruit_SSD1306 display(128, 64, &Wire, OLED_RESET);

float last1;
float last2;

void setup()
{
  pinMode(A0, INPUT);
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C); //or 0x3D
  display.clearDisplay(); //for Clearing the display
  display.display();
  
  Serial.begin(9600);
  while (!Serial) continue;
  
  askForImage(0);
  askForImage(1);
  display.display();
}
float getCurrentValue(int pin)
{
  int val = analogRead(pin);
  return (float)val / 1023;
}
void askForImage(int start)
{
  //read 64 lines of the image
  for (int i = 0; i < 64; i++)
  {
    //read 64/8 column
    for (int j = 56 + start * 64; j >= 0 + start * 64; j -= 8)
    {
      while (Serial.available() == 0) {
      }
      uint8_t val = Serial.read();
      //cycle over the bits in the 8 bit val
      for (int k = 7; k >= 0; k--)
      {
        int color = bitRead(val, k);
        if (color > 0)
          display.drawPixel(j + k, i, WHITE);
      }
    }
  }
}

void loop()
{
  int next = digitalRead(8);
  int cmd = next;
  exitJson["command"] = cmd;
  if (cmd == 0)
  {
    float val1 = getCurrentValue(0);
    float diff1 = last1 - val1;
    float val2 = getCurrentValue(1);
    float diff2 = last2 - val2;

    exitJson["value1"] = val1;
    exitJson["value2"] = val2;
    //send values only if the values difference is greather than 0.5%
    if (abs(diff1) >= 0.005f || abs(diff2) >= 0.005)
    {
      last1 = val1;
      last2 = val2;
      serializeJson(exitJson, Serial);
      Serial.println();
    }
  }
  else if (cmd == 1)
  {
    serializeJson(exitJson, Serial);
    Serial.println();
    
    display.clearDisplay(); //for Clearing the display
    display.display();
    askForImage(0);
    askForImage(1);
    display.display();
  }
  delay(10);
}
