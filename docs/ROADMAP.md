# ClipScribe Strategic Roadmap: From Tool to SaaS Platform

*Last Updated: August 4, 2025*

## Strategic Vision: The Video Intelligence SaaS Platform

Following a comprehensive technical and market validation, ClipScribe is pivoting from a CLI-first tool to a **web-based SaaS platform**. Our mission is to democratize video intelligence, making professional-grade analysis accessible to individual researchers, analysts, and small teams who are currently underserved by expensive enterprise solutions.

Our core competitive advantage is our ability to provide deep intelligence extraction (entities, relationships, knowledge graphs) from 1800+ platforms at a radically disruptive price point.

---

## Phase 1: API-ization & Core Service Extraction (The Foundation)
*Goal: Decouple our core logic from the CLI and build a stable, scalable, service-oriented architecture.*

### **Priority 1: Fix Long-Video Processing (Critical Blocker)**
- **Status**: ✅ COMPLETE
- **Justification**: The `504 Deadline Exceeded` error on long videos was the single biggest blocker to a reliable API. A service cannot have hour-long timeouts. The new "Smart Transcribe, Global Analyze" architecture resolves this.
- **Tasks**:
  1. ~~Re-architect `transcriber.py` to use a two-step process: (1) Transcribe video to text, (2) Analyze text for intelligence.~~
  2. ~~Validate the fix with a >30 minute video from the `MASTER_TEST_VIDEO_TABLE.md`.~~

### **Priority 2: Implement "Deco-Futurist" TUI (In Progress)**
- **Status**:  ইন প্রোগ্রেস
- **Justification**: A professional, stable, and aesthetically pleasing CLI is a core feature, not an afterthought. It builds user trust and serves as an architectural prototype for the future web application.
- **Tasks**:
  1. **Architect `TuiManager`**: Create a centralized manager for the `rich.Layout` to handle all rendering.
  2. **Create `log_panel`**: Implement a scrolling panel to capture and display logs cleanly.
  3. **Decouple Logic**: Refactor `VideoIntelligenceRetriever` to use a simple callback system, making it UI-agnostic.
  4. **Simplify CLI**: Refactor the main CLI command to use the `TuiManager`, drastically cleaning up the code.

### **Priority 3: Build a Core API**
- **Status**: Not Started
- **Justification**: The API is the heart of the SaaS platform. All future development (web frontend, user accounts) will be built on top of this.
- **Tasks**:
  1. Choose a framework (e.g., FastAPI).
  2. Create endpoints for processing single videos and collections.
  3. Implement API key-based authentication.

### **Priority 4: Implement a Job Queuing System**
- **Status**: Not Started
- **Justification**: Video processing is a long-running task. A job queue is essential for handling these tasks asynchronously in the background without blocking the API or web server.
- **Tasks**:
  1. Choose and integrate a task queue (e.g., Celery with Redis).
  2. Refactor the core processing logic into background workers.
  3. Create API endpoints to submit jobs and check their status.

---

## Phase 2: The MVP SaaS Platform
*Goal: Launch a minimal but functional web service to acquire our first paying customers.*

### **Priority 5: Develop a Basic Web Frontend**
- **Status**: Not Started
- **Tasks**:
  1. Build a simple web dashboard (e.g., using React or Vue).
  2. Create pages for user sign-up, login, and submitting URLs for processing.

### **Priority 6: User Authentication & Billing**
- **Status**: Not Started
- **Tasks**:
  1. Implement a secure user account system.
  2. Integrate with a payment provider (e.g., Stripe) for pay-per-use billing.

### **Priority 7: Results Dashboard**
- **Status**: Not Started
- **Tasks**:
  1. Create a page to display the results of a processed video.
  2. Include options to view the summary, entities, and download the output files.

---

## Phase 3: The "Pro" Platform (Automation & Scheduling)
*Goal: Introduce subscription tiers with high-value automation features for recurring revenue.*

### **Priority 8: Scheduled & Automated Processing**
- **Status**: Not Started
- **Tasks**:
  1. Build the backend functionality for users to schedule recurring tasks (e.g., "process the latest video from this channel every day").
  2. Create UI components for managing these schedules.

### **Priority 9: Subscription Billing**
- **Status**: Not Started
- **Tasks**:
  1. Integrate a subscription billing model (e.g., Stripe Subscriptions).
  2. Define feature tiers for different subscription levels.
