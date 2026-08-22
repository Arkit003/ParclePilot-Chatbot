from __future__ import annotations

from pathlib import Path

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from src.ingestion.document_manifest import (
    DOCUMENT_MANIFEST,
    DocumentMetadata,
    get_document_path,
)


BASE_DIR = Path(__file__).resolve().parents[2]

CHROMA_DIR = BASE_DIR / "data" / "chroma"

COLLECTION_NAME = "parcelpilot_documents"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from all pages of a PDF."""

    reader = PdfReader(str(pdf_path))

    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def normalize_text(text: str) -> str:
    """Normalize extracted PDF text."""

    text = text.replace("\u00a0", " ")

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)


def chunk_text(
    text: str,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[str]:
    """
    Split text into overlapping character chunks.

    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def build_metadata(
    document: DocumentMetadata,
    chunk_index: int,
) -> dict[str, object]:
    """Build Chroma metadata for one chunk."""

    return {
        "document_name": document["filename"],
        "document_type": document["document_type"],
        "status": document["status"],
        "version": document.get("version") or "",
        "effective_date": document["effective_date"],
        "account_id": document.get("account_id") or "",
        "customer_name": document.get("customer_name") or "",
        "chunk_index": chunk_index,
    }


def build_document_chunks(document: DocumentMetadata,) -> tuple[list[str], list[dict[str, object]]]:

    pdf_path = get_document_path(document)

    raw_text = extract_pdf_text(pdf_path)

    if not raw_text.strip():
        raise ValueError(
            f"No text extracted from {pdf_path}"
        )

    text = normalize_text(raw_text)

    chunks = chunk_text(text)

    metadata = [
        build_metadata(
            document,
            index,
        )
        for index in range(len(chunks))
    ]

    return chunks, metadata


def build_doc_index() -> None:
    """Build the ParcelPilot Chroma document index."""

    CHROMA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading embedding model...")

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    print("Opening Chroma...")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    # Rebuild the collection from scratch.
    try:
        client.delete_collection(
            COLLECTION_NAME
        )
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "ParcelPilot document index",
            "embedding_model": EMBEDDING_MODEL,
        },
    )

    total_chunks = 0

    for document in DOCUMENT_MANIFEST:

        print(
            f"Indexing {document['filename']}..."
        )

        chunks, metadatas = build_document_chunks(
            document
        )

        embeddings = model.encode(
            chunks,
            normalize_embeddings=True,
        ).tolist()

        ids = [
            (
                f"{document['filename']}"
                f"::chunk-{index}"
            )
            for index in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        total_chunks += len(chunks)

        print(
            f"  Added {len(chunks)} chunks"
        )

    print(
        f"Index built successfully. "
        f"Total chunks: {total_chunks}"
    )

    print(
        f"Chroma path: {CHROMA_DIR}"
    )


if __name__ == "__main__":
    build_doc_index()