import base64
from io import BytesIO

def sanitize_image(img):
    # If the image is base64
    if isinstance(img, str) and "base64," in img:
        image_stream = base64_to_image(img)
    else:
        # If it's a file path
        image_stream = img
    return image_stream

def base64_to_image(base64_string):
    try:
        # Remove header if present
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
        
        # Convert base64 to bytes
        image_data = base64.b64decode(base64_string)
        
        # Create BytesIO object
        image_stream = BytesIO(image_data)
        return image_stream
    except Exception as e:
        print(f"Error converting base64 to image: {e}")
        return None
 