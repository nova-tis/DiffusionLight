from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image, UnidentifiedImageError
import io
import os
from datetime import datetime

app = FastAPI()

# Ensure directories exist
os.makedirs("input-image", exist_ok=True)
os.makedirs("output-image", exist_ok=True)

@app.get("/")
def root():
    return {"message": "Image processing API is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))  # Validate image
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # Unique timestamped name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    clean_filename = file.filename.replace(" ", "_")
    input_path = f"input-image/{timestamp}_{clean_filename}"
    output_path = f"output-image/{timestamp}_{clean_filename}"

    # Save input
    with open(input_path, "wb") as f:
        f.write(contents)

    # Process and save output
    processed_image = image.convert("L")
    processed_image.save(output_path)

    return JSONResponse(content={
        "status": "processed",
        "input": input_path,
        "output": output_path,
        "fetch_url": f"/get-image/{timestamp}_{clean_filename}"
    })

@app.get("/get-image/{filename}")
async def get_image(filename: str):
    path = f"output-image/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Processed image not found")
    return FileResponse(path, media_type="image/png", filename=filename)
