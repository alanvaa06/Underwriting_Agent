from pathlib import Path

import pytest
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import Chroma

from underwriter.rag import load_or_build_store, retrieve_policy


@pytest.fixture
def tiny_chroma(tmp_path: Path) -> Chroma:
    return Chroma.from_texts(
        texts=[
            "FICO scores above 700 generally qualify for prime rates.",
            "LTV ratios above 80% require private mortgage insurance.",
            "DTI above 43% disqualifies under qualified mortgage rules.",
        ],
        embedding=FakeEmbeddings(size=128),
        persist_directory=str(tmp_path / "chroma_test"),
        collection_name="test_policies",
    )


def test_retrieve_policy_returns_top_k(tiny_chroma: Chroma):
    docs = retrieve_policy(tiny_chroma, query="What's the LTV cutoff for PMI?", k=2)
    assert len(docs) == 2
    assert all(hasattr(d, "page_content") for d in docs)


def test_load_or_build_returns_existing_when_dir_exists(tmp_path: Path):
    # Build once
    persist_dir = tmp_path / "chroma_existing"
    Chroma.from_texts(
        texts=["seed"],
        embedding=FakeEmbeddings(size=128),
        persist_directory=str(persist_dir),
        collection_name="seed",
    )
    # Load (should not re-embed; the helper takes an embedding fn to use for the load path)
    store = load_or_build_store(
        chroma_dir=persist_dir,
        pdf_path=None,
        embedding=FakeEmbeddings(size=128),
        collection_name="seed",
    )
    assert store is not None


def test_load_or_build_raises_when_no_dir_and_no_pdf(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_or_build_store(
            chroma_dir=tmp_path / "nope",
            pdf_path=None,
            embedding=FakeEmbeddings(size=128),
            collection_name="x",
        )
