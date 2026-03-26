# MCP Local (Chroma)

Guía rápida para clonar y operar el entorno MCP local basado en Chroma.

## 1. Prerrequisitos
- Windows con Python 3.14 (`py -0` para confirmar).
- Git / PowerShell.
- ~500 MB libres para entorno y modelos ONNX.

## 2. Configuración inicial
```powershell
cd C:\Users\leiva.maite\Documents\Proyectos\Experimentales\opencode\rag\vectara
py -3.14 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## 3. Variables de entorno
1. Copia `.env.example` → `.env`.
2. Ajusta solo si necesitas personalizar persistencia/puerto:
   - `CHROMA_PERSIST_DIR`, `CHROMA_COLLECTION`, `CHROMA_EMBED_MODEL`.
- `CHROMA_CHUNK_SIZE` / `CHROMA_CHUNK_OVERLAP`.
- `CHROMA_BATCH_SIZE`: cantidad de registros por batch al agregar en Chroma (bajalo si el PDF es muy grande).
- `CHROMA_DEFAULT_METADATA` (JSON con metadata fija para cada chunk).

## 4. Carpetas
- `documentacion/`: archivos a indexar (PDF, Markdown, TXT).
- `data/chroma/`: almacenamiento del vector store (no borrar salvo reset).

## 5. Ingesta
```powershell
python scripts/chroma_ingest.py "documentacion/Manual de Marca.pdf" --metadata proyecto=documentacion
```
- Usa comillas si hay espacios.
- `--metadata` acepta pares `clave=valor` (puedes repetir el flag).
- `--encoding` para archivos no UTF-8.

## 6. Query
```powershell
python scripts/chroma_query.py "¿Cuál es el mensaje principal del manual?" --limit 3
```
- Muestra score, documento, chunk y texto.
- La primera consulta descarga el modelo de embeddings.

## 7. Servidor MCP
- **Servicio persistente**:
  ```powershell
  powershell -File scripts/start_chroma_mcp.ps1
  ```
  - Usa `CHROMA_HOST` / `CHROMA_PORT` del `.env` (default `0.0.0.0:8050`).
  - Scripts complementarios: `scripts/stop_chroma_mcp.ps1`, `scripts/status_chroma_mcp.ps1`.
- **STDIO (Claude Desktop / otros clientes)**:
  ```powershell
  python scripts/chroma_mcp.py --stdio
  ```
- **HTTP manual**:
  ```powershell
  python scripts/chroma_mcp.py --host 127.0.0.1 --port 8050
  ```

### Claude Desktop
1. Abre `claude_desktop_config.json` local.
2. Añade el bloque de `config/claude-mcp.json`.
3. Reinicia o recarga el cliente.
4. Activa las herramientas `chroma_ingest`, `chroma_search`, `chroma_list_documents`.

## 8. Flujo sugerido
1. Copia nuevos archivos a `documentacion/`.
2. Ejecuta `python scripts/chroma_ingest.py` con metadata.
3. Verifica con `python scripts/chroma_query.py` o desde Claude (`chroma_search`).
4. Mantén `python scripts/chroma_mcp.py --host 127.0.0.1 --port 8050` en segundo plano si expones HTTP.

## 9. Troubleshooting
- Advertencia Pydantic V1: proviene de LangChain, puede ignorarse.
- Advertencia HuggingFace symlinks: requiere Developer Mode; si no, usa más disco.
- PDF sin texto: realiza OCR antes de ingestar.
- Borrar corpus: elimina `data/chroma/` y vuelve a ingestar.
- Limpiar modelos: borra `%USERPROFILE%\.cache\chroma`.

## 10. Próximos pasos
- Automatizar ingestas programadas.
- Filtrar por metadata en `chroma_query.py` (argumentos `--metadata` futuros).
- Evaluar embeddings superiores (`all-mpnet-base-v2`) si el hardware lo permite.
