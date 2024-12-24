## **Esp32 Media Controller**

### To check out the newest version, check the latest branch.

This project, inspired by jailbroken Spotify car thing, ESP32 Spotify controls, and Deej, allows you to control your Windows media playing softwares (Spotify, browser, etc.) using an ESP32 board with a 2.4-inch TFT display.

**Features:**

- Media Controls: Play/Pause, Skip Next/Previous, Volume Control

- Customizable: Configure button and potentiometer functions in config.yaml.

- Multiple Controls: Supports multiple potentiometers for master volume and individual app volumes.
  
- Display: 2.4-inch TFT display for media information. Displays album art thumbnails.

**How it Works:**

The ESP32 reads button presses and potentiometer values.
Python script translates these inputs into media controls (e.g., Play/Pause, Volume Up).
Python interacts with Windows media sessions to control playback and retrieves album art thumbnails.
Python sends image data and media information to the ESP32.
ESP32 displays the album art and media information on the TFT display.
To Get Started:

- Install dependencies: pip install pycaw pywin32 pyserial pillow

- Configure config.yaml: Define button and potentiometer functions.

- Connect the TFT display to the ESP32.

- Run the Python script: python main.py

  
**Contributing:**

Contributions are welcome! Please check out the branches for the latest features and bug fixes.
