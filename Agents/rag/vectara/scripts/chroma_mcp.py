from pathlib import Path
from typing import Dict, List, Optional, TypedDict

import typer
from mcp.server.fastmcp import FastMCP

from chroma_support import (
    ChromaSettings,
    ingest_document,
    list_local_documents,
    query_documents,
)

mcp = FastMCP(
    name="Chroma Local",
    instructions="Proveedor MCP para ingestar y consultar una colección local en Chroma.",
    json_response=True,
)


class IngestResult(TypedDict):
    document: str
    chunks: int
    path: str


class SearchResult(TypedDict):
    score: str
    metadata: str
    text: str


class DocumentInfo(TypedDict):
    path: str
    size_bytes: str
    modified_at: str


@mcp.tool(description="Ingresa un archivo en la colección local de Chroma")
def chroma_ingest_tool(
    path: str,
    metadata: dict[str, str] = None,
    encoding: str = "utf-8",
) -> IngestResult:
    settings = ChromaSettings.from_env()
    summary = ingest_document(
        Path(path),
        metadata=metadata or {},
        encoding=encoding,
        settings=settings,
    )
    return IngestResult(
        document=str(summary["document"]),
        chunks=int(summary["chunks"]),
        path=str(summary["path"]),
    )


@mcp.tool(description="Busca texto en la colección de Chroma")
def chroma_search_tool(
    query: str,
    limit: int = 3,
    metadata: dict[str, str] = None,
) -> List[SearchResult]:
    settings = ChromaSettings.from_env()
    rows = query_documents(
        query=query,
        limit=limit,
        metadata=metadata or {},
        settings=settings,
    )
    return [
        SearchResult(score=row["score"], metadata=row["metadata"], text=row["text"])
        for row in rows
    ]


@mcp.tool(description="Lista los archivos disponibles en documentacion/")
def chroma_list_documents_tool() -> List[DocumentInfo]:
    settings = ChromaSettings.from_env()
    documents = list_local_documents(settings)
    return [
        DocumentInfo(
            path=item["path"],
            size_bytes=item["size_bytes"],
            modified_at=item["modified_at"],
        )
        for item in documents
    ]


cli = typer.Typer(add_completion=False)


@cli.command()
def main(
    host: Optional[str] = typer.Option(None, help="Host para el modo HTTP"),
    port: Optional[int] = typer.Option(None, help="Puerto para el modo HTTP"),
    stdio: bool = typer.Option(False, help="Ejecuta el servidor en modo STDIO"),
):
    settings = ChromaSettings.from_env()
    resolved_host = host or settings.host
    resolved_port = port or settings.port

    if stdio:
        mcp.run(transport="stdio")
        return

    mcp.settings.host = resolved_host
    mcp.settings.port = resolved_port
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    cli()
