import time
import serial
import serial.tools.list_ports_windows
import logging
import threading
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import io
import struct

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

        # Synchronization events and queues
        self.connection_event = threading.Event()
        self.stop_event = threading.Event()

        # Existing threads (connection and read threads)
        self.serial_connection_thread = threading.Thread(
            target=self._start_and_check_conn_thread,
            daemon=True
        )
        self.serial_read_thread = threading.Thread(
            target=self._read_data_thread,
            daemon=True
        )

        # Start all threads
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

    # noinspection PyUnresolvedReferences
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
                self.ser.setRTS(False)
                self.ser.setDTR(False)
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

    @staticmethod
    def create_jpeg_in_memory(image):
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="JPEG", quality=85)
        image_data = image_buffer.getvalue()
        print(f"Generated JPEG image size: {len(image_data)} bytes")
        return image_data

    @staticmethod
    def thumbnail_to_jpg(image: Image, text, subtext):
        # BLUR
        blur = image
        blur = blur.filter(ImageFilter.GaussianBlur(radius=5))
        blur = blur.resize((320, 240))
        enhancer = ImageEnhance.Brightness(blur)
        blur = enhancer.enhance(0.5)

        # IMAGE
        imge = image.resize((140, 140))

        # Create a rounded mask
        rad = 10  # radius for the rounded corners
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)

        # Create an alpha mask for the image with rounded corners
        alpha = Image.new('L', imge.size, 255)  # Start with a fully transparent alpha channel
        w, h = imge.size

        # Paste the circular mask into the four corners
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))  # Top-left corner
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))  # Bottom-left corner
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))  # Top-right corner
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))  # Bottom-right corner

        imge.putalpha(alpha)  # Apply the alpha mask to the image

        # Position the image onto the blurred background
        position = (90, 35)
        blur.paste(imge, position, imge)  # Use the image's alpha channel as a mask

        # FONTS
        i1 = ImageDraw.Draw(blur)
        font = ImageFont.truetype('liberation-serif/LiberationSerif-Regular.ttf', 24)

        # Get the bounding box of the text to center it
        text = text
        bbox = i1.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # Calculate the position to center the text
        x = (blur.width - text_width) // 2
        y = 176  # Position for the text (can adjust as needed)
        i1.text((x, y), text, font=font, fill=(255, 255, 255))

        # AUTHOR, SUBTEXT
        text = subtext
        font = ImageFont.truetype('liberation-serif/LiberationSerif-Regular.ttf',
                                  15)
        bbox = i1.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (blur.width - text_width) // 2
        y = 205  # Position for the text (can adjust as needed)
        i1.text((x, y), text, font=font, fill=(255, 255, 255))

        # blur.show()

        return blur

    def send_image_to_esp32(self, image, text, subtext):
        """
        Send image to ESP32 with more robust communication.
        """
        if not self.connected or not self.ser or not self.ser.is_open:
            self.logger.warning("Serial connection not ready for image sending")
            return

        try:
            # Prepare and send image
            prepared_img = self.thumbnail_to_jpg(image, text, subtext)
            image_data = self.create_jpeg_in_memory(prepared_img)

            # Send image size
            image_size = len(image_data)
            self.ser.write(struct.pack("<I", image_size))
            print(f"Sending image size: {image_size} bytes")

            # Wait for acknowledgment (with timeout)
            start_time = time.time()
            ack_received = False
            while time.time() - start_time < 5:
                if self.ser.in_waiting:
                    ack = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    # print(f"Received acknowledgment: '{ack}'")
                    if "ACK" in ack:
                        ack_received = True
                        break

            if not ack_received:
                print("No acknowledgment received")
                return

            # Send image data
            print("Sending image data...")
            self.ser.write(image_data)

            # Wait for done signal (with timeout)
            done_start_time = time.time()
            done_received = False
            while time.time() - done_start_time < 4:
                if self.ser.in_waiting:
                    done = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    # print(f"Received done signal: '{done}'")
                    if "DONE" in done:
                        done_received = True
                        print("Image sent successfully!")
                        break

            if not done_received:
                print("No 'DONE' signal received")

        except Exception as e:
            self.logger.error(f"Image sending error: {e}")


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