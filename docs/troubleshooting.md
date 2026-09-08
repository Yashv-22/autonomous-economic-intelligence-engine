# Troubleshooting Guide

## 1. Common Issues & Solutions

### 1.1 Port Already in Use (Ports 8000, 20128, 3001)
* **Symptom:** `OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`
* **Cause:** A previous instance of the FastAPI server, OmniRoute router, or FreeLLMAPI daemon is still running.
* **Solution:**
  * Find and terminate the process holding the port:
    * **Windows (PowerShell):**
      ```powershell
      Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
      Stop-Process -Id <PID> -Force
      ```
    * **Linux / macOS:**
      ```bash
      lsof -i :8000
      kill -9 <PID>
      ```

### 1.2 Missing API Key or Provider Initialization Error
* **Symptom:** `ValueError: Missing API key for provider: gemini` or `ProviderNotAvailableError`
* **Cause:** `.env` file does not contain a valid key, or the selected provider is not reachable.
* **Solution:**
  * For offline testing without API keys, set `DEFAULT_PROVIDER=mock` in your `.env` file or environment.
  * If using OmniRoute, ensure the OmniRoute daemon is running at `http://127.0.0.1:20128` or verify `OMNIROUTE_BASE_URL`.
  * If using FreeLLMAPI, ensure the FreeLLMAPI daemon is running at `http://127.0.0.1:3001` or verify `FREELLMAPI_BASE_URL`.

### 1.3 SQLite Database Locked / Concurrency Conflicts
* **Symptom:** `sqlite3.OperationalError: database is locked`
* **Cause:** Multiple concurrent worker processes attempting write operations on `intelligence_ledger.db` simultaneously without WAL mode enabled.
* **Solution:**
  * Enable Write-Ahead Logging (WAL) on the SQLite database:
    ```sql
    PRAGMA journal_mode=WAL;
    ```
  * In high-concurrency production deployments, configure `DATABASE_URL` to point to a managed PostgreSQL instance.

### 1.4 Test Suite Import or Discovery Errors
* **Symptom:** Pytest collects duplicate modules from `backups/` or fails with `ModuleNotFoundError`.
* **Cause:** Virtual environment or backup folders being scanned during test discovery.
* **Solution:**
  * Verify that `pytest.ini` exists in the repository root and includes:
    ```ini
    [pytest]
    testpaths = tests
    norecursedirs = backups scratch infrastructure vendor .venv output
    ```
  * Run tests explicitly targeting the `tests/` directory:
    ```bash
    python -m pytest tests/
    ```

### 1.5 Corrupted Document Parsing (PDF / Word)
* **Symptom:** Empty extracted text or `PdfReadError` when ingesting documents.
* **Cause:** The PDF is either password-protected, corrupted, or consists entirely of raster images without embedded OCR text.
* **Solution:**
  * Verify document readability using a standard viewer.
  * For scanned image PDFs, preprocess the document with an OCR tool (such as Tesseract) prior to ingestion.
