import pyserial
import media_session
import volume_potentiometer
import keyboard_event
import time
from numpy import interp
import yaml


def process_received_data(data, volume_obj, total_switches_sliders
                          , no_of_switches, no_of_sliders, prev_btn_states,
                          switch_functions, slider_functions):
    if data is None or len(data) != total_switches_sliders:
        return

    for i in range(no_of_switches):
        try:
            current_value = int(data[i])

            if prev_btn_states[i] >= 4000 and current_value < 100:
                print(f"BUTTON PRESSED: {i + 1}")
                keyboard_event.validate_key(switch_functions[i])

            # Update the previous state
            prev_btn_states[i] = current_value
        except Exception as e:
            print(f"Cannot read data, ignoring: {e}")
            break

    for i in range(no_of_sliders):
        try:
            vol_lvl = map_potentiometer_value(data[no_of_switches + i])
            volume_obj.set_volume(name=slider_functions[i], value=vol_lvl)
        except Exception as e:
            print(f"Cannot set volume error: {e}")


def map_potentiometer_value(value):
    return int(interp(int(value), [5, 4090], [0, 100]))


def main():
    try:
        with open('config.yaml', 'r') as file:
            file_service = yaml.safe_load(file)
            switch_functions = file_service['switch_functions']
            slider_functions = file_service['slider_functions']

            no_of_switches = len(switch_functions)
            no_of_sliders = len(slider_functions)
            total_switches_sliders = no_of_switches + no_of_sliders

            prev_btn_states = [4095] * no_of_switches

    except Exception as e:
        print(f"Error reading config.yaml: {e}")
        return

    serial_obj = pyserial.SerialConnection(total_switches_sliders)
    time.sleep(1)
    volume_obj = volume_potentiometer.VolumeControl()
    time.sleep(1)
    media_obj = media_session.Media()
    time.sleep(1)

    print("Everything Initialised")

    try:
        while True:
            process_received_data(data=serial_obj.data, volume_obj=volume_obj,
                                  total_switches_sliders=total_switches_sliders,
                                  no_of_switches=no_of_switches, no_of_sliders=no_of_sliders,
                                  prev_btn_states=prev_btn_states, switch_functions=switch_functions,
                                  slider_functions=slider_functions)

            time.sleep(0.01)

    except Exception as e:
        print(f"Exception occurred, stopping: {e}")

    finally:
        media_obj.stop()
        serial_obj.stop()
        keyboard_event.key_listener.stop()


if __name__ == "__main__":
    main()
