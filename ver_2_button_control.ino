// Button configuration
struct Button {
    const uint8_t pin;            // GPIO pin number
    const char* name;             // Button name for serial output
    volatile bool flag;           // Flag for new button press
    volatile unsigned long prev_time;    // Changed to unsigned long for millis()
    volatile uint8_t state;       // Current debounced state
};

// Button definitions
Button buttons[] = {
    {12, "SKIP_PREV", false, 0, LOW},
    {14, "PLAY", false, 0, LOW},
    {27, "SKIP_NEXT", false, 0, LOW},
    {26, "MUTE", false, 0, LOW},
    {32, "VOL_UP", false, 0, LOW},
    {25, "VOL_DOWN", false, 0, LOW}
};

const uint8_t NUM_BUTTONS = sizeof(buttons) / sizeof(buttons[0]);
const uint16_t DEBOUNCE_DELAY = 50;    // Adjust this value based on your buttons

// Combined ISR for all buttons
void IRAM_ATTR button_isr(void* arg) {
    Button* button = (Button*)arg;
    unsigned long current_time = millis();
    
    // Check if enough time has passed AND pin is actually HIGH
    if ((current_time - button->prev_time > DEBOUNCE_DELAY) && digitalRead(button->pin)) {
        button->flag = true;
        button->prev_time = current_time;
    }
}

void setup() {
    Serial.begin(115200);
    
    // Setup pins and interrupts
    for(int i = 0; i < NUM_BUTTONS; i++) {
        pinMode(buttons[i].pin, INPUT);        // Using external pulldown
        
        // Attach interrupts with error checking
        if (digitalPinToInterrupt(buttons[i].pin) != -1) {
            attachInterruptArg(
                digitalPinToInterrupt(buttons[i].pin),
                button_isr,
                &buttons[i],
                RISING
            );
        }
    }

}

void loop() {
    // Check for button presses
    for(int i = 0; i < NUM_BUTTONS; i++) {
        if(buttons[i].flag) {
            // Double-check the pin state
            if(digitalRead(buttons[i].pin) == HIGH) {
                // Serial.print("Button pressed: ");
                Serial.println(buttons[i].name);
            }
            buttons[i].flag = false;
        }
    }
    
    // Handle serial communication
    if (Serial.available()) {
        String received = Serial.readStringUntil('\n');
        if (received == "PING") {
            Serial.println("ALIVE");
        }
    }

    // Small delay to prevent CPU hogging
    delay(10);
}