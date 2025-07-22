from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import io
import base64
import glob
import subprocess
import sys
from datetime import datetime
from PIL import Image, UnidentifiedImageError
import shutil

app = FastAPI()

# Ensure required folders exist
os.makedirs("input-image", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("/data/output", exist_ok=True)
os.makedirs("/data/logs", exist_ok=True)

LOG_PATH = "/data/logs/pipeline.log"

# Logging function
def log(message: str):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{timestamp} {message}"
    print(full_message)
    with open(LOG_PATH, "a") as log_file:
        log_file.write(full_message + "\n")

# Run pipeline
def run_processing_pipeline(input_filename: str) -> str:
    try:
        scripts = [
            [sys.executable, "inpaint.py", "--dataset", "input-image", "--output_dir", "output"],
            [sys.executable, "ball2envmap.py", "--ball_dir", "output/square", "--envmap_dir", "output/envmap"],
            [sys.executable, "exposure2hdr.py", "--input_dir", "output/envmap", "--output_dir", "output/hdr"]
        ]

        for cmd in scripts:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log(f"❌ Error in {cmd[0]}:\n{result.stderr}")
                raise RuntimeError(f"Pipeline failed: {cmd[0]}")
            else:
                log(f"✅ {cmd[0]} completed successfully.")
                log(f"↪ stdout:\n{result.stdout.strip()}")

        log("HDR pipeline completed successfully.")

        # Move HDR files to /data/output
        src_dir = "output/hdr"
        dst_dir = "/data/output"
        os.makedirs(dst_dir, exist_ok=True)

        hdr_path = None
        for filename in os.listdir(src_dir):
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, filename)
            shutil.move(src_path, dst_path)
            log(f"Moved {src_path} → {dst_path}")
            hdr_path = dst_path  # Assume first HDR is result

        if hdr_path is None:
            raise FileNotFoundError("No HDR file produced.")

        return hdr_path

    except Exception as e:
        log(f"Exception during processing: {e}")
        raise

# Upload + process endpoint (blocking)
@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        contents = await file.read()
        Image.open(io.BytesIO(contents))  # Validate it's an image
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    clean_filename = file.filename.replace(" ", "_")
    input_filename = f"{timestamp}_{clean_filename}"
    input_path = f"input-image/{input_filename}"

    # Save image
    with open(input_path, "wb") as f:
        f.write(contents)

    # Clear log
    with open(LOG_PATH, "w") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting job for {input_filename}\n")

    # Run pipeline (blocking)
    try:
        hdr_path = run_processing_pipeline(input_filename)
        with open(hdr_path, "rb") as f:
            hdr_encoded = base64.b64encode(f.read()).decode("utf-8")

        return JSONResponse(content={
            "status": "complete",
            "filename": os.path.basename(hdr_path),
            "hdr_base64": hdr_encoded
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Log file download
@app.get("/logs")
def get_logs():
    if not os.path.exists(LOG_PATH):
        return JSONResponse(content={"log": "No log available."})

    return FileResponse(LOG_PATH, media_type="text/plain", filename="pipeline.log")

# Health + root endpoints
@app.get("/")
def root():
    return {"message": "Image processing API is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}
