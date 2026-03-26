"""Funciones compartidas para el stack MCP/Chroma."""

from __future__ import annotations

import json
import os
import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaDBSettings
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from rich.console import Console

load_dotenv()

console = Console()


@dataclass
class ChromaSettings:
    persist_dir: Path
    collection: str
    embed_model: str
    chunk_size: int
    chunk_overlap: int
    batch_size: int
    default_metadata: Dict[str, str]
    host: str
    port: int
    document_root: Path

    @classmethod
    def from_env(cls) -> "ChromaSettings":
        raw_default = os.getenv("CHROMA_DEFAULT_METADATA", "{}")
        try:
            default_metadata = json.loads(raw_default) if raw_default else {}
            if not isinstance(default_metadata, dict):
                raise ValueError("metadata debe ser dict")
        except Exception:
            console.print(
                "[yellow]CHROMA_DEFAULT_METADATA inválido; usando {} por defecto[/yellow]"
            )
            default_metadata = {}

        return cls(
            persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", "data/chroma")),
            collection=os.getenv("CHROMA_COLLECTION", "documentacion"),
            embed_model=os.getenv(
                "CHROMA_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            chunk_size=int(os.getenv("CHROMA_CHUNK_SIZE", "750")),
            chunk_overlap=int(os.getenv("CHROMA_CHUNK_OVERLAP", "150")),
            batch_size=int(os.getenv("CHROMA_BATCH_SIZE", "512")),
            default_metadata=default_metadata,
            host=os.getenv("CHROMA_HOST", "0.0.0.0"),
            port=int(os.getenv("CHROMA_PORT", "8050")),
            document_root=Path(os.getenv("DOCUMENT_ROOT", "documentacion")),
        )


def ensure_directories(settings: ChromaSettings) -> None:
    settings.persist_dir.mkdir(parents=True, exist_ok=True)
    settings.document_root.mkdir(parents=True, exist_ok=True)


def build_collection(settings: ChromaSettings) -> Collection:
    ensure_directories(settings)
    client = chromadb.PersistentClient(
        settings=ChromaDBSettings(
            persist_directory=str(settings.persist_dir),
        )
    )
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name=settings.embed_model
    )
    return client.get_or_create_collection(
        name=settings.collection,
        embedding_function=embedding_function,
    )


def read_document(path: Path, encoding: str = "utf-8") -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise ValueError("El PDF no contiene texto extraíble. Usa OCR antes de ingestar.")
        return text
    return path.read_text(encoding=encoding)


def split_text(text: str, settings: ChromaSettings) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]


def resolve_document_path(target: Path, settings: ChromaSettings) -> Path:
    if target.exists():
        return target.resolve()
    candidate = settings.document_root / target
    if candidate.exists():
        return candidate.resolve()
    raise FileNotFoundError(f"No encuentro el archivo {target} ni en {settings.document_root}")


def parse_metadata(pairs: Optional[Iterable[str]]) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    if not pairs:
        return metadata
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"El metadata '{item}' debe tener formato clave=valor")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("La clave de metadata no puede estar vacía")
        metadata[key] = value
    return metadata


def make_chunk_ids(prefix: str, total: int) -> List[str]:
    token = secrets.token_hex(4)
    slug = slugify(prefix)
    return [f"{slug}-{token}-{idx}" for idx in range(total)]


def slugify(value: str) -> str:
    valid = string.ascii_lowercase + string.digits + "-"
    normalized = value.lower().replace(" ", "-")
    return "".join(ch if ch in valid else "-" for ch in normalized).strip("-") or "doc"


def base_metadata(path: Path) -> Dict[str, str]:
    return {
        "source": str(path),
        "filename": path.name,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def merge_metadata(*dicts: Dict[str, str]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for data in dicts:
        merged.update({k: str(v) for k, v in data.items()})
    return merged


def format_documents(result: Dict[str, List[List[str]]], limit: int) -> List[Dict[str, str]]:
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    output: List[Dict[str, str]] = []
    for idx in range(min(limit, len(documents))):
        output.append(
            {
                "score": f"{distances[idx]:.4f}" if idx < len(distances) else "",
                "metadata": json.dumps(metadatas[idx], ensure_ascii=False),
                "text": documents[idx],
            }
        )
    return output


def ingest_document(
    file: Path,
    metadata: Dict[str, str] | None = None,
    *,
    encoding: str = "utf-8",
    settings: Optional[ChromaSettings] = None,
) -> Dict[str, str | int]:
    settings = settings or ChromaSettings.from_env()
    target = resolve_document_path(file, settings)
    text = read_document(target, encoding)
    chunks = split_text(text, settings)
    if not chunks:
        raise ValueError("El documento no generó chunks")

    collection = build_collection(settings)
    ids = make_chunk_ids(target.stem, len(chunks))
    metadata = metadata or {}
    payload_metadata = []
    for idx in range(len(chunks)):
        payload_metadata.append(
            merge_metadata(
                settings.default_metadata,
                base_metadata(target),
                metadata,
                {"chunk_index": idx},
            )
        )

    batch_size = max(1, settings.batch_size)
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            documents=chunks[start:end],
            metadatas=payload_metadata[start:end],
            ids=ids[start:end],
        )
    return {
        "document": target.name,
        "chunks": len(chunks),
        "path": str(target),
    }


def query_documents(
    query: str,
    limit: int,
    metadata: Dict[str, str] | None = None,
    *,
    settings: Optional[ChromaSettings] = None,
) -> List[Dict[str, str]]:
    settings = settings or ChromaSettings.from_env()
    collection = build_collection(settings)
    result = collection.query(
        query_texts=[query],
        n_results=limit,
        where=metadata or None,
        include=["documents", "metadatas", "distances"],
    )
    return format_documents(result, limit)


def list_local_documents(settings: Optional[ChromaSettings] = None) -> List[Dict[str, str]]:
    settings = settings or ChromaSettings.from_env()
    ensure_directories(settings)
    documents: List[Dict[str, str]] = []
    root = settings.document_root
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        stats = path.stat()
        documents.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": str(stats.st_size),
                "modified_at": datetime.fromtimestamp(stats.st_mtime, timezone.utc).isoformat(),
            }
        )
    return documents
