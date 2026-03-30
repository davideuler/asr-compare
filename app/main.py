"""
ASR Multi-Model Comparison Platform
FastAPI main entry point
"""
import os
# ── Mirror & cache env vars — set before ANY model library is imported ──
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN") 
os.environ.setdefault("HF_HOME",          "/mnt/nvme/clawspace/asr-compare/models/hf_cache")
os.environ.setdefault("MODELSCOPE_CACHE", "/mnt/nvme/clawspace/asr-compare/models/ms_cache")

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.transcribe import router as transcribe_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = "/mnt/nvme/clawspace/asr-compare/static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ASR Compare platform starting up...")
    yield
    logger.info("ASR Compare platform shutting down...")


app = FastAPI(
    title="ASR Multi-Model Comparison Platform",
    description="Compare multiple ASR models side by side",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(transcribe_router)

# Static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ASR Compare Platform API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
