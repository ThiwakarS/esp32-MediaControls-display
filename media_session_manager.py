import asyncio
from io import BytesIO

import keyboard_event  # For listening to keyboard events
import pyserial
from PIL import Image
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions


class Media:
    def __init__(self):
        self.session_timer_running = False  # Flag to manage the session timer
        self.session_timer_interval = 1  # Interval to check for new media\
        self.current_session_flg = False
        self.current_media_title = None  # Store the current media title
        self.current_media_thumbnail = None  # Store the current thumbnail
        self.keyboard_handler = keyboard_event.KeyboardHandler()  # Controller for keyboard
        self.serial_handler = pyserial.SerialConnection()

    ######### SESSION HANDLERS #########
    async def session_timer_start(self):
        """Starts a timer to periodically check for active media sessions."""
        self.session_timer_running = True
        print("Session timer started")
        while self.session_timer_running:
            await self.session_handler()
            await asyncio.sleep(self.session_timer_interval)

    async def load_thumbnail(self, thumb_stream_ref):
        """Loads and displays the media thumbnail."""
        try:
            thumb_read_buffer = Buffer(5000000)  # Allocate buffer for thumbnail
            readable_stream = await thumb_stream_ref.open_read_async()  # Open thumbnail stream

            # Read the stream data into the buffer
            await readable_stream.read_async(
                thumb_read_buffer,
                thumb_read_buffer.capacity,
                InputStreamOptions.READ_AHEAD
            )

            # Convert buffer data into an image
            buffer_reader = DataReader.from_buffer(thumb_read_buffer)
            byte_buffer = buffer_reader.read_bytes(thumb_read_buffer.length)
            binary = BytesIO(bytearray(byte_buffer))
            img = Image.open(binary)

            self.current_media_thumbnail = img  # Update the current thumbnail
            #  img.show()  # Display the thumbnail

            # Clean up resources
            binary.close()
            readable_stream.close()
            return True
        except Exception as e:
            print(f"Failed to load thumbnail: {str(e)}")
            return False

    async def session_handler(self):
        """Handles active media sessions and processes media properties."""
        try:
            # Get the media session manager
            session_manager = await MediaManager.request_async()
            current_session = session_manager.get_current_session()

            # Check if a session is active
            if not current_session:
                print("No current session available")
                self.current_media_title = None
                self.current_media_thumbnail = None
                if self.current_session_flg:
                    self.current_session_flg = False
                return

            # Retrieve media properties
            media_properties = await current_session.try_get_media_properties_async()

            # Check for a new media session
            self.current_session_flg = True
            if media_properties.title != self.current_media_title:
                self.current_media_title = media_properties.title
                title = media_properties.title
                artist = media_properties.artist

                print(f"Title: {title}, Artist: {artist}")

                # Load and display thumbnail if available
                if media_properties.thumbnail:
                    success = await self.load_thumbnail(media_properties.thumbnail)
                    if not success:
                        print("Failed to process thumbnail")
                else:
                    print("No thumbnail available")

        except Exception as e:
            print(f"Error in session handler: {str(e)}")
            self.current_media_title = None

    ######### SERIAL HANDLERS #########
    # async def serial_init(self):
    #     await self.serial_handler.start_connection()
    #
    #     while True:
    #         if not self.serial_handler.ser or not (
    #             await self.serial_handler.check_connection()):
    #
    #             await self.serial_handler.start_connection()
    #
    #
    # async def serial_reader(self):
    #     while True:
    #         data = await self.serial_handler.read_serial_data()
    #
    #         if not data:
    #             continue
    #
    #         if data == "PLAY":
    #             self.keyboard_handler.press_key(
    #                 keyboard_event.keyboard.Key.media_play_pause)
    #
    #         elif data == "SKIP_NEXT":
    #             self.keyboard_handler.press_key(
    #                 keyboard_event.keyboard.Key.media_next)
    #
    #         elif data == "SKIP_PREV":
    #             self.keyboard_handler.press_key(
    #                 keyboard_event.keyboard.Key.media_previous)
    #
    #         elif data == "MUTE":
    #             self.keyboard_handler.press_key(
    #                 keyboard_event.keyboard.Key.media_volume_mute)
    #
    #         elif data == "VOL_UP":
    #             for i in range(5):
    #                 self.keyboard_handler.press_key(
    #                     keyboard_event.keyboard.Key.media_volume_up)
    #
    #         elif data == "VOL_DOWN":
    #             for i in range(5):
    #                 self.keyboard_handler.press_key(
    #                     keyboard_event.keyboard.Key.media_volume_down)
    #
    #         await asyncio.sleep(0.1)

    async def serial_init(self):
        while True:
            if not self.serial_handler.connected:
                success = await self.serial_handler.start_connection()
                if success:
                    # Initial connection check
                    if not await self.serial_handler.check_connection():
                        self.serial_handler.connected = False
            await asyncio.sleep(1)  # Check connection every second

    async def serial_reader(self):
        while True:
            if self.serial_handler.connected:
                data = await self.serial_handler.read_serial_data()
                if data:
                    await self.handle_command(data)
            await asyncio.sleep(0.1)

    async def handle_command(self, data):
        command_map = {
            "PLAY": keyboard_event.keyboard.Key.media_play_pause,
            "SKIP_NEXT": keyboard_event.keyboard.Key.media_next,
            "SKIP_PREV": keyboard_event.keyboard.Key.media_previous,
            "MUTE": keyboard_event.keyboard.Key.media_volume_mute,
            "VOL_UP": keyboard_event.keyboard.Key.media_volume_up,
            "VOL_DOWN": keyboard_event.keyboard.Key.media_volume_down
        }

        if data in command_map:
            key = command_map[data]
            if data in ("VOL_UP", "VOL_DOWN"):
                for _ in range(5):
                    self.keyboard_handler.press_key(key)
            else:
                self.keyboard_handler.press_key(key)

    ######### KEYBOARD HANDLERS #########
    async def keyboard_init(self):
        self.keyboard_handler.key_listener.start()


async def main():
    """Entry point to initialize and run the media session timer."""
    media_obj = Media()
    timer_task = asyncio.create_task(media_obj.session_timer_start())
    keyboard_init = asyncio.create_task(media_obj.keyboard_init())
    serial_init = asyncio.create_task(media_obj.serial_init())
    serial_reader = asyncio.create_task(media_obj.serial_reader())
    try:
        await timer_task
        await keyboard_init
        await serial_init
        await serial_reader
    except asyncio.CancelledError:
        media_obj.session_timer_running = False  # Stop the session timer
    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
