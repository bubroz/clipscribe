# ClipScribe SaaS - Job Queue Architecture (v1)

Last Updated: August 11, 2025
Status: DRAFT (exploratory). Current implementation uses Redis + RQ as documented in the Readiness Spec.

## 1. Overview

To handle long-running video processing tasks in a scalable and reliable way, ClipScribe will use a background job queuing system. This architecture decouples the job submission (via the API) from the actual work, allowing our API to remain responsive while videos are processed asynchronously.

## 2. Technology Choices

- **Broker:** **Redis**. It is lightweight, fast, and easy to manage. It's perfect for our use case.
- **Job Queue Framework:** **RQ** (Redis Queue). Lightweight and sufficient for our API v1 worker model. Previously evaluated Celery; Redis + RQ chosen for simplicity.

## 3. Architecture Diagram

```mermaid
graph TD
    A[User via Web App/API] --> B[FastAPI Web Server];
    B --> C{Redis Broker};
    C --> D[Celery Worker(s)];
    D --> E[Gemini API];
    D --> F{Database};
    D --> G[Cloud Storage];
    B --> F;
    subgraph "Job Submission"
        A; B;
    end
    subgraph "Job Processing"
        C; D; E; F; G;
    end
```

## 4. Workflow

1.  A user submits a video URL to the `/v1/jobs` API endpoint.
2.  The FastAPI web server receives the request, creates a new job record in the database with a "QUEUED" status, and pushes a task onto the Redis queue.
3.  The API immediately returns a `202 Accepted` response to the user with the `job_id`.
4.  One or more Celery workers, running on separate machines, are constantly monitoring the Redis queue. One of them picks up the new task.
5.  The worker updates the job status in the database to "PROCESSING".
6.  The worker executes the core video intelligence logic (downloading the video, calling the Gemini API, etc.).
7.  Upon completion, the worker saves the resulting output files to a cloud storage bucket (GCS or S3).
8.  The worker updates the job status in the database to "COMPLETED" (or "FAILED") and stores the URLs to the output files.
9.  If a `webhook_url` was provided, the worker sends a notification to the user's service.

## 5. Scalability & Reliability

- **Scalability:** We can easily scale the number of Celery workers horizontally to handle increased load. More workers = more videos processed in parallel.
- **Reliability:** Celery has built-in support for retrying failed jobs, which will make our system resilient to transient errors from the Gemini API or network issues.
- **Decoupling:** The web server is only responsible for handling fast API requests. It doesn't get bogged down with long-running tasks, ensuring the user-facing parts of the service are always fast and responsive.
