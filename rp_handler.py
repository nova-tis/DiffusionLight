import runpod
import time
import base64
import os
from io import BytesIO
from PIL import Image
from datetime import datetime

def handler(event):
    print("Worker Start")
    input = event['input']
    
    image_b64 = input.get('image_base64')
    seconds = input.get('seconds', 0)

    if not image_b64:
        return {"error": "No image_base64 field found in input."}

    try:
        # Decode image
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        # Ensure output directory exists
        output_dir = "input-image"
        os.makedirs(output_dir, exist_ok=True)

        # Generate a unique filename using timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"input-image/image_{timestamp}.{image.format.lower()}"

        # Save image
        image.save(filename)
        print(f"Image saved to {filename}")

        print(f"Sleeping for {seconds} seconds...")
        time.sleep(seconds)

        return {
            "status": "success",
            "file_saved": filename,
            "format": image.format,
            "size": image.size
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    runpod.serverless.start({'handler': handler})
