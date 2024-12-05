import serial
import serial.tools.list_ports_windows
import asyncio
import logging


class SerialConnection:
    def __init__(self):
        self.COM_PORT = None
        self.BAUD_RATE = 115200
        self.ser = None
        self.connected = False
        self.VALID_COMMANDS = ["PLAY", "SKIP_NEXT", "SKIP_PREV", "MUTE", "VOL"]
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def find_esp32_port(self):
        """Find available ESP32 USB ports."""
        ports = serial.tools.list_ports_windows.comports()
        esp_ports = [port for port, desc, hwid in ports if "USB" in hwid]
        return esp_ports

    async def start_connection(self):
        """Initialize serial connection with error handling and logging."""
        if self.ser and self.ser.is_open:
            self.ser.close()

        esp_ports = await self.find_esp32_port()
        if not esp_ports:
            self.logger.error("No USB devices found")
            self.connected = False
            return False

        for port in esp_ports:
            try:
                self.ser = serial.Serial(
                    port=port,
                    baudrate=self.BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1  # Short timeout for more responsive reading
                )
                self.COM_PORT = port
                self.connected = True
                self.logger.info(f"Connected to ESP32 on {self.COM_PORT}")
                return True
            except serial.SerialException as e:
                self.logger.error(f"Failed to connect to {port}: {str(e)}")
                continue

        self.connected = False
        return False

    async def check_connection(self):
        """Verify connection is alive with timeout."""
        if not self.ser or not self.ser.is_open:
            return False

        try:
            # Clear any existing data
            self.ser.reset_input_buffer()

            # Send heartbeat
            self.ser.write(b'PING\n')

            # Wait for response with timeout
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < 5:  # 5 second timeout
                if self.ser.in_waiting:
                    data = self.ser.readline().decode().strip()
                    if data == "ALIVE":
                        return True
                await asyncio.sleep(0.1)

            self.logger.warning("No response to heartbeat")
            return False

        except serial.SerialException as e:
            self.logger.error(f"Connection check failed: {str(e)}")
            return False

    async def read_serial_data(self):
        """Read and validate serial data with error handling."""
        if not self.ser or not self.ser.is_open:
            return None

        try:
            if self.ser.in_waiting:
                data = self.ser.readline().decode().strip()

                # Validate received command
                for command in self.VALID_COMMANDS:
                    if command in data:
                        self.logger.debug(f"Received valid command: {command}")
                        # print("pyserial: " + str(data))
                        return data

                if data:  # Log invalid commands for debugging
                    self.logger.warning(f"Received invalid command: {data}")

            return None

        except serial.SerialException as e:
            self.logger.error(f"Error reading serial data: {str(e)}")
            self.connected = False
            return None
        except UnicodeDecodeError as e:
            self.logger.error(f"Error decoding serial data: {str(e)}")
            return None

    async def volume_change_accept(self):
        self.ser.write(b"VOL_ACP\n")
