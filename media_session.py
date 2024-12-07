import threading
import asyncio
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager

class Media:
    def __init__(self):
        # Initialize session management
        self.session_thread = None
        self.session_timer_interval = 0.5  # Check session every 0.5sec
        self.current_session_flag = False
        self.title = None
        self.artist = None

        # Event to handle stopping
        self.stop_event = threading.Event()

        # Async loop for managing media sessions
        self.session_loop = asyncio.new_event_loop()


        # Start session thread
        self.session_thread = threading.Thread(
            target=self._async_session_thread, daemon=True)
        self.session_thread.start()

    def stop(self):
        """Gracefully stop the media session."""
        self.stop_event.set()

        try:
            # Stop the asyncio loop
            # noinspection PyTypeChecker
            self.session_loop.call_soon_threadsafe(self.session_loop.stop)
        except Exception as e:
            print(f"Error stopping event loop: {e}")

        # Ensure threads stop properly
        self.session_thread.join(timeout=2)

    def _async_session_thread(self):
        """Thread to run the asyncio loop."""
        asyncio.set_event_loop(self.session_loop)
        try:
            self.session_loop.run_until_complete(self._async_session_runner())
        except Exception as e:
            print(f"Error in async session thread: {e}")
        finally:
            try:
                self.session_loop.close()
            except Exception as e:
                print(f"Error closing event loop: {e}")

    async def _async_session_runner(self):
        """Async runner to manage media sessions."""
        while not self.stop_event.is_set():
            try:
                await self._async_session_handler()
                await asyncio.sleep(self.session_timer_interval)
            except Exception as e:
                print(f"Error in async session handler: {e}")
                await asyncio.sleep(0.5)  # Add delay to avoid busy-waiting on errors

    async def _async_session_handler(self):
        """Handle media session updates."""
        try:
            session_manager = await MediaManager.request_async()
            current_session = session_manager.get_current_session()

            if not current_session:
                if self.current_session_flag:
                    print("No current session available")
                    self.current_session_flag = False
                    self.title = None
                    self.artist = None
                return

            media_properties = await current_session.try_get_media_properties_async()

            # Check for updated media session properties
            if media_properties.title != self.title:
                self.title = media_properties.title
                self.artist = media_properties.artist
                self.current_session_flag = True

                print(f"Now Playing: Title: {self.title}, Artist: {self.artist}")

        except Exception as e:
            print(f"Error managing media session: {e}")
            self.current_session_flag = False
            self.title = None
            self.artist = None
