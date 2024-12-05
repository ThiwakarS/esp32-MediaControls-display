from pynput import keyboard


class KeyboardHandler:

    def __init__(self):
        self.key_listener = keyboard.Listener(
            on_press=on_press)

        self.key_controller = keyboard.Controller()

    def press_key(self, key: keyboard.Key):
        self.key_controller.press(key)
        self.key_controller.release(key)


def on_press(key: keyboard.Key):
    try:
        if key == keyboard.Key.media_play_pause:
            print("Play pause pressed")
        elif key == keyboard.Key.media_next:
            print("Skip next pressed")
        elif key == keyboard.Key.media_previous:
            print("Skip previous pressed")
        elif key == keyboard.Key.media_volume_mute:
            print("volume mute pressed")

    except AttributeError:
        print("Attribute error")
    except Exception as e:
        print("Key error: " + str(e))
