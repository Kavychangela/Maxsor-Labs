import json
import re
from pathlib import Path

import numpy as np
from google import genai

from .config import settings


KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
VECTOR_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "vector_store.json"

EMBEDDING_MODEL = "gemini-embedding-001"


def get_client():
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def load_documents() -> list[dict]:
    """Load all Markdown documents from the knowledge base."""

    documents = []

    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            continue

        documents.append(
            {
                "source": file_path.name,
                "text": text,
            }
        )

    if not documents:
        raise RuntimeError(
            f"No knowledge-base documents found in {KNOWLEDGE_BASE_DIR}"
        )

    return documents


def split_into_chunks(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[str]:
    """
    Split policy text into overlapping chunks.

    We preserve paragraph/numbered-rule boundaries where possible,
    then enforce a character limit.
    """

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip()
    ]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        candidate = (
            paragraph
            if not current
            else f"{current}\n{paragraph}"
        )

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        # If one paragraph is itself too large,
        # split it into smaller pieces.
        if len(paragraph) > chunk_size:
            start = 0

            while start < len(paragraph):
                end = start + chunk_size
                piece = paragraph[start:end].strip()

                if piece:
                    chunks.append(piece)

                start = end - overlap

            current = ""
        else:
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def create_chunks() -> list[dict]:
    """Load documents and split them into chunks."""

    documents = load_documents()

    chunks = []

    chunk_id = 0

    for document in documents:
        document_chunks = split_into_chunks(
            document["text"]
        )

        for chunk in document_chunks:
            chunks.append(
                {
                    "id": chunk_id,
                    "source": document["source"],
                    "text": chunk,
                }
            )

            chunk_id += 1

    return chunks


def embed_text(text: str) -> list[float]:
    """Create an embedding for a piece of text."""

    client = get_client()

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return response.embeddings[0].values


def build_vector_store():
    """
    Create embeddings for all knowledge-base chunks
    and save them locally.
    """

    chunks = create_chunks()

    print(f"Loaded {len(chunks)} chunks.")

    vector_store = []

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"Embedding chunk {index}/{len(chunks)}..."
        )

        embedding = embed_text(
            chunk["text"]
        )

        vector_store.append(
            {
                **chunk,
                "embedding": embedding,
            }
        )

    VECTOR_STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    VECTOR_STORE_PATH.write_text(
        json.dumps(
            vector_store,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Vector store saved to {VECTOR_STORE_PATH}"
    )

    return vector_store


def load_vector_store() -> list[dict]:
    """Load the locally stored vector database."""

    if not VECTOR_STORE_PATH.exists():
        raise RuntimeError(
            "Vector store does not exist. "
            "Run build_vector_store() first."
        )

    return json.loads(
        VECTOR_STORE_PATH.read_text(
            encoding="utf-8"
        )
    )


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """Calculate cosine similarity."""

    a = np.array(vector_a)
    b = np.array(vector_b)

    denominator = (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b) / denominator
    )


def retrieve(
    query: str,
    top_k: int = 4,
) -> list[dict]:
    """
    Embed a query and retrieve the most
    semantically similar knowledge-base chunks.
    """

    vector_store = load_vector_store()

    query_embedding = embed_text(query)

    scored_chunks = []

    for chunk in vector_store:
        score = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        scored_chunks.append(
            {
                "id": chunk["id"],
                "source": chunk["source"],
                "text": chunk["text"],
                "score": score,
            }
        )

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_chunks[:top_k]