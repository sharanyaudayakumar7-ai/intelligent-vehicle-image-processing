# Intelligent Vehicle Image Processing Pipeline

An asynchronous vehicle image analysis system that accepts uploaded images, creates a unique processing job, and performs multiple validation and analysis checks in the background.
The pipeline evaluates image quality, brightness, perceptual similarity, number-plate information, and image dimensions, then stores and returns structured analysis results through a FastAPI backend and React frontend.

## 🔗 Live Demo

The application is deployed and can be tested end-to-end using the links below.

- **Live Frontend:** https://intelligent-vehicle-image-processin.vercel.app/
- **Backend API:** https://intelligent-vehicle-image-processing.onrender.com/
- **API Documentation:** https://intelligent-vehicle-image-processing.onrender.com/docs
- **GitHub Repository:** https://github.com/sharanyaudayakumar7-ai/intelligent-vehicle-image-processing

The live frontend communicates with the deployed FastAPI backend to upload images, create processing jobs, track their status, and display the completed analysis results.

<img width="1895" height="953" alt="live-frontend-results1" src="https://github.com/user-attachments/assets/110cb451-2223-48c6-a657-1636e8ae2bad" />
<img width="1881" height="947" alt="live-frontend-results2" src="https://github.com/user-attachments/assets/780af869-6033-492b-8c31-ae4e78c6ddf3" />


## 📌 Project Overview

The Intelligent Vehicle Image Processing Pipeline is an asynchronous backend system designed to analyze uploaded vehicle images and identify potential quality and validation issues.

When an image is uploaded, the system immediately creates a unique job ID and places the job into a background processing queue. The image is then analyzed independently through multiple processing modules, while the job status is tracked throughout its lifecycle.

The pipeline currently performs the following checks:

- **Blur Detection** — evaluates image sharpness using Laplacian variance.
- **Brightness Detection** — identifies potentially low-light images using brightness metrics.
- **Duplicate Detection** — compares images using perceptual hashing.
- **OCR / Number Plate Detection** — attempts to extract vehicle registration information and validate the detected format.
- **Dimension Validation** — checks whether the uploaded image satisfies the configured resolution requirements.

The results from these modules are aggregated into a structured analysis result and persisted in PostgreSQL. The React frontend communicates with the FastAPI backend to upload images, monitor processing status, and display the analysis results.



## 🏗️ System Architecture

The system is organized into a React frontend, FastAPI backend, PostgreSQL database, and an asynchronous background-processing layer. The architecture separates request handling from image processing so that uploads can return a Job ID immediately while analysis continues in the background.

### Architecture Diagram

<img width="1536" height="1024" alt="System Architecture" src="https://github.com/user-attachments/assets/cdfe3102-f5c8-4266-b903-e5248f4cb450" />
  Figure 1 — System Architecture and Job Processing Lifecycle

  ### Deployment Architecture

The application is deployed using separate hosting services while remaining within a single GitHub repository.

- **Frontend:** React + Vite → Vercel
- **Backend:** FastAPI → Render
- **Database:** PostgreSQL
- **Communication:** HTTPS API requests between the deployed frontend and backend

The deployed frontend communicates with the FastAPI backend for image uploads, job-status polling, and retrieval of completed analysis results.
### Queue Strategy

The system uses an in-memory asynchronous queue to decouple image upload requests from longer-running image analysis.

When an image is uploaded, the API creates a unique Job ID, persists the job information, and places the job into the queue. A background worker consumes queued jobs and processes them independently, allowing the upload API to respond without waiting for the complete analysis.

The in-memory queue was intentionally chosen to keep the implementation lightweight and suitable for the scope of the assignment. For a production-scale system, it could be replaced with a durable distributed queue or message broker.
## 🔍 Core Analysis Modules

Each uploaded vehicle image is evaluated by five independent analysis modules. The modules produce structured results that are combined into the final job result.

| Module | Purpose | Primary Metric / Method |
|---|---|---|
| **Blur Detection** | Determines whether the image has sufficient sharpness | Laplacian variance |
| **Brightness Detection** | Identifies potentially low-light images | Image brightness score |
| **Duplicate Detection** | Identifies visually similar previously processed images | Perceptual hashing |
| **OCR / Number Plate Detection** | Attempts to extract and validate vehicle registration information | OCR confidence + format validation |
| **Dimension Validation** | Checks whether the image satisfies the required resolution | Width × Height |

### Blur Detection

Blur detection uses the **variance of the Laplacian** as a sharpness measure. The calculated score is compared against a configured threshold to determine whether the image has sufficient detail for further processing.

### Brightness Detection

The image brightness is calculated and compared against a configurable low-light threshold. This helps identify images that may be too dark for reliable downstream analysis.

### Duplicate Detection

A perceptual hash is generated for each image and compared against previously processed images. The resulting hash distance is used to identify potential visual duplicates.

