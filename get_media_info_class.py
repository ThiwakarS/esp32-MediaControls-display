import asyncio
from io import BytesIO
from PIL import Image
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions


class Media:
    def __init__(self):
        self.session_timer_running = False  # Flag to manage the session timer
        self.session_timer_interval = 1  # Interval to check for new media
        self.current_media_title = None  # Store the current media title
        self.current_media_thumbnail = None  # Store the current thumbnail

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
            img.show()  # Display the thumbnail

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
                return

            # Retrieve media properties
            media_properties = await current_session.try_get_media_properties_async()

            # Check for a new media session
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

async def main():
    """Entry point to initialize and run the media session timer."""
    media_obj = Media()
    timer_task = asyncio.create_task(media_obj.session_timer_start())
    try:
        await timer_task
    except asyncio.CancelledError:
        media_obj.session_timer_running = False  # Stop the session timer
    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
