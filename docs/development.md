# Developer Guide & Local Workflow

## 1. Prerequisites

* **Python:** 3.11+ (Python 3.12 recommended)
* **Operating System:** Windows 10/11, macOS, or Linux (Ubuntu 22.04+ / Debian 12+)
* **Git:** 2.30+
* **Node.js (Optional):** Required only if managing external infrastructure frontends or local FreeLLMAPI/OmniRoute tooling.

---

## 2. Environment Setup

### 2.1 Clone the Repository
```bash
git clone https://github.com/Yashv-22/autonomous-economic-intelligence-engine.git
cd autonomous-economic-intelligence-engine
```

### 2.2 Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 Configure Environment Variables
Copy the sanitized environment template:
```bash
cp .env.example .env
```
Edit `.env` to configure your preferred model gateway and credentials:
* Set `DEFAULT_PROVIDER=mock` for offline local testing with no external API calls.
* Set `GEMINI_API_KEY` or `OPENAI_API_KEY` if testing frontier providers directly.
* Configure `OMNIROUTE_BASE_URL=http://localhost:20128` if running the OmniRoute router locally.
* Configure `FREELLMAPI_BASE_URL=http://localhost:3001/v1` if running FreeLLMAPI locally.

---

## 3. Running the Test Suite

The test suite uses `pytest` and does not require external network access or paid API keys when running standard suites (all external calls are mocked or routed through deterministic baselines).

### Run Full Test Suite
```bash
python -m pytest tests/
```

### Run With Detailed Verbosity
```bash
python -m pytest -v tests/
```

### Run a Specific Test Module
```bash
python -m pytest tests/test_opportunity_engine.py
python -m pytest tests/test_gateway.py
python -m pytest tests/test_omniroute_provider.py
```

---

## 4. Running the Application Locally

### 4.1 Launch the FastAPI Engine Server
```bash
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to:
* **Interactive Dashboard:** `http://127.0.0.1:8000/`
* **Swagger API Docs:** `http://127.0.0.1:8000/docs`
* **System Status JSON:** `http://127.0.0.1:8000/api/status`

### 4.2 Execute End-to-End Research Pipeline (CLI)
To run an automated research cycle from sample datasets:
```bash
python run_mvp0.py
```
This executes:
1. Document ingestion from `datasets/`
2. SHA-256 chunk hashing and provenance registration
3. Claim extraction and epistemic classification
4. Market problem discovery
5. Economic modeling and opportunity scoring
6. Report generation into `output/`

---

## 5. Adding New Components

### Adding a Model Gateway Provider
1. Create a new provider class inheriting from `BaseProvider` in `src/gateway/`.
2. Implement `generate()` and `stream()` methods.
3. Register the provider in `src/gateway/gateway.py`.
4. Add unit test coverage in `tests/`.

### Extending Ingestion Formats
1. Implement a parser in `src/ingestion/` conforming to the base extractor contract.
2. Ensure every extracted block yields a valid `source_hash` and metadata tuple.
3. Register the parser in `src/ingestion/engine.py`.
