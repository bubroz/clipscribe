# ClipScribe Strategic Roadmap: From Tool to SaaS Platform

*Last Updated: 2025-09-01*

## Strategic Vision: The Video Intelligence SaaS Platform

ClipScribe is evolving from a CLI-first tool to a **web-based SaaS platform**. Our mission is to democratize video intelligence, making professional-grade analysis accessible to individual researchers, analysts, and small teams.

Our core competitive advantage is our ability to provide deep intelligence extraction at a radically disruptive price point, with a clear path to scalable deployment.

---

## Current Status: Private Alpha

**⚠️ PRIVATE ALPHA**: ClipScribe v2.44.0 is deployed to Google Cloud Run but NOT publicly available.

- **Infrastructure Ready**: API and web services are deployed but access-restricted
- **Worker Service**: In development with hybrid Cloud Run + Compute Engine architecture
- **Beta Timeline**: Private alpha (Month 1-2) → Closed beta (Month 3-4) → Public launch (Month 6+)

---

## Phase 1: Foundation & Deployment (Completed)

- **✅ Critical Bug Fixes**: Resolved all deployment-blocking issues.
- **✅ Professional CLI**: A stable and feature-complete command-line interface.
- **✅ Full API Implementation**: A production-ready FastAPI backend.
- **✅ Job Queuing System**: A scalable job queuing system with Redis.
- **✅ Performance & Build Optimization**: A multi-stage Dockerfile for small, efficient images.

---

## Phase 2: User Experience & Commercialization (Current Focus)

*Goal: Build on our stable backend to create a polished, user-facing product and prepare for commercialization.*

### **Priority 1: Custom Domain & Professional Hosting** (IN PROGRESS)
- **Status**: Active Development
- **Tasks**:
  1.  **Configure Custom Domain**: Map the deployed services to `api.clipscribe.app` and `clipscribe.app` using Cloudflare.
  2.  **Set Up Production Monitoring**: Implement basic monitoring and alerting for the live services.

### **Priority 2: User Authentication & Billing**
- **Status**: Not Started
- **Tasks**:
  1.  Implement a secure user account system.
  2.  Integrate with a payment provider (e.g., Stripe) for pay-per-use billing.

### **Priority 3: Interactive Results Dashboard**
- **Status**: Not Started
- **Tasks**:
  1.  Create a dynamic dashboard to display the results of a processed video.
  2.  Include interactive visualizations for the knowledge graph and entities.
  3.  Provide options to download all generated artifacts.

---

## Phase 3: "Pro" Platform (Automation & Scheduling)

*Goal: Introduce subscription tiers with high-value automation features for recurring revenue.*

### **Priority 4: Scheduled & Automated Processing**
- **Status**: Not Started
- **Tasks**:
  1.  Build the backend functionality for users to schedule recurring tasks (e.g., "process the latest video from this channel every day").
  2.  Create UI components for managing these schedules.

### **Priority 5: Subscription Billing**
- **Status**: Not Started
- **Tasks**:
  1.  Integrate a subscription billing model (e.g., Stripe Subscriptions).
  2.  Define feature tiers for different subscription levels.
