# Replicar MCP Local (Chroma)

## 1. Prerrequisitos
- Windows con Python 3.14 instalado (`py -0` para verificar).
- Git/PowerShell o terminal equivalente.
- Espacio en disco suficiente (~500 MB para entorno + modelos).

## 2. Clonar/copiar el proyecto
1. Usa la carpeta base `C:\Users\leiva.maite\Documents\Proyectos\Experimentales\opencode\rag\vectara` (ya creada aquí).
2. Si lo necesitas en otro equipo, copia este repositorio y conserva la estructura dentro de la misma ruta relativa (`...\opencode\rag\vectara`).

## 3. Preparar virtualenv
```powershell
cd C:\Users\leiva.maite\Documents\Proyectos\Experimentales\opencode\rag\vectara
py -3.14 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## 4. Configurar variables (.env)
1. Copia `.env.example` → `.env`.
2. Ajusta sólo si necesitas cambios:
   - `CHROMA_PERSIST_DIR`: carpeta para embeddings (default `data/chroma`).
   - `CHROMA_COLLECTION`: nombre de la colección.
   - `CHROMA_EMBED_MODEL`: modelo de embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
   - `CHROMA_CHUNK_SIZE` / `CHROMA_CHUNK_OVERLAP` si quieres otros tamaños.
   - `CHROMA_DEFAULT_METADATA` con metadata fija (JSON) opcional.

## 5. Estructura de carpetas
- `documentacion/`: coloca aquí todos los archivos que quieras indexar (PDF, Markdown, TXT).
- `data/chroma/`: generado automáticamente; no lo borres salvo que quieras reiniciar el corpus.

## 6. Ingestar documentos
```powershell
python scripts/chroma_ingest.py "documentacion/Manual de Marca.pdf" --metadata proyecto=documentacion
```
- Usa comillas si la ruta tiene espacios.
- `--metadata` acepta pares `clave=valor`. Puedes pasar varios.
- `--encoding` para archivos no UTF-8.

## 7. Consultar el corpus
```powershell
python scripts/chroma_query.py "¿Cuál es el mensaje principal del manual?" --limit 3
```
- Muestra score, documento, chunk y texto.
- Primer query descarga el modelo ONNX (puede tardar ~1 min.).

## 8. Levantar el MCP local
- **PowerShell (servicio persistente)**:
  ```powershell
  powershell -File scripts/start_chroma_mcp.ps1
  ```
  - Usa `CHROMA_HOST`/`CHROMA_PORT` definidos en `.env` (por defecto `0.0.0.0:8050` para disponibilidad global).
  - Complementos: `scripts/stop_chroma_mcp.ps1`, `scripts/status_chroma_mcp.ps1`.
- **STDIO (Claude Desktop / otros clientes)**:
  ```powershell
  python scripts/chroma_mcp.py --stdio
  ```
- **Manual HTTP** (si prefieres lanzarlo sin el script):
  ```powershell
  python scripts/chroma_mcp.py --host 127.0.0.1 --port 8050
  ```

### Configurar Claude Desktop
1. Abre `claude_desktop_config.json`.
2. Añade el bloque de `config/claude-mcp.json`:
   ```json
   {
     "mcpServers": {
       "Chroma": {
         "command": "python",
         "args": ["scripts/chroma_mcp.py", "--stdio"]
       }
     }
   }
   ```
3. Reinicia Claude Desktop o usa la opción de recargar.
4. Desde la UI, selecciona las herramientas `chroma_ingest`, `chroma_search` o `chroma_list_documents`.

## 9. Workflow diario sugerido
1. Copia nuevos archivos a `documentacion/`.
2. Ejecuta `python scripts/chroma_ingest.py ...` con la metadata correspondiente.
3. Verifica con `python scripts/chroma_query.py ...` o desde Claude (`chroma_search`).
4. Si necesitas exponer el servidor a otros agentes, mantén `python scripts/chroma_mcp.py --host 127.0.0.1 --port 8050` ejecutándose en segundo plano.

## 10. Troubleshooting
- **Advertencia de Pydantic V1**: ignorable; proviene de LangChain en Python 3.14.
- **Advertencia HuggingFace symlinks**: habilita Developer Mode o ignora (sólo usa más disco).
- **PDF sin texto**: conviértelo a texto (OCR) antes de ingestar.
- **Borrar corpus**: elimina `data/chroma/` y vuelve a ingestar.
- **Limpiar modelos**: borra `%USERPROFILE%\.cache\chroma` si necesitas espacio.

## 11. Registro en Obsidian
- Usa la carpeta `Proyectos/Tecnologia/MCP Local/` del vault para documentar sesiones y notas.
- Cada intervención importante debería reflejarse en `Sesiones.md` y `Nota-Memoria - MCP Local.md`.

## 12. Próximas mejoras recomendadas
- Automatizar la ingesta periódica de `documentacion/` (tarea programada).
- Implementar filtros por metadata en `chroma_query.py`.
- Evaluar modelos de embeddings más robustos si el hardware lo permite (`all-mpnet-base-v2`).
