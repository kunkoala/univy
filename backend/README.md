# Univy Backend

This is the backend service for the Univy project, built with FastAPI, Celery, and Alembic. It provides APIs for PDF/document processing, background task management, and database migrations.

---

## Table of Contents
- [Features](#features)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running the FastAPI App](#running-the-fastapi-app)
- [Celery Workers & Beat](#celery-workers--beat)
- [Database Migrations & Reset](#database-migrations--reset)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)

---

## Features
- Upload and parse PDF documents asynchronously
- Background processing with Celery (multiple queues)
- Periodic maintenance tasks (cleanup, scanning)
- REST API for document management
- Database migrations with Alembic

---

## Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd backend
   ```

2. **Install dependencies** (Python 3.12 required)
   ```bash
   pip install -r requirements.txt
   # or, if using Poetry
   poetry install
   ```

3. **Copy and configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

4. **Create required folders** (auto-created on app start, but can be created manually)
   ```bash
   mkdir -p uploads outputs
   ```

---

## Environment Variables
See `env.example` for all options. Key variables:

- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Database connection
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`: Redis for Celery broker/result backend
- `CORS_ORIGINS`, `CORS_HEADERS`: CORS settings
- `OPENAI_API_KEY`, `LIGHTRAG_URL`, `LIGHTRAG_API_KEY`: (if using Lightrag/OpenAI integrations)

---

## Running the FastAPI App

```bash
uvicorn src.univy.main:app --reload
```

- The API will be available at `http://localhost:8000` by default.
- Health check: `GET /healthcheck`

---

## Celery Workers & Beat

Celery is used for background processing. There are multiple queues for different task types.

### Start All Workers
```bash
python scripts/start_celery_workers.py
```

### Start Worker for a Specific Queue
```bash
python scripts/start_celery_workers.py --queue <queue_name> --concurrency <num_workers> --loglevel <level>
# Example:
python scripts/start_celery_workers.py --queue pdf_processing --concurrency 2
```

#### Available Queues
- `pdf_processing`: For CPU-intensive PDF parsing tasks
- `file_scanning`: For scanning upload directories (I/O intensive)
- `maintenance`: For periodic cleanup and maintenance

### Start Celery Beat (Scheduler)
```bash
python scripts/start_celery_beat.py
```

---

## Database Migrations & Reset

### Run Alembic Migrations
```bash
alembic upgrade head
```

### Reset Database (Dangerous: drops and recreates all tables)
```bash
python scripts/reset_db.py
```

---

## API Endpoints

All endpoints are prefixed with `/pdf_parser`.

### Upload a PDF
- `POST /pdf_parser/upload`
  - Upload a PDF file. Triggers background parsing.

### Scan for New Files
- `POST /pdf_parser/scan`
  - Scans the upload directory for new files (background task).

### Check Task Status
- `GET /pdf_parser/task-status/{task_id}`
  - Get the status/result of a Celery task.

### Cleanup Old Task Directories
- `POST /pdf_parser/cleanup`
  - Triggers cleanup of old output directories (background task).

### Health Check
- `GET /healthcheck`
  - Returns `{"status": "ok"}` if the app is running.

---

## Project Structure

```
backend/
  alembic/                # Alembic migration scripts
  openapi/                # OpenAPI specs
  scripts/                # Helper scripts (Celery, DB reset)
  src/univy/              # Main application code
    api.py                # API router
    main.py               # FastAPI app
    celery_config/        # Celery config
    pdf_parser/           # PDF processing logic
  test_pdfs/              # Example/test PDFs
  tests/                  # (empty)
```

---

## Notes
- **Celery workers and beat must be started separately from the FastAPI app.**
- **Uploads** are stored in the `uploads/` directory, and outputs in `outputs/`.
- **Database migrations** use Alembic and are configured in `alembic.ini`.
- For more details, see the source code and comments.
