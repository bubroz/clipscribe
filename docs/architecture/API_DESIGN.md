# ClipScribe SaaS - API Design Document (v1)

*Last Updated: August 4, 2025*
*Status: DRAFT*

## 1. Overview

This document defines the version 1 specification for the ClipScribe public API. The API will provide programmatic access to ClipScribe's core video intelligence extraction capabilities. The primary goal is to provide a simple, robust, and asynchronous interface for developers to submit videos for processing and retrieve the results.

## 2. Guiding Principles

- **API-First:** The API is the core product. All other clients (CLI, Web App) will be built on top of this public API.
- **Asynchronous by Default:** Video processing is a long-running task. The API will be asynchronous, based on a job queue model. Users will submit a job and then poll for its status.
- **Simple & RESTful:** The API will follow standard REST conventions.
- **Secure:** All endpoints will be protected by API key authentication.
- **Scalable:** The architecture will be designed to scale horizontally to handle a high volume of requests.

## 3. Authentication

Authentication will be handled via an API key sent in the HTTP header.

`Authorization: Bearer <YOUR_API_KEY>`

Keys will be generated and managed through the user's account dashboard in the future web application.

## 4. Endpoints

### POST /v1/jobs

Submits a new video for processing.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "use_flash": false,
  "webhook_url": "https://your-service.com/webhook/optional"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_12345abcde",
  "status": "QUEUED",
  "estimated_cost": 0.1916,
  "status_url": "https://api.clipscribe.com/v1/jobs/job_12345abcde"
}
```

### GET /v1/jobs/{job_id}

Retrieves the status and results of a processing job.

**Response (200 OK):**
```json
{
  "job_id": "job_12345abcde",
  "status": "COMPLETED", // or QUEUED, PROCESSING, FAILED
  "created_at": "2025-08-04T18:00:00Z",
  "completed_at": "2025-08-04T18:05:21Z",
  "result": {
    "output_urls": {
      "report_md": "https://storage.googleapis.com/...",
      "entities_json": "https://storage.googleapis.com/...",
      "knowledge_graph_gexf": "https://storage.googleapis.com/..."
      // ... links to all generated files
    }
  },
  "error": null // or an error message if status is FAILED
}
```

## 5. Data Models

The API will return the same rich `VideoIntelligence` Pydantic models that the CLI currently produces. The final output will be links to the generated files stored in a cloud storage bucket (e.g., GCS or S3).

## 6. Error Handling

The API will use standard HTTP status codes:
- `202 Accepted`: Job successfully submitted.
- `400 Bad Request`: Invalid URL or parameters.
- `401 Unauthorized`: Invalid or missing API key.
- `404 Not Found`: Job ID not found.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: An error occurred on our end.
