import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8001";
console.log("API URL:", API_URL);

const ACCEPTED_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
]);

const TERMINAL_STATUSES = new Set([
  "completed",
  "failed",
]);

const ACTIVE_STATUSES = new Set([
  "uploading",
  "pending",
  "processing",
]);

function readResponse(response) {
  return response.json().catch(() => ({})).then((body) => {
    if (!response.ok) {
      throw new Error(
        body.detail ||
          body.message ||
          `Request failed (${response.status})`
      );
    }

    return body;
  });
}

function StatusBadge({ status }) {
  return (
    <span className={`status status-${status || "uploading"}`}>
      {status || "uploading"}
    </span>
  );
}

function Value({ children }) {
  return <span className="value">{children ?? "—"}</span>;
}

function CheckCard({ title, state, icon, children }) {
  return (
    <section className={`check-card ${state}`}>
      <div className="check-heading">
        <span className="check-icon">{icon}</span>
        <h4>{title}</h4>
      </div>

      {children}
    </section>
  );
}

function ResultDetails({ result }) {
  const analysis = result.analysis || {};
  const image = result.image || {};

  const blur = analysis.blur || {};
  const brightness = analysis.brightness || {};
  const duplicate = analysis.duplicate || {};
  const plate = analysis.number_plate || {};
  const dimensions = analysis.dimensions || {};

  return (
    <div className="result-details">
      <div className="image-meta">
        <div>
          <span>Filename</span>
          <strong>{image.filename || "—"}</strong>
        </div>

        <div>
          <span>Dimensions</span>
          <strong>
            {image.width
              ? `${image.width} × ${image.height}`
              : "—"}
          </strong>
        </div>

        <div>
          <span>Format</span>
          <strong>{image.mime_type || "—"}</strong>
        </div>
      </div>

      <div className="checks-grid">
        <CheckCard
          title="Image quality"
          icon="✓"
          state={blur.is_blurry ? "problem" : "pass"}
        >
          <div className="metric-row">
            <span>Sharpness score</span>
            <Value>{blur.score}</Value>
          </div>

          <div className="metric-row">
            <span>Threshold</span>
            <Value>{blur.threshold}</Value>
          </div>

          <div className="check-result">
            {blur.is_blurry
              ? "Blur detected"
              : "Image is sufficiently sharp"}
          </div>
        </CheckCard>

        <CheckCard
          title="Brightness"
          icon="☀"
          state={brightness.is_low_light ? "problem" : "pass"}
        >
          <div className="metric-row">
            <span>Brightness score</span>
            <Value>{brightness.score}</Value>
          </div>

          <div className="metric-row">
            <span>Threshold</span>
            <Value>{brightness.threshold}</Value>
          </div>

          <div className="check-result">
            {brightness.is_low_light
              ? "Low-light condition detected"
              : "Brightness is within range"}
          </div>
        </CheckCard>

        <CheckCard
          title="Duplicate check"
          icon="◈"
          state={duplicate.is_duplicate ? "warning" : "pass"}
        >
          <div className="metric-row">
            <span>Hash distance</span>
            <Value>{duplicate.hash_distance}</Value>
          </div>

          <div className="metric-row">
            <span>Matched job</span>
            <Value>
              {duplicate.matched_job_id
                ? duplicate.matched_job_id
                : "No match"}
            </Value>
          </div>

          <div className="check-result">
            {duplicate.is_duplicate
              ? "Potential duplicate image detected"
              : "No close perceptual match found"}
          </div>
        </CheckCard>

        <CheckCard
          title="Number plate / OCR"
          icon="Aa"
          state={plate.format_valid ? "warning" : "neutral"}
        >
          <div className="ocr-result">
            <div>
              <span>Extracted text</span>
              <strong>
                {plate.text ||
                  plate.extracted_text ||
                  "Not detected"}
              </strong>
            </div>

            <div>
              <span>Confidence</span>
              <strong>
                {plate.confidence != null
                  ? `${(
                      Number(plate.confidence) * 100
                    ).toFixed(1)}%`
                  : "—"}
              </strong>
            </div>
          </div>

          <div className="check-result">
            {plate.format_valid
              ? "Possible Indian vehicle registration detected"
              : "No valid Indian vehicle registration format detected"}
          </div>
        </CheckCard>

        <CheckCard
          title="Dimensions"
          icon="↗"
          state={dimensions.valid ? "pass" : "problem"}
        >
          <div className="metric-row">
            <span>Resolution</span>
            <Value>{dimensions.resolution}</Value>
          </div>

          <div className="metric-row">
            <span>Minimum required</span>
            <Value>
              {dimensions.minimum_width &&
              dimensions.minimum_height
                ? `${dimensions.minimum_width} × ${dimensions.minimum_height}`
                : "—"}
            </Value>
          </div>

          <div className="check-result">
            {dimensions.valid
              ? "Image dimensions meet requirements"
              : "Image dimensions are below requirements"}
          </div>
        </CheckCard>
      </div>
    </div>
  );
}