### OCR / Number Plate Detection

The OCR module attempts to extract text from the vehicle image and validate the extracted text against an expected Indian vehicle registration format.

The system does not force an OCR result when the extracted text cannot be confidently validated. In such cases, the result is reported as **`Not detected`**.

### Dimension Validation

The uploaded image dimensions are checked against the configured minimum width and height requirements. Images that do not satisfy the required dimensions are flagged accordingly.


## 🔌 API Design

The FastAPI backend provides REST endpoints for image upload, job-status tracking, and retrieval of analysis results.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/images` | Upload image and create processing job |
| `GET` | `/api/v1/images/{job_id}/status` | Check job processing status |
| `GET` | `/api/v1/images/{job_id}/results` | Retrieve analysis results or failure details |

### Upload API

The upload endpoint returns a `202 Accepted` response with a unique Job ID while the image is queued for background processing.

<img width="1919" height="1033" alt="Screenshot 2026-08-13 205509" src="https://github.com/user-attachments/assets/a9f942ff-751c-4f99-87c6-4de28feeae9b" />

### Analysis Results API

After processing is completed, the results endpoint returns structured results from all analysis modules.
<img width="1537" height="985" alt="Screenshot 2026-08-13 205650" src="https://github.com/user-attachments/assets/11ceb319-f590-43a4-9a58-1b6ef8986204" />

**Interactive API Documentation:**  
https://intelligent-vehicle-image-processing.onrender.com/docs

## ⚙️ Configuration & Thresholds

The analysis pipeline uses configurable thresholds to determine image quality and validation results.

| Configuration | Value | Purpose |
|---|---:|---|
| `BLUR_THRESHOLD` | `100.0` | Minimum Laplacian variance for acceptable sharpness |
| `LOW_LIGHT_THRESHOLD` | `60.0` | Brightness threshold for low-light detection |
| `DUPLICATE_HASH_DISTANCE` | `6` | Maximum perceptual-hash distance for duplicate detection |
| `MIN_IMAGE_WIDTH` | `640 px` | Minimum required image width |
| `MIN_IMAGE_HEIGHT` | `480 px` | Minimum required image height |
| `OCR_ENABLED` | `true` | Enables OCR / number-plate analysis |

These values are maintained through environment-based configuration, allowing the analysis criteria to be adjusted without changing the processing modules.


## 🧪 Testing & Validation

The system was validated both locally and through the deployed application.

### Automated / Functional Test Results

The implemented test suite currently passes all available test cases:

**15 / 15 tests passed** ✅

This verifies the expected behavior of the implemented API and processing components.

<img width="1833" height="783" alt="Screenshot 2026-08-13 222349" src="https://github.com/user-attachments/assets/5299e992-cd71-4538-bf95-72acbf21e213" />


### Local Background Processing

The backend was also tested locally to verify the complete asynchronous processing workflow.

The local execution confirmed:

- Job creation and queueing
- Background worker startup
- Queue consumption
- Image processing
- Individual analysis stages
- Result persistence
- Successful completion of the processing job

<img width="1803" height="863" alt="Screenshot 2026-08-13 222918" src="https://github.com/user-attachments/assets/7176ea47-348c-43e4-b041-3423cef26cbc" />

The local logs demonstrate the complete lifecycle from job creation through background processing and result persistence.

## 📊 Results & Evaluation

Each processed image produces a structured result containing the outputs of all analysis modules.

The result includes:

- **Image Quality** — Laplacian variance-based sharpness score and threshold comparison.
- **Brightness** — brightness score with low-light threshold evaluation.
- **Duplicate Detection** — perceptual hash, hash distance, and matched-job information.
- **OCR / Number Plate** — extracted text, confidence, and Indian vehicle-registration format validation.
- **Dimensions** — image width, height, resolution, and minimum-dimension validation.

The final result is persisted in PostgreSQL and returned through the Results API.

### Example API Response
<img width="1411" height="879" alt="Screenshot 2026-08-13 010222" src="https://github.com/user-attachments/assets/7c05a2f8-82a4-44ba-b291-eeb3ca4d6538" />

## ⚖️ Design Trade-offs & Limitations

The implementation prioritizes simplicity, modularity, and reliable end-to-end processing within the scope of the assignment.

| Decision | Benefit | Trade-off |
|---|---|---|
| **In-memory async queue** | Simple and lightweight background processing | Queued jobs are lost if the backend process restarts |
| **PostgreSQL persistence** | Reliable storage for jobs, metadata, and results | Requires a persistent database connection |
| **Server-side image storage** | Simple implementation | Not ideal for large-scale or multi-instance deployments |
| **Configurable thresholds** | Easy to tune analysis behavior | Thresholds require calibration against a larger labelled dataset |
| **CPU-based OCR** | No GPU infrastructure required | OCR can be slower and more sensitive to image quality |
| **Modular analysis pipeline** | Individual checks can be maintained and extended independently | Processing time increases as additional analysis stages are added |

### OCR Deployment Limitation

The OCR pipeline was validated locally using the complete development environment, where supported vehicle images can produce extracted number-plate text that is reasonably close to the expected registration value.

In the deployed environment, OCR behavior can be less consistent due to differences in available resources and runtime dependencies. Some images that produce OCR output locally may therefore return `Not detected` in the deployed application.

The system does not substitute or hard-code a plate number when OCR is uncertain. Instead, it reports `Not detected`, allowing the remaining image-analysis checks to complete normally.

This provides graceful degradation rather than presenting an unreliable result.

### Scalability Considerations

For a production-scale deployment, the current in-memory queue could be replaced with a durable distributed queue such as Redis or a managed message broker. Uploaded images could also be moved from server-side storage to object storage, and background workers could be scaled independently from the API service.

## 🛡️ Reliability, Failure Handling & Retry

The processing pipeline is designed to handle asynchronous job failures without immediately terminating the workflow.

- Each job supports up to **2 processing attempts**.
- Retryable failures are logged and the job is reprocessed.
- Successfully processed jobs are marked as `completed`.
- Jobs that fail after the maximum retry attempts are marked as `failed`.
- Error information is persisted for failed jobs.
- Processing events and analysis-stage durations are logged for debugging and observability.

The backend logs key events throughout the lifecycle, including:

- Job creation and queueing
- Background worker startup
- Queue consumption
- Processing attempts
- Individual analysis stages
- Processing duration
- Result persistence
- Final completion or failure

### Job State Flow

```text
pending
   │
   ▼
