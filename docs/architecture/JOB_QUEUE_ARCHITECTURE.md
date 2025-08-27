# ClipScribe Job Queue Architecture

*Last Updated: 2025-08-26*
*Status: Implemented*

## 1. Overview

To handle long-running video processing tasks in a scalable and reliable way, ClipScribe uses a background job queuing system. This architecture decouples the job submission (via the API) from the actual work, allowing our API to remain responsive while videos are processed asynchronously.

## 2. Technology Choices

-   **Broker:** **Redis**. It is lightweight, fast, and easy to manage.
-   **Job Queue Framework:** **RQ** (Redis Queue). A simple and effective library for queuing jobs and processing them asynchronously with workers.

## 3. Architecture Diagram

```mermaid
graph TD
    A[User via Web App/API] --> B[FastAPI Web Server];
    B --> C{Redis Broker};
    C --> D[RQ Worker(s)];
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
2.  The FastAPI web server receives the request, creates a new job record with a "QUEUED" status, and pushes a task onto the Redis queue.
3.  The API immediately returns a `202 Accepted` response to the user with the `job_id`.
4.  One or more RQ workers, running on separate machines or containers, monitor the Redis queue. One of them picks up the new task.
5.  The worker updates the job status to "PROCESSING".
6.  The worker executes the core video intelligence logic (downloading the video, calling the Gemini API, etc.).
7.  Upon completion, the worker saves the resulting output files to a cloud storage bucket.
8.  The worker updates the job status to "COMPLETED" (or "FAILED") and stores the URLs to the output files.

## 5. Scalability & Reliability

-   **Scalability:** We can easily scale the number of RQ workers horizontally to handle increased load.
-   **Reliability:** RQ has built-in support for retrying failed jobs, which makes our system resilient to transient errors.
-   **Decoupling:** The web server is only responsible for handling fast API requests and doesn't get blocked by long-running tasks.
