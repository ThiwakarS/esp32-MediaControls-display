import serial
import struct
import time
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import io

SERIAL_PORT = "COM7"  # Replace with your ESP32's port
BAUD_RATE = 115200

def create_jpeg_in_memory(image):
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="JPEG", quality=85)
    image_data = image_buffer.getvalue()
    print(f"Generated JPEG image size: {len(image_data)} bytes")
    return image_data

def send_image_to_esp32(image_data):
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.setRTS(False)
    ser.setDTR(False)
    time.sleep(2)

    # Send image size first
    image_size = len(image_data)
    ser.write(struct.pack("<I", image_size))
    print("Image size sent. Waiting for acknowledgment...")

    # Wait for acknowledgment
    while True:
        try:
            ack = ser.readline().decode().strip()
            if ack == "A":
                print("Acknowledgment received. Sending image data...")
                break

        except:
            pass

    # Send image data
    ser.write(image_data)
    print(f"Image data sent ({image_size} bytes). Waiting for done signal...")

    # Wait for done signal
    while True:
        try:
            done = ser.readline().decode().strip()
            if done == "D":
                print("Image received and displayed successfully!")
                break

        except:
            pass
    ser.close()

# Image processing function (from your original code)
def thumbnail_to_jpg(image: Image, text, subtext):
    # BLUR
    blur = image
    blur = blur.filter(ImageFilter.GaussianBlur(radius=5))
    blur = blur.resize((320, 240))
    enhancer = ImageEnhance.Brightness(blur)
    blur = enhancer.enhance(0.5)

    # IMAGE
    w, h = image.size
    imge = image
    imge.thumbnail((140, 140))

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

# Main execution
img = Image.open('color_test.jpg')
img = img.convert(mode='RGB')  # Ensure RGB mode
# img = img.resize((320, 240))  # Match TFT display dimensions
text1 = "What's My Car Collection"
subtext1 = "Mat Watson Cars"
img = thumbnail_to_jpg(img, text1, subtext1)

# Save as JPEG
image_data = create_jpeg_in_memory(img)
send_image_to_esp32(image_data)