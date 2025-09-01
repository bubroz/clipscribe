# ClipScribe Beta Launch Checklist

## Phase 1: Technical Deployment (This Week)

### 1. Deploy v2.45.0 Architecture
- [ ] Cloud Build deployment (IN PROGRESS)
- [ ] Verify all services are running
- [ ] Check logs for startup errors

### 2. Create Cloud Tasks Queues
```bash
# Create the queues
gcloud tasks queues create clipscribe-short \
  --location=us-central1 \
  --max-dispatches-per-second=10 \
  --max-concurrent-dispatches=100

gcloud tasks queues create clipscribe-long \
  --location=us-central1 \
  --max-dispatches-per-second=2 \
  --max-concurrent-dispatches=10
```

### 3. End-to-End Testing
- [ ] Submit test job via API
- [ ] Verify job appears in Cloud Tasks queue
- [ ] Confirm worker picks up and processes job
- [ ] Check output artifacts in GCS
- [ ] Test monitoring endpoints

### 4. Cost Verification
- [ ] Process 5-10 test videos
- [ ] Monitor actual costs in GCP console
- [ ] Verify we're under $0.01/video average

## Phase 2: Beta User Preparation (Next 2 Weeks)

### 1. Token Management System
- [ ] Create beta token generation script
- [ ] Set up token tracking spreadsheet
- [ ] Document token distribution process

### 2. Beta Documentation
- [ ] Create beta user guide
- [ ] Write FAQ for common issues
- [ ] Set up feedback collection form

### 3. Legal Preparation
- [ ] Draft basic Terms of Service
- [ ] Create Privacy Policy
- [ ] Add legal disclaimers to web UI

### 4. Communication Channels
- [ ] Set up beta user Discord/Slack
- [ ] Create email templates for invites
- [ ] Prepare status update schedule

## Phase 3: Beta User Recruitment (Week 3-4)

### 1. Initial Beta Users (5-10)
Target: Trusted contacts who understand "beta"
- [ ] Family members (wife, kids for UI testing)
- [ ] Close friends in research/analysis
- [ ] Former colleagues who'd benefit
- [ ] Early supporters from Twitter/LinkedIn

### 2. Outreach Strategy
- [ ] Personal email invitations
- [ ] 1-on-1 onboarding calls
- [ ] Clear expectations about beta status
- [ ] Feedback collection process

### 3. Token Distribution
- [ ] Generate unique tokens per user
- [ ] Track usage and costs per token
- [ ] Set conservative limits initially
- [ ] Monitor for abuse/issues

## Phase 4: Expand to 20-50 Users (Month 2-3)

### 1. Recruitment Channels
- [ ] Twitter announcement
- [ ] LinkedIn post
- [ ] Relevant subreddit posts
- [ ] University research groups

### 2. Selection Criteria
- [ ] Clear use case for video analysis
- [ ] Willing to provide feedback
- [ ] Understanding of beta limitations
- [ ] Diverse use cases (research, journalism, education)

## Phase 5: Public Launch Prep (Month 5-6)

### 1. Business Formation
- [ ] Register LLC
- [ ] Business bank account
- [ ] Accounting setup
- [ ] Insurance considerations

### 2. Payment Integration
- [ ] Stripe account setup
- [ ] Subscription management
- [ ] Usage tracking
- [ ] Billing portal

### 3. Marketing Website
- [ ] Landing page design
- [ ] Pricing page
- [ ] Documentation site
- [ ] Blog/case studies

## Success Metrics

### Technical
- [ ] <1% error rate on job processing
- [ ] <30s average processing time for 5min videos
- [ ] <$0.01/video average cost
- [ ] 99.9% uptime

### Business
- [ ] 80% beta user retention
- [ ] 10+ testimonials/case studies
- [ ] Clear product-market fit signals
- [ ] Path to 100 paying customers

## Risk Mitigation

### Technical Risks
- [ ] Daily GCP billing alerts
- [ ] Automatic pause at $100/day
- [ ] Rate limiting per token
- [ ] Gradual rollout

### Business Risks
- [ ] Clear beta disclaimers
- [ ] No payment until stable
- [ ] Conservative promises
- [ ] Focus on learning

---

This checklist will guide us from technical deployment through public launch. Update regularly!
