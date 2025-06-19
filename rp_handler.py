import runpod
import time
import base64
import os
import subprocess
from io import BytesIO
from PIL import Image
from datetime import datetime
import glob

def handler(event):
    print("Worker Start")
    input = event['input']
    
    image_b64 = input.get('image_base64')
    seconds = input.get('seconds', 0)

    if not image_b64:
        return {"error": "No image_base64 field found in input."}

    try:
        # Decode and save input image
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        input_dir = "input-image"
        os.makedirs(input_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{input_dir}/image_{timestamp}.{image.format.lower()}"
        image.save(filename)
        print(f"Image saved to {filename}")

        print(f"Sleeping for {seconds} seconds...")
        time.sleep(seconds)

        # Run processing scripts
        scripts = [
            ["python3", "inpaint.py", "--dataset", "input-image", "--output_dir", "output"],
            ["python3", "ball2envmap.py", "--ball_dir", "output/square", "--envmap_dir", "output/envmap"],
            ["python3", "exposure2hdr.py", "--input_dir", "output/envmap", "--output_dir", "output/hdr"]
        ]

        for cmd in scripts:
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "error": f"Script {' '.join(cmd)} failed",
                    "stderr": result.stderr,
                    "stdout": result.stdout
                }
            print(f"{' '.join(cmd)} completed successfully.")

        # Find the HDR file in output/hdr
        hdr_files = glob.glob("output/hdr/*.hdr")
        if not hdr_files:
            return {"error": "No HDR file found in output/hdr directory."}

        hdr_path = hdr_files[0]  # Assuming there's only one or you want the first one

        # Encode HDR file to base64
        with open(hdr_path, "rb") as f:
            hdr_encoded = base64.b64encode(f.read()).decode('utf-8')

        return {
            "status": "success",
            "file_saved": filename,
            "format": image.format,
            "size": image.size,
            "hdr_base64": hdr_encoded
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    runpod.serverless.start({'handler': handler})
