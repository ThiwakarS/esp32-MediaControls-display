#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <TJpg_Decoder.h>

// TFT Display Pins
#define TFT_CS   15
#define TFT_DC   2
#define TFT_RST  -1

// Display dimensions
#define TFT_WIDTH  240
#define TFT_HEIGHT 320

// Max image size
#define MAX_IMAGE_SIZE 90000

TaskHandle_t send_slider_values_task;

// Create TFT display object
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

// Image receive buffer
uint8_t imageBuffer[MAX_IMAGE_SIZE];

const int NUM_SLIDERS = 11;
const int analog_inputs[] = { 13, 27, 26, 25, 33, 32, 35, 34, 39, 36, 4 };
volatile int analog_slider_values[NUM_SLIDERS];

void updateSliderValues() {
  for (int i = 0; i < NUM_SLIDERS; i++) {
    analog_slider_values[i] = analogRead(analog_inputs[i]);
  }
}

void sendSliderValues() {
  String builtString = String("");

  for (int i = 0; i < NUM_SLIDERS; i++) {
    builtString += String((int)analog_slider_values[i]);

    if (i < NUM_SLIDERS - 1) {
      builtString += String("|");
    }
  }

  Serial.println(builtString);
}

//////////////////////////////////////////////////////////////////////////
/////////////////////////// SETUP SECTION ////////////////////////////////
////////////////////////////////////////////////////////////////////////// 

void setup() {
  Serial.begin(115200);

  // Initialize TFT display
  tft.init(TFT_WIDTH, TFT_HEIGHT);
  tft.setRotation(3);  // Landscape mode
  tft.invertDisplay(false);
  tft.fillScreen(ST77XX_BLACK);

  for (int i = 0; i < NUM_SLIDERS; i++) {
    pinMode(analog_inputs[i], INPUT_PULLDOWN);
  }

  xTaskCreatePinnedToCore(
      send_slider_values_code, /* Function to implement the task */
      "send_slider_Values", /* Name of the task */
      10000,  /* Stack size in words */
      NULL,  /* Task input parameter */
      0,  /* Priority of the task */
      &send_slider_values_task,  /* Task handle. */
      0); /* Core where the task should run */

  Serial.println("ESP32 Ready");
}

//////////////////////////////////////////////////////////////////////////
//////////////////////IMAGE TRANSMISSION SECTION//////////////////////////
////////////////////////////////////////////////////////////////////////// 

void loop() {
  processIncomingSerial();
  delay(10);
}

// Function to process serial communication
void processIncomingSerial() {
  if (Serial.available()) {
    // Check for "PING" command
    if (Serial.peek() == 'P') {
      String command = Serial.readStringUntil('\n');
      if (command == "PING") {
        Serial.println("ALIVE");
        return;
      }
    }

    // If data length >= 4, assume it's the image size
    if (Serial.available() >= 4) {
      uint32_t imageSize = 0;
      Serial.readBytes((char*)&imageSize, 4);

      // Validate the image size
      if (imageSize > MAX_IMAGE_SIZE) {
        Serial.println("Error: Image too large!");
        return;
      }

      // Acknowledge the size
      Serial.println("ACK");

      // Receive image data
      if (receiveImageData(imageSize)) {
        // Display the image on the TFT
        displayImage(imageSize);

        // Send "D" to indicate image received and displayed
        Serial.println("DONE");
      }
    }
  }
}

// Function to receive the image data
bool receiveImageData(uint32_t imageSize) {
  uint32_t receivedBytes = 0;

  while (receivedBytes < imageSize) {
    if (Serial.available()) {
      int bytesToRead = min(Serial.available(), (int)(imageSize - receivedBytes));
      Serial.readBytes(&imageBuffer[receivedBytes], bytesToRead);
      receivedBytes += bytesToRead;
    }
  }

  return receivedBytes == imageSize;
}

bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t* bitmap)
{
  // Stop further decoding as the image will not fit on the screen
  if ( y >= tft.height() ) return 0;

  // This function will be called during decoding
  tft.drawRGBBitmap(x, y, bitmap, w, h);
  return 1; // Continue decoding
}

void displayImage(uint32_t imageSize) {
  tft.fillScreen(ST77XX_BLACK);  // Clear screen

  // Configure the decoder
  TJpgDec.setJpgScale(1);
  TJpgDec.setCallback(tft_output);

  // Decode the image from the buffer
  TJpgDec.drawJpg(0, 0, imageBuffer, imageSize);
}

//////////////////////////////////////////////////////////////////////////
///////////////////////// SLIDER VALUES SECTION //////////////////////////
//////////////////////////////////////////////////////////////////////////


void send_slider_values_code(void * parameter)
{
  for(;;)
  {
    updateSliderValues();
    sendSliderValues();

    delay(20);
  }
}
