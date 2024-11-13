import asyncio
from io import BytesIO
from PIL import Image  # To display thumbnail image
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions


async def get_media_info():
    # Get the media session manager
    session_manager = await MediaManager.request_async()
    current_session = session_manager.get_current_session()

    if not current_session:
        print("No media is currently playing.")
        return

    # Get media properties
    media_properties = await current_session.try_get_media_properties_async()
    media_info = {song_attr: media_properties.__getattribute__(song_attr)
              for song_attr in dir(media_properties) if song_attr[0] != '_'}

    print(media_info)

    title = media_info['title']
    artist = media_info['artist']
    album_title = media_info['album_title']

    # Print media info
    print(f"Title: {title}")
    print(f"Artist: {artist}")
    print(f"Album: {album_title}")

    # Get thumbnail image
    if media_info.get('thumbnail'):
        thumb_stream_ref = media_info['thumbnail']
        thumb_read_buffer = Buffer(5000000)

        readable_stream = await thumb_stream_ref.open_read_async()
        readable_stream.read_async(thumb_read_buffer, thumb_read_buffer.capacity, InputStreamOptions.READ_AHEAD)

        buffer_reader = DataReader.from_buffer(thumb_read_buffer)
        byte_buffer = buffer_reader.read_bytes(thumb_read_buffer.length)

        binary = BytesIO()
        binary.write(bytearray(byte_buffer))
        binary.seek(0)

        img = Image.open(binary)
        img.show()
    # else:
    #     print("No thumbnail available.")


# Run the async function
asyncio.run(get_media_info())
