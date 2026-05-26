"""FastAPI app factory. Loads Chroma at startup, mounts API routes + static frontend."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import cases, health, run
from underwriter.rag import load_or_build_store

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = ROOT / "data" / "chroma"
PDF_PATH = ROOT / "data" / "underwriting_policies.pdf"
FRONTEND_DIR = ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()):
        try:
            from langchain_openai import OpenAIEmbeddings

            api_key = os.getenv("OPENAI_API_KEY", "sk-placeholder-for-load-only")
            app.state.vector_store = load_or_build_store(
                chroma_dir=CHROMA_DIR,
                pdf_path=None,
                embedding=OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-small"),  # type: ignore[arg-type]
            )
            logger.info("Chroma store loaded from %s", CHROMA_DIR)
        except Exception:
            logger.exception("Failed to load Chroma store; RAG will be disabled")
            app.state.vector_store = None
    else:
        logger.warning("No Chroma store at %s; RAG disabled", CHROMA_DIR)
        app.state.vector_store = None

    yield


app = FastAPI(
    title="Underwriter Agent",
    version="0.1.0",
    description="Multi-agent mortgage underwriting demo. Bring your own OpenAI key.",
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(run.router, prefix="/api")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
