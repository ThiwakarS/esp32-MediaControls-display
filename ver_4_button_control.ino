#include <BfButton.h>


const int btns[] = { 12, 14, 27, 26 };
const int master_vol_pin = 25;
volatile int prev_vol_lvl = 0, master_vol = 0;
unsigned long last_vol_change_time = 0;
const unsigned long STABILITY_DELAY = 500;  // 500 milliseconds of no change
volatile bool vol_changed = false, vol_change_accepted = false;


BfButton skip_prev(BfButton::STANDALONE_DIGITAL, btns[0], false, HIGH);
BfButton play(BfButton::STANDALONE_DIGITAL, btns[1], false, HIGH);
BfButton skip_next(BfButton::STANDALONE_DIGITAL, btns[2], false, HIGH);
BfButton mute(BfButton::STANDALONE_DIGITAL, btns[3], false, HIGH);

int Value_Mapper(int value) {
  return map(value, 0, 4095, 0, 100);
}

//Button press hanlding function
void Skip_Prev_Handler(BfButton *btn, BfButton::press_pattern_t pattern) {
  if (pattern == BfButton::SINGLE_PRESS)
    Serial.println("SKIP_PREV");
}

void Play_Handler(BfButton *btn, BfButton::press_pattern_t pattern) {
  if (pattern == BfButton::SINGLE_PRESS)
    Serial.println("PLAY");
}

void Skip_Next_Handler(BfButton *btn, BfButton::press_pattern_t pattern) {
  if (pattern == BfButton::SINGLE_PRESS)
    Serial.println("SKIP_NEXT");
}

void Mute_Handler(BfButton *btn, BfButton::press_pattern_t pattern) {
  if (pattern == BfButton::SINGLE_PRESS)
    Serial.println("MUTE");
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(master_vol_pin, INPUT);

  skip_prev.onPress(Skip_Prev_Handler);
  play.onPress(Play_Handler);
  skip_next.onPress(Skip_Next_Handler);
  mute.onPress(Mute_Handler);
}

void loop() {

  //Wait for button press to execute commands
  skip_prev.read();
  play.read();
  skip_next.read();
  mute.read();

  // Handle serial communication
  if (Serial.available()) {
    String received = Serial.readStringUntil('\n');
    if (received == "PING") {
      Serial.println("ALIVE");
    }

    else if (received == "VOL_ACP") {
      vol_change_accepted = true;
    }
  }

  // Read and map potentiometer value
  master_vol = Value_Mapper(analogRead(master_vol_pin));

  // Check if volume has changed significantly
  if (abs(master_vol - prev_vol_lvl) >= 2) {
    prev_vol_lvl = master_vol;
    last_vol_change_time = millis();
    vol_changed = true;
    vol_change_accepted = false;
  }

  // Print only when volume stabilizes
  if (vol_changed && (millis() - last_vol_change_time > STABILITY_DELAY)) {
    if (vol_change_accepted == false) {
      Serial.println("VOL " + String(master_vol));
    }

    else 
    {
      vol_changed = false;
    }

    last_vol_change_time = millis();
  }

  // Small delay to prevent CPU hogging
  delay(10);
}
