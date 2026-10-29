#   Copyright 2026 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import uuid
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

import settings


def init_model() -> TextEmbedding:
    print("Initializing components...")
    print(f"Model cache path: {settings.EMBEDDING_MODEL_CACHE_PATH}")
    try:
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL} (offline mode)...")
        model = TextEmbedding(model_name=settings.EMBEDDING_MODEL, cache_dir=settings.EMBEDDING_MODEL_CACHE_PATH)
        print("Model loaded successfully.")
        return model
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}")
        print("Please ensure the model is pre-downloaded or network is available.")
        print("Tip: Run download_model.py in a network-enabled environment first.")
        raise


def init_client() -> QdrantClient:
    print("Connecting to Qdrant...")
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    print("Connected to Qdrant.")
    return client


def chunk_text(text: str):
    chunks = []
    start = 0
    while start < len(text):
        end = start + settings.CHUNK_SIZE
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
    return chunks


def clean_md(text: str) -> str:
    # Markdown files don't need special cleaning like RST
    # Just return the text as-is or add minimal cleaning if needed
    return text


def extract_title(text: str, file: Path) -> str:
    lines = text.split('\n', 1)
    first_line = lines[0].strip() if lines else ""
    # Remove markdown heading markers (# ## ### etc)
    title = first_line.lstrip('#').strip() if first_line else file.stem
    if not title:  # If first line is empty, fallback to filename
        title = file.stem
    return title


def ensure_collection(client: QdrantClient, model: TextEmbedding):
    collections = [c.name for c in client.get_collections().collections]
    if settings.COMMON_COLLECTION_NAME not in collections:
        dim = len(next(model.embed(["test"])))
        client.create_collection(
            collection_name=settings.COMMON_COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )


def make_point_id(rel_path: str, chunk_idx: int) -> str:
    # Deterministic ID keyed on (source, chunk) so re-importing a document
    # overwrites exactly its own points instead of colliding with other
    # files' points.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{rel_path}#{chunk_idx}"))


def build_points_for_file(model: TextEmbedding, base: Path, file: Path):
    rel_path = file.relative_to(base).as_posix()
    raw = file.read_text(encoding="utf-8")
    text = clean_md(raw)
    title = extract_title(text, file)

    chunks = chunk_text(text)
    print(f"  - Title: {title}")
    print(f"  - Created {len(chunks)} chunks")

    print("  - Generating embeddings...")
    # Small batch_size caps the ONNX Runtime memory arena growth: it grows to
    # fit the largest batch ever seen and never shrinks back, so a single file
    # with many chunks would otherwise inflate peak memory for the rest of the run.
    embeddings = list(model.passage_embed(chunks, batch_size=1))

    points = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=make_point_id(rel_path, idx),
                vector=emb.tolist(),
                payload={
                    "source": rel_path,
                    "filename": file.name,
                    "title": title,
                    "directory": file.parent.relative_to(base).as_posix(),
                    "chunk": idx,
                    "text": chunk,
                },
            )
        )
    return rel_path, points


def delete_points_by_source(client: QdrantClient, rel_path: str):
    client.delete(
        collection_name=settings.COMMON_COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=rel_path))]
        ),
    )


def upsert_points(client: QdrantClient, points, batch_size: int = 100):
    if not points:
        return
    print(f"\nUpserting {len(points)} points to Qdrant...")
    # Split into batches to avoid payload size limit (33.5MB)
    total_batches = (len(points) + batch_size - 1) // batch_size
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  - Upserting batch {batch_num}/{total_batches} ({len(batch)} points)...")
        client.upsert(collection_name=settings.COMMON_COLLECTION_NAME, points=batch)
    print("Upsert completed.")


def resolve_relative_path(bases, arg: str) -> tuple[Path, Path]:
    # Resolves arg (absolute, or relative to one of `bases`) to a path under
    # one of `bases`, without requiring the path to exist on disk.
    # Returns the matching base together with the resolved file path.
    path = Path(arg)
    candidates = [path] if path.is_absolute() else [base / path for base in bases]
    for candidate in candidates:
        file = candidate.resolve()
        for base in bases:
            if base.resolve() in file.parents:
                return base, file
    bases_desc = "', '".join(str(base) for base in bases)
    raise ValueError(f"'{arg}' is not located under any document path ('{bases_desc}')")


def resolve_document_path(bases, arg: str) -> tuple[Path, Path]:
    base, file = resolve_relative_path(bases, arg)
    if not file.is_file():
        raise FileNotFoundError(f"'{file}' does not exist")
    return base, file
