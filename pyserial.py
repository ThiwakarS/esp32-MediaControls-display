import time
import serial
import serial.tools.list_ports_windows
import logging
import threading

class SerialConnection:
    def __init__(self, total_no_of_switches_sliders):

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Serial connection parameters
        self.COM_PORT = None
        self.BAUD_RATE = 115200
        self.ser = None
        self.data = []
        self.connected = False
        self.total_no_of_switches_sliders = total_no_of_switches_sliders
        # Keyboard and volume handlers
        # self.keyboard_handler = keyboard_event.KeyboardHandler()
        # self.keyboard_handler.key_listener.start()
        # self.volume_handler = volume_potentiometer.VolumeControl()
        # self._prev_button_states = [4095] * NO_OF_SWITCHES

        # Synchronization events
        self.connection_event = threading.Event()
        self.stop_event = threading.Event()

        # Start connection and read threads
        self.serial_connection_thread = threading.Thread(
            target=self._start_and_check_conn_thread,
            daemon=True
        )
        self.serial_read_thread = threading.Thread(
            target=self._read_data_thread,
            daemon=True
        )

        self.serial_connection_thread.start()
        self.serial_read_thread.start()

    def _start_and_check_conn_thread(self):
        """Continuously manage serial connection."""
        while not self.stop_event.is_set():
            try:
                if not self.connected:
                    self._start_connection()
                else:
                    self._check_connection()

            except Exception as e:
                self.logger.error(f"Connection management error: {e}")
                self.connected = False

            time.sleep(5)

    def _start_connection(self):
        """Find and establish connection with ESP32."""
        if self.ser and self.ser.is_open:
            self.ser.close()

        ports = self._find_esp32_port()
        if not ports:
            self.logger.warning("No ESP32 ports found")
            return

        for port in ports:
            try:
                self.ser = serial.Serial(
                    port=port,
                    baudrate=self.BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1
                )
                self.COM_PORT = port
                self.connected = True
                self.connection_event.set()
                self.logger.info(f"Connected to ESP32 on {self.COM_PORT}")
                return
            except (serial.SerialException, OSError) as e:
                self.logger.error(f"Failed to connect to {port}: {e}")

    def _check_connection(self):
        """Verify active serial connection."""
        if not self.ser or not self.ser.is_open:
            self.connected = False
            return

        try:
            # Send a ping and check response
            self.ser.reset_input_buffer()
            self.ser.write(b'PING\n')

        except Exception as e:
            self.logger.error(f"Connection verification failed: {e}")
            self.connected = False

    def _read_data_thread(self):
        """Read serial data continuously."""
        while not self.stop_event.is_set():
            try:
                # Wait for connection to be established
                self.connection_event.wait(timeout=5)

                if self.connected and self.ser and self.ser.is_open:
                    data = self._read_serial_data()
                    if data and data[0] == "ALIVE":
                        self.connected = True
                    elif data and len(data) == self.total_no_of_switches_sliders:
                        self.data = data
                        ### PROCESSING RECEIVED DATA FOR BUTTONS AND SWITCHES
                        ### IS DONE IN MAIN.PY FILE

                    else:
                        self.data = []

                time.sleep(0.01)

            except Exception as e:
                self.logger.error(f"Data reading error: {e}")
                self.connected = False
                time.sleep(1)

    def _read_serial_data(self):
        """Read and parse serial data."""
        try:
            if self.ser.in_waiting:
                raw_data = self.ser.readline()
                data = raw_data.decode('utf-8', errors='ignore').strip()
                data = data.split('|')

                if data:
                    return data

                return None

        except Exception as e:
            self.logger.error(f"Serial data reading error: {e}")
        return None

    @staticmethod
    def _find_esp32_port():
        """Find available ESP32 USB ports."""
        ports = serial.tools.list_ports_windows.comports()
        return [port.device for port in ports if "USB" in str(port.hwid)]

    def stop(self):
        """Stop all threads and close connection."""
        self.stop_event.set()
        self.connection_event.set()
        # self.media_obj.stop()
        # self.keyboard_handler.key_listener.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()


# def main():
#     serial_obj = SerialConnection()
#     # Keep the main thread running
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("Stopping...")
#     finally:
#         serial_obj.stop()
#
#
# if __name__ == "__main__":
#     main()