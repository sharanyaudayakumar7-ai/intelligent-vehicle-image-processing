# GoGig Intelligent Vehicle Image Processing Pipeline

## Overview

A deliberately small, explainable take-home application: upload a vehicle image, receive a job ID immediately, and retrieve asynchronous quality, duplicate, OCR/registration-format, and dimension checks.

## Architecture and flow

`React/Vite → FastAPI upload route → PostgreSQL + local upload directory → asyncio.Queue → background worker → PostgreSQL results`.

The worker persists `pending → processing → completed` or `failed`. It is started through FastAPI's lifespan hook and runs independently of the request that queued a job.

## Database design

`jobs` holds lifecycle and filesystem path data. `image_metadata` is a one-to-one image facts table. `analysis_results` is a one-to-one record containing each check's structured JSON and indexed perceptual hash. Image binaries are deliberately not stored in PostgreSQL. Local file storage would become S3/object storage in production.

## Analysis methods

- Blur: Laplacian variance, threshold from `BLUR_THRESHOLD`.
- Brightness: mean grayscale luminance, threshold from `LOW_LIGHT_THRESHOLD`.
- Duplicate: perceptual hash Hamming distance, threshold from `DUPLICATE_HASH_DISTANCE`.
- OCR: local EasyOCR, then normalized against an Indian registration pattern. OCR is not treated as ground truth.
- Dimensions: minimum configured width/height.

## Windows / PostgreSQL setup

Install PostgreSQL for Windows, then run in **SQL Shell (psql)**:

```sql
CREATE USER gogig_user WITH PASSWORD 'choose-a-local-password';
CREATE DATABASE gogig_vehicle_pipeline OWNER gogig_user;
```

Create `backend/.env` from `.env.example`, replacing `DATABASE_URL`:

```env
DATABASE_URL=postgresql+psycopg://gogig_user:choose-a-local-password@localhost:5432/gogig_vehicle_pipeline
```

## Start the backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Tables are created on startup for the assignment. Production code should use versioned migrations (for example Alembic).

## Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the API is not at `http://localhost:8000`.

## API examples

```powershell
curl.exe -X POST http://localhost:8000/api/v1/images -F "file=@C:\path\vehicle.jpg"
curl.exe http://localhost:8000/api/v1/images/<job_id>/status
curl.exe http://localhost:8000/api/v1/images/<job_id>/results
```

Upload returns HTTP 202 and `{"job_id":"...","status":"pending"}`. Results returns a clear waiting message for pending/processing jobs, final structured results for completed jobs, and a failure reason for failed jobs.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Detector tests use generated arrays and do not call external AI services. API helper tests cover missing IDs. Manual end-to-end testing should upload each of the three assignment images and poll `/status` then `/results`.

## Configuration

All analysis thresholds and operational settings live in `.env`: database URL, upload directory, CORS origins, file types, blur/brightness/duplicate/dimension thresholds, OCR enablement, and log level.

## Trade-offs and limitations

- The in-memory `asyncio.Queue` is intentionally non-durable. Restarting the API loses queued-but-not-yet-started jobs. Production could use Redis, RabbitMQ, or SQS with independent workers.
- One in-process worker is appropriate for this take-home, not horizontal scale.
- EasyOCR can be slow on first run and can misread plates; the response communicates uncertainty rather than accuracy claims.
- Perceptual hashing identifies visual similarity, not definitive duplication.
- Local filesystem storage is for development only.

## AI usage disclosure

AI assistance was used to help scaffold modules, tests, README structure, and candidate implementation details. The architecture, configuration boundaries, error behavior, and detector claims were manually reviewed. In particular, suggestions that could imply OCR or duplicate-detection certainty were rejected; responses explicitly state uncertainty. The code is validated with unit tests and should be manually exercised against the supplied images and local PostgreSQL before submission.