processing
   │
   ├──────────────► completed
   │
   └── failure
         │
         ▼
       retry
         │
         ├──────────────► completed
         │
         └──────────────► failed
````

## 🤖 AI-Assisted Development

AI tools were used as development assistants for architecture discussions, backend/frontend debugging, asynchronous processing logic, error handling, and documentation.

AI-generated suggestions were validated against the actual implementation by running the application locally, testing APIs through Swagger, inspecting background-worker logs, executing the automated test suite, and verifying the deployed frontend.

One example of AI output requiring correction was the local server configuration: an AI-suggested Uvicorn command initially used a stale virtual-environment path and failed to launch. The issue was identified from the runtime error and corrected by using the project's active environment and `python -m uvicorn` invocation. Similar suggestions were modified or discarded whenever they did not match the project's actual runtime or deployment configuration.

AI was therefore used as an engineering assistant, with implementation decisions verified through actual execution and testing rather than accepted blindly.

## 🧠 Design Decisions

The main design decisions were made to keep the system modular, asynchronous, and easy to extend while avoiding unnecessary infrastructure for the scope of the assignment.

- **FastAPI** was chosen for its lightweight REST API design and support for asynchronous application workflows.
- **In-memory asynchronous queue** was used to keep background job processing simple without introducing an additional queueing service.
- **PostgreSQL** was selected for persistent storage of jobs, image metadata, processing status, and structured analysis results.
- **Modular analysis services** allow each image-quality or validation check to be developed and maintained independently.
- **Job-based processing** separates image upload from longer-running analysis and allows the frontend to track each image independently.
- **React + Vite** provides a lightweight frontend for image upload, job monitoring, and result visualization.

## 🚀 Future Improvements

The current implementation is designed for the scope of the assignment. For a production-scale system, the following improvements could be considered:

- Replace the in-memory queue with a durable distributed queue such as Redis or a managed message broker.
- Move uploaded images to object storage instead of server-side filesystem storage.
- Scale background workers independently from the API service.
- Calibrate blur, brightness, and duplicate-detection thresholds using a larger labelled dataset.
- Improve number-plate detection with a dedicated vehicle/number-plate detection model.
- Add authentication, rate limiting, monitoring, and structured application metrics.
- Add automated evaluation of OCR and image-quality performance using a representative test dataset.

## 🛠️ Running Locally

### Prerequisites

- Python 3.13+
- Node.js
- PostgreSQL

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment and install the dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables using:

```text
backend/.env.example
```

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

**Backend API:**  
[http://127.0.0.1:8001](http://127.0.0.1:8001)

**Swagger Documentation:**  
[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

### Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at the local Vite URL displayed in the terminal.

Configure the frontend to communicate with the local backend:

```text
http://127.0.0.1:8001
```
## 📌 Assumptions

- Uploaded files are expected to be valid vehicle images in supported image formats.
- Analysis thresholds are configurable and are not intended to represent universal production-quality standards.
- OCR is treated as a best-effort signal rather than a guaranteed source of truth.
- Duplicate detection identifies visually similar images using perceptual-hash distance.
- The current in-memory queue is intended for assignment-scale workloads rather than high-availability production workloads.
