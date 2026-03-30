"""
Transcription API endpoints.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models import MODEL_REGISTRY, MODEL_DISPLAY_NAMES

logger = logging.getLogger(__name__)
router = APIRouter()

# Thread pool for blocking model inference
executor = ThreadPoolExecutor(max_workers=4)

UPLOAD_DIR = "/mnt/nvme/clawspace/asr-compare/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".webm", ".opus"}


def convert_to_wav16k(input_path: str, output_path: str) -> str:
    """Convert any audio file to 16kHz mono WAV using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", "-f", "wav",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")
    return output_path


def run_transcription(model_id: str, wav_path: str) -> dict:
    """Run a single model's transcription synchronously (called in thread pool)."""
    if model_id not in MODEL_REGISTRY:
        return {
            "model_id": model_id,
            "model_name": model_id,
            "text": "",
            "duration_ms": 0,
            "success": False,
            "error": f"Unknown model: {model_id}"
        }
    module = MODEL_REGISTRY[model_id]
    result = module.transcribe(wav_path)
    return {
        "model_id": model_id,
        "model_name": MODEL_DISPLAY_NAMES.get(model_id, model_id),
        **result,
    }


@router.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    models: str = Form(...),  # comma-separated list of model ids
):
    """
    Upload an audio file and transcribe it with selected models in parallel.
    Returns results for each model.
    """
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_FORMATS and ext != "":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {ext}. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Parse selected models
    selected_models = [m.strip() for m in models.split(",") if m.strip()]
    if not selected_models:
        raise HTTPException(status_code=400, detail="No models selected")

    # Save uploaded file
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    original_path = os.path.join(job_dir, f"original{ext or '.audio'}")
    wav_path = os.path.join(job_dir, "audio_16k.wav")

    try:
        with open(original_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Convert to 16kHz mono WAV
        convert_to_wav16k(original_path, wav_path)

        # Run all selected models in parallel using thread pool
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, run_transcription, model_id, wav_path)
            for model_id in selected_models
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Normalize results (handle exceptions)
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "model_id": selected_models[i],
                    "model_name": MODEL_DISPLAY_NAMES.get(selected_models[i], selected_models[i]),
                    "text": "",
                    "duration_ms": 0,
                    "success": False,
                    "error": str(result),
                })
            else:
                final_results.append(result)

        return JSONResponse(content={"results": final_results, "job_id": job_id})

    finally:
        # Cleanup job dir after response (async)
        asyncio.create_task(cleanup_job(job_dir))


async def cleanup_job(job_dir: str):
    """Clean up temporary files after a delay."""
    await asyncio.sleep(300)  # Keep for 5 minutes for debugging
    try:
        shutil.rmtree(job_dir, ignore_errors=True)
    except Exception:
        pass


@router.get("/api/models/status")
async def models_status():
    """Return loading status of all models."""
    status = {}
    for model_id, module in MODEL_REGISTRY.items():
        status[model_id] = {
            "model_id": model_id,
            "model_name": MODEL_DISPLAY_NAMES.get(model_id, model_id),
            "loaded": module.is_loaded(),
        }
    return JSONResponse(content={"models": status})


@router.get("/api/models")
async def list_models():
    """List all available models."""
    models = [
        {
            "id": model_id,
            "name": MODEL_DISPLAY_NAMES.get(model_id, model_id),
            "loaded": MODULE.is_loaded(),
        }
        for model_id, MODULE in MODEL_REGISTRY.items()
    ]
    return JSONResponse(content={"models": models})
