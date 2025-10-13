# Station10 Build Plan - TONIGHT

**Start**: 8:50 PM PDT  
**Token budget**: 18K remaining  
**Goal**: Working multi-user Telegram bot on Cloud Run

---

## Build Order (Cloud-First)

### 1. Database Schema (SQLite → PostgreSQL)
- User table (telegram_id, name, budget_limit)
- Video table (video_id, processed_by, cost, timestamp)
- Entity table (name, type, video_id, user_id)
- Cost tracking

### 2. Cloud Run Deployment
- Dockerfile for bot service
- Environment variables (API keys)
- Webhook setup (not polling)
- Continuous deployment

### 3. Telegram Bot Core
- User authentication (/start registers user)
- /process <URL> (queue video, notify when done)
- /recent (last 10 videos, any user)
- /search <query> (entities across all videos)
- /stats (per-user costs)

### 4. Integration
- Bot triggers existing ClipScribe pipeline
- Saves to shared storage
- Notifies user when complete
- Cost tracked per user

---

## START: Create Database Schema

File: `src/clipscribe/database/schema.sql`

