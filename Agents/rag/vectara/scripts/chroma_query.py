from __future__ import annotations

import json
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from chroma_support import ChromaSettings, parse_metadata, query_documents

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    query: str = typer.Argument(..., help="Pregunta o texto para buscar"),
    limit: int = typer.Option(3, min=1, help="Número de resultados"),
    metadata: Optional[List[str]] = typer.Option(
        None,
        "--metadata",
        "-m",
        help="Filtro where (clave=valor). Puedes repetir la opción.",
    ),
    raw: bool = typer.Option(False, help="Devuelve JSON en vez de tabla"),
):
    settings = ChromaSettings.from_env()
    where = parse_metadata(metadata)
    documents = query_documents(
        query=query,
        limit=limit,
        metadata=where,
        settings=settings,
    )
    if not documents:
        console.print("[yellow]Sin resultados[/yellow]")
        raise typer.Exit()

    if raw:
        console.print_json(data=json.dumps(documents, ensure_ascii=False))
        raise typer.Exit()

    table = Table(title=f"Resultados para: {query}")
    table.add_column("Score", justify="right")
    table.add_column("Metadata")
    table.add_column("Texto", overflow="fold")

    for item in documents:
        table.add_row(item["score"], item["metadata"], item["text"])

    console.print(table)


if __name__ == "__main__":
    app()
