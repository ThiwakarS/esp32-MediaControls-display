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


void setup() {
  // put your setup code here, to run once:
  for (int i = 0; i < NUM_SLIDERS; i++) {
    pinMode(analog_inputs[i], INPUT_PULLDOWN);
  }

  Serial.begin(115200);
}

void loop() {

  updateSliderValues();
  sendSliderValues();  // Actually send data (all the time)

  // Handle serial communication
  if (Serial.available()) {
    String received = Serial.readStringUntil('\n');
    if (received == "PING") {
      Serial.println("ALIVE");
    }
  }
  
  delay(50);
}
