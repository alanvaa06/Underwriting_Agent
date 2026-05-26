"""One-shot script: load underwriting_policies.pdf, split, embed, persist to data/chroma/.

Run locally with OPENAI_API_KEY set. The resulting data/chroma/ is committed to the repo
and baked into the Docker image (spec strategy A).

Usage:
    python scripts/build_chroma.py
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "data" / "underwriting_policies.pdf"
CHROMA_DIR = ROOT / "data" / "chroma"


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment.", file=sys.stderr)
        return 1

    if not PDF_PATH.exists():
        print(f"ERROR: {PDF_PATH} not found.", file=sys.stderr)
        return 1

    if CHROMA_DIR.exists():
        print(f"Removing stale {CHROMA_DIR}...")
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading {PDF_PATH}...")
    loader = PyPDFLoader(str(PDF_PATH))
    docs = loader.load()
    print(f"Loaded {len(docs)} pages.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    print("Embedding + persisting to Chroma...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="underwriting_policies",
    )
    print(f"Done. Vector store at {CHROMA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
