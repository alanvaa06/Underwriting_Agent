"""Chroma load/build + policy retrieval. Used by agents that need policy context."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from langchain_community.vectorstores import Chroma

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings


def load_or_build_store(
    *,
    chroma_dir: Path,
    pdf_path: Path | None,
    embedding: Embeddings,
    collection_name: str = "underwriting_policies",
) -> Chroma:
    """Load existing Chroma at chroma_dir, else build from pdf_path.

    Raises FileNotFoundError if neither path is usable.
    """
    if chroma_dir.exists() and any(chroma_dir.iterdir()):
        return Chroma(
            persist_directory=str(chroma_dir),
            embedding_function=embedding,
            collection_name=collection_name,
        )

    if pdf_path is None or not pdf_path.exists():
        raise FileNotFoundError(
            f"No existing Chroma at {chroma_dir} and no PDF at {pdf_path}. "
            "Run scripts/build_chroma.py to build the vector store."
        )

    # Defer heavy imports until build path is actually needed
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=str(chroma_dir),
        collection_name=collection_name,
    )


def retrieve_policy(store: Chroma, query: str, *, k: int = 4) -> list[Document]:
    """Return top-k policy chunks most similar to query."""
    return store.similarity_search(query, k=k)
