import os
from PIL import Image
import io
from werkzeug.datastructures import FileStorage

def convert_to_webp(file: FileStorage) -> io.BytesIO:
    file.stream.seek(0)
    image = Image.open(file.stream)
    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)
    return output

def resize(file: io.BytesIO, new_witdh: int = 500) -> Image.Image:
    img = Image.open(io.BytesIO(file.read()))
    return img.resize((new_witdh, new_witdh))

# Create a dummy image
img = Image.new('RGB', (100, 100), color = 'red')
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_byte_arr.seek(0)

# Mock FileStorage
file = FileStorage(stream=img_byte_arr, filename="test.jpg", content_type="image/jpeg")

# Test
try:
    img_converted = convert_to_webp(file)
    print(f"img_converted size: {len(img_converted.getvalue())}")
    img_resized = resize(img_converted, 500)
    print(f"img_resized size: {img_resized.size}")
    
    # Save it
    img_resized.save("test_save.webp")
    print(f"Saved size on disk: {os.path.getsize('test_save.webp')}")
except Exception as e:
    print(f"Error: {e}")
