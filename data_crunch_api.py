# main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image
import io

app = FastAPI()

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))

    # === Your image processing script here ===
    processed_image = image.convert("L")  # Example: grayscale conversion

    # Save to buffer
    buf = io.BytesIO()
    processed_image.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")