function App() {
  const [jobs, setJobs] = useState([]);
  const [notice, setNotice] = useState("");
  const [dragging, setDragging] = useState(false);

  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      jobs.forEach((job) => {
        if (job.preview) {
          URL.revokeObjectURL(job.preview);
        }
      });
    };
  }, []);

  function addFiles(fileList) {
    const files = Array.from(fileList || []);

    const invalid = files.filter(
      (file) => !ACCEPTED_TYPES.has(file.type)
    );

    const valid = files.filter(
      (file) => ACCEPTED_TYPES.has(file.type)
    );

    if (invalid.length) {
      setNotice(
        `${invalid.length} unsupported file${
          invalid.length === 1 ? " was" : "s were"
        } skipped. Choose JPEG, PNG, or WEBP images.`
      );
    } else {
      setNotice("");
    }

    if (!valid.length) return;

    const newJobs = valid.map((file) => ({
      localId: crypto.randomUUID(),
      file,
      preview: URL.createObjectURL(file),
      status: "selected",
      error: null,
      jobId: null,
      result: null,
    }));

    setJobs((current) => [...current, ...newJobs]);
  }

  function removeJob(localId) {
    setJobs((current) =>
      current.filter((job) => {
        if (job.localId === localId && job.preview) {
          URL.revokeObjectURL(job.preview);
        }

        return job.localId !== localId;
      })
    );
  }

  async function uploadOne(localId, file) {
    const data = new FormData();

    data.append("file", file);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/images`,
        {
          method: "POST",
          body: data,
        }
      );

      const body = await readResponse(response);

      if (!body.job_id || !body.status) {
        throw new Error(
          "The API returned an invalid upload response."
        );
      }

      setJobs((current) =>
        current.map((job) =>
          job.localId === localId
            ? {
                ...job,
                jobId: body.job_id,
                status: body.status,
              }
            : job
        )
      );
    } catch (error) {
      setJobs((current) =>
        current.map((job) =>
          job.localId === localId
            ? {
                ...job,
                status: "failed",
                error: error.message,
              }
            : job
        )
      );
    }
  }

  function analyzeImages() {
    const selected = jobs.filter(
      (job) => job.status === "selected"
    );

    if (!selected.length) {
      setNotice(
        "Choose at least one supported image before analyzing."
      );
      return;
    }

    setNotice("");

    setJobs((current) =>
      current.map((job) =>
        job.status === "selected"
          ? {
              ...job,
              status: "uploading",
              error: null,
            }
          : job
      )
    );

    selected.forEach((job) => {
      uploadOne(job.localId, job.file);
    });
  }

  function reprocessAll() {
    const availableJobs = jobs.filter((job) => job.file);

    if (!availableJobs.length) {
      setNotice("No images available to reprocess.");
      return;
    }

    setNotice("");

    setJobs((current) =>
      current.map((job) => ({
        ...job,
        status: "uploading",
        jobId: null,
        result: null,
        error: null,
      }))
    );

    availableJobs.forEach((job) => {
      uploadOne(job.localId, job.file);
    });
  }

  useEffect(() => {
    const activeJobs = jobs.filter(
      (job) =>
        job.jobId &&
        !TERMINAL_STATUSES.has(job.status)
    );

    if (!activeJobs.length) {
      return undefined;
    }

    const timer = window.setInterval(async () => {
      await Promise.all(
        activeJobs.map(async (job) => {
          try {
            const statusResponse = await fetch(
              `${API_URL}/api/v1/images/${job.jobId}/status`
            );

            const statusData =
              await readResponse(statusResponse);

            if (!statusData.status) {
              throw new Error(
                "The API returned an invalid status response."
              );
            }

            setJobs((current) =>
              current.map((item) =>
                item.localId === job.localId
                  ? {
                      ...item,
                      status: statusData.status,
                      error:
                        statusData.error_message ||
                        item.error,
                    }
                  : item
              )
            );

            if (
              TERMINAL_STATUSES.has(
                statusData.status
              )
            ) {
              const resultsResponse = await fetch(
                `${API_URL}/api/v1/images/${job.jobId}/results`
              );

              const resultData =
                await readResponse(resultsResponse);

              setJobs((current) =>
                current.map((item) =>
                  item.localId === job.localId
                    ? {
                        ...item,
                        result: resultData,
                        error:
                          resultData.error_message ||
                          item.error,
                      }
                    : item
                )
              );
            }
          } catch (error) {
            setJobs((current) =>
              current.map((item) =>
                item.localId === job.localId
                  ? {
                      ...item,
                      status: "failed",
                      error: `Status check failed: ${error.message}`,
                    }
                  : item
              )
            );
          }
        })
      );
    }, 1600);

    return () => window.clearInterval(timer);
  }, [jobs]);

  function clearAll() {
    jobs.forEach((job) => {
      if (job.preview) {
        URL.revokeObjectURL(job.preview);
      }
    });

    setJobs([]);
    setNotice("");

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  const hasSelectedImages = jobs.some(
    (job) => job.status === "selected"
  );

  const hasCompletedJobs = jobs.some(
    (job) =>
      job.status === "completed" ||
      job.status === "failed"
  );

  const hasActiveJobs = jobs.some((job) =>
    ACTIVE_STATUSES.has(job.status)
  );

  const canReprocess =
    jobs.length > 0 &&
    hasCompletedJobs &&
    !hasActiveJobs;

  return (
    <main className="app-shell">

      {/* HEADER */}

      <header className="main-header">
        <div className="header-copy">

          <div className="brand-line">
            <span className="brand-mark">IV</span>
            <span className="eyebrow">
              VEHICLE IMAGE ANALYSIS
            </span>
          </div>

          <h1>
            Intelligent Vehicle Image
            <br />
            Processing Pipeline
          </h1>

          <p className="subtitle">
            Automated quality, duplicate, number plate,
            and dimension validation through an
            asynchronous processing pipeline.
          </p>

        </div>

        <div className="api-chip">
          <span className="api-dot" />
          <span className="api-label">
            System online
          </span>
          <span className="api-url">
            {API_URL}
          </span>
        </div>
      </header>

      {/* UPLOAD */}

      <section className="upload-panel">

        <div
          className={`drop-zone ${
            dragging ? "dragging" : ""
          }`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            addFiles(event.dataTransfer.files);
          }}
        >

          <div className="upload-icon">
            ↑
          </div>

          <h2>Upload vehicle images</h2>

          <p>
            Drag and drop images here, or browse
            files from your computer.
          </p>

          <input
            ref={inputRef}
            id="image-input"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            onChange={(event) =>
              addFiles(event.target.files)
            }
          />

          <label
            className="button secondary"
            htmlFor="image-input"
          >
            Browse Images
          </label>

          <div className="file-hint">
            JPG · PNG · WEBP
            <span>Multiple images supported</span>
          </div>

        </div>

        {notice && (
          <p className="notice" role="alert">
            {notice}
          </p>
        )}

        {/* PIPELINE */}

        <div className="pipeline">

          <div className="pipeline-label">
            <span>PROCESSING PIPELINE</span>
          </div>

          <div className="pipeline-steps">

            <div className="pipeline-step active">
              <span>01</span>
              Upload
            </div>

            <div className="pipeline-line" />

            <div className="pipeline-step">
              <span>02</span>
              Quality
            </div>

            <div className="pipeline-line" />

            <div className="pipeline-step">
              <span>03</span>
              Duplicate
            </div>

            <div className="pipeline-line" />

            <div className="pipeline-step">
              <span>04</span>
              OCR
            </div>

            <div className="pipeline-line" />

            <div className="pipeline-step">
              <span>05</span>
              Dimensions
            </div>

          </div>
        </div>

        {/* ACTIONS */}

        <div className="actions">

          <div className="action-left">

            <button
              className="button primary"
              onClick={analyzeImages}
              disabled={!hasSelectedImages}
            >
              Analyze Images
            </button>

            {canReprocess && (
              <button
                className="button reprocess"
                onClick={reprocessAll}
              >
                ↻ Reprocess All
              </button>
            )}

            <button
              className="button ghost"
              onClick={clearAll}
              disabled={!jobs.length}
            >
              Clear All
            </button>

          </div>

          <div className="image-count">
            <strong>{jobs.length}</strong>
            {jobs.length === 1
              ? " image"
              : " images"}
          </div>

        </div>

      </section>

      {/* RESULTS */}

      {jobs.length > 0 && (
        <section className="jobs-section">

          <div className="section-heading">

            <div>
              <span className="section-kicker">
                ANALYSIS RESULTS
              </span>

              <h2>
                Processed images
              </h2>
            </div>

            <p>
              Each image is processed and monitored
              independently.
            </p>

          </div>

          <div className="job-grid">

            {jobs.map((job) => (

              <article
                className="job-card"
                key={job.localId}
              >

                <div className="job-top">

                  <img
                    src={job.preview}
                    alt={`Preview of ${job.file.name}`}
                  />

                  <div className="image-overlay" />

                  <button
                    className="remove"
                    onClick={() =>
                      removeJob(job.localId)
                    }
                    aria-label={`Remove ${job.file.name}`}
                  >
                    ×
                  </button>

                  <div className="image-status">
                    <StatusBadge
                      status={job.status}
                    />
                  </div>

                </div>

                <div className="job-content">

                  <div className="job-title">

                    <div>
                      <span className="file-label">
                        IMAGE FILE
                      </span>

                      <h3 title={job.file.name}>
                        {job.file.name}
                      </h3>
                    </div>

                  </div>

                  {job.jobId && (
                    <div className="job-id">
                      <span>JOB ID</span>
                      <code>{job.jobId}</code>
                    </div>
                  )}

                  {ACTIVE_STATUSES.has(
                    job.status
                  ) && (
                    <div className="loading">

                      <i />

                      <span>
                        {job.status === "uploading"
                          ? "Uploading image…"
                          : "Analysis is running in the background…"}
                      </span>

                    </div>
                  )}

                  {job.error && (
                    <p className="job-error">
                      {job.error}
                    </p>
                  )}

                  {job.status === "completed" &&
                    job.result && (
                      <ResultDetails
                        result={job.result}
                      />
                    )}

                </div>

              </article>

            ))}

          </div>

        </section>
      )}

    </main>
  );
}

createRoot(
  document.getElementById("root")
).render(<App />);