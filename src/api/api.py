from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
import cv2
from openvino.runtime import Core
import time
import os
import psutil

START_TIME = time.time()
# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "..", "model")

MODEL_XML = os.path.join(MODEL_DIR, "ghostnet_nsfw.xml")
MODEL_BIN = os.path.join(MODEL_DIR, "ghostnet_nsfw.bin")

IMG_SIZE = 160
CLASS_NAMES = ["drawing", "hentai", "neutral", "porn", "sexy"]

# =========================
# Load OpenVINO Model
# =========================
core = Core()
model = core.read_model(model=MODEL_XML, weights=MODEL_BIN)
compiled_model = core.compile_model(model=model, device_name="CPU")
input_layer = compiled_model.input(0)
output_layer = compiled_model.output(0)

# =========================
# FastAPI init
# =========================
app = FastAPI(
    title="GhostNet NSFW Detection API",
    description="NSFW Detection API using GhostNet + OpenVINO",
    version="1.0"
)

# =========================
# Utils
# =========================
def preprocess_image(image_bytes):
    img = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))  # HWC → CHW
    img = np.expand_dims(img, axis=0)   # BCHW
    return img


def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum(axis=-1, keepdims=True)

# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "message": "GhostNet NSFW API is running",
        "model": "GhostNet + OpenVINO",
        "status": "ok"
    }


@app.get("/status")
def health():
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)  # MB
    uptime = time.time() - START_TIME

    return {
        "service": "ghostnet-nsfw-api",
        "model": "ghostnet",
        "runtime": "openvino",
        "device": "CPU",
        "img_size": IMG_SIZE,
        "classes": CLASS_NAMES,
        "uptime_sec": round(uptime, 2),
        "memory_mb": round(mem, 2),
        "model_path": MODEL_XML,
        "status": "running"
    }


@app.post("/predict")
async def predict_nsfw(file: UploadFile = File(...)):
    start_time = time.time()

    image_bytes = await file.read()

    try:
        input_tensor = preprocess_image(image_bytes)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid image", "detail": str(e)}
        )

    # OpenVINO inference
    result = compiled_model([input_tensor])[output_layer]
    probs = softmax(result[0])

    pred_idx = int(np.argmax(probs))
    pred_label = CLASS_NAMES[pred_idx]
    confidence = float(probs[pred_idx])

    latency = round((time.time() - start_time) * 1000, 2)

    response = {
        "model": "ghostnet",
        "prediksi": pred_label,
        "skor_confidence": round(confidence, 4),
        "waktu_komputasi": str(latency) + " ms",
        "skor_confidence_semua": {
            CLASS_NAMES[i]: float(probs[i]) for i in range(len(CLASS_NAMES))
        }
    }

    return JSONResponse(content=response)


# =========================
# Run server
# =========================
if __name__ == "__main__":
    uvicorn.run("api_ghostnet:app", host="0.0.0.0", port=8000, reload=True)
