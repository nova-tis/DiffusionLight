from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import io
import base64
import glob
import subprocess
import sys
from datetime import datetime
from PIL import Image, UnidentifiedImageError

app = FastAPI()

# Ensure required folders exist
os.makedirs("input-image", exist_ok=True)
os.makedirs("output", exist_ok=True)

def run_processing_pipeline(input_filename: str):
    try:
        scripts = [
            [sys.executable, "inpaint.py", "--dataset", "input-image", "--output_dir", "output"],
            [sys.executable, "ball2envmap.py", "--ball_dir", "output/square", "--envmap_dir", "output/envmap"],
            [sys.executable, "exposure2hdr.py", "--input_dir", "output/envmap", "--output_dir", "output/hdr"]
        ]
        for cmd in scripts:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error in {cmd[0]}:\n{result.stderr}")
                return
        print("HDR pipeline completed successfully.")
    except Exception as e:
        print(f"Exception during processing: {e}")

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        contents = await file.read()
        Image.open(io.BytesIO(contents))  # Validate image
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    clean_filename = file.filename.replace(" ", "_")
    input_filename = f"{timestamp}_{clean_filename}"
    input_path = f"input-image/{input_filename}"

    # Save image
    with open(input_path, "wb") as f:
        f.write(contents)

    # Kick off processing in background
    background_tasks.add_task(run_processing_pipeline, input_filename)

    return JSONResponse(content={
        "status": "uploaded",
        "input_path": input_path,
        "fetch_url": f"/get-hdr/{input_filename}"
    })

@app.get("/get-hdr/{filename}")
def get_hdr(filename: str):
    expected_hdr_pattern = f"output/hdr/*{filename.split('.')[0]}*.hdr"
    hdr_files = glob.glob(expected_hdr_pattern)

    if not hdr_files:
        return JSONResponse(status_code=202, content={
            "status": "processing",
            "detail": "HDR not yet available. Please check back later.",
            "filename": filename
        })

    hdr_path = hdr_files[0]
    with open(hdr_path, "rb") as f:
        hdr_encoded = base64.b64encode(f.read()).decode("utf-8")

    return JSONResponse(content={
        "status": "complete",
        "filename": os.path.basename(hdr_path),
        "hdr_base64": hdr_encoded
    })

@app.get("/")
def root():
    return {"message": "Image processing API is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}
