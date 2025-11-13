# Technical Requirements
**ClipScribe v3.0.0 Web Presence**  
**Date:** November 13, 2025  
**Purpose:** Define technical stack, infrastructure, and implementation requirements

---

## Overview

This document specifies the technical requirements for clipscribe.ai, organized by implementation phase.

**Philosophy:**
- Start simple (MVP)
- Automate incrementally
- Use managed services where possible
- Avoid premature optimization

---

## Phase 1: MVP Launch (Dec 2025)

**Goal:** Static website with manual processing

**Timeline:** 1-2 weeks to build and deploy

### Frontend

**Recommended Stack: Plain HTML/CSS/JavaScript**

**Why:**
- Fast to build
- No build step or dependencies
- Easy to maintain
- Cloudflare Pages deploys instantly
- No framework lock-in

**Alternative:** Modern framework if designer prefers
- React/Next.js (if static generation used)
- Astro (fast, modern)
- Hugo/Jekyll (static site generators)

**Requirements:**
- Responsive design (mobile + desktop)
- Semantic HTML
- Accessible (WCAG 2.1 AA)
- Fast load times (<3s)
- Works without JavaScript (progressive enhancement)

### Hosting

**Recommended: Cloudflare Pages**

**Why:**
- Free tier (generous limits)
- Global CDN (fast everywhere)
- Auto SSL
- GitHub integration (deploy on push)
- DDoS protection included

**Setup:**
1. Connect GitHub repo
2. Configure build settings (if needed)
3. Deploy automatically

**Cost:** $0/month (free tier sufficient)

**Alternative:** Netlify, Vercel (similar benefits)

### Email

**Recommended: Cloudflare Email Routing → Gmail**

**Setup:**
1. Configure trials@clipscribe.ai
2. Route to your Gmail (zforristall@gmail.com)
3. Set up Gmail filters and templates

**Why:**
- Free (included with Cloudflare domain)
- Simple setup
- Uses familiar Gmail interface
- Professional email address

**Cost:** $0/month

**Alternative:** Custom email client if you prefer

### Forms

**MVP: mailto: links**

**Why:**
- Zero setup
- No backend needed
- Works everywhere
- Simple for users

**Implementation:**
```html
<a href="mailto:trials@clipscribe.ai?subject=Single Video Processing&body=Video link:%0D%0A%0D%0ARequirements:">
  Upload Video ($25)
</a>
```

**Alternative for Phase 2:** Cloudflare Workers + R2 for file uploads

### Payments

**Recommended: Stripe Payment Links**

**Why:**
- No code required
- Create link in Stripe dashboard
- Send via email
- Secure and professional

**Setup:**
1. Create Stripe account
2. Create product: "Single Video ($25)"
3. Create product: "Single Video ($50)"
4. Generate payment links
5. Copy/paste into emails

**Process:**
1. Customer emails video link
2. You reply with Stripe payment link
3. They pay
4. You get notification
5. You process video
6. You email results

**Cost:** Stripe fees (~3% = $0.75-15 per transaction)

**Phase 2 Alternative:** Stripe Checkout API (automated)

### Analytics

**Recommended: Plausible Analytics**

**Why:**
- Privacy-friendly (GDPR compliant)
- No cookies
- Simple dashboard
- Lightweight (<1KB script)
- Honest company

**Metrics to Track:**
- Page views
- CTA clicks (GitHub, Upload, Pricing)
- Sample downloads
- Time on page
- Bounce rate

**Cost:** $9/month

**Free Alternative:** 
- Cloudflare Web Analytics (free, basic)
- Self-hosted Umami (free, requires server)

### Sample File Hosting

**Option 1: GitHub (Recommended for MVP)**

**Why:**
- Free
- Version control
- CDN via raw.githubusercontent.com
- Already using GitHub

**Setup:**
- Samples already in `examples/sample_outputs/`
- Link directly from website
- GitHub serves files

**Cost:** $0/month

**Limitations:**
- No download tracking
- Slower than CDN
- 100MB file limit (we're well under)

**Option 2: Cloudflare R2**

**Why:**
- S3-compatible
- No egress fees
- Fast global delivery
- Custom domains

**Setup:**
- Upload samples to R2 bucket
- Configure public access
- Link from website

**Cost:** $0/month (free tier: 10GB storage, 1M reads)

**Recommendation:** Start with GitHub, move to R2 if needed

---

## Phase 2: Automation (Jan-Feb 2026)

**Goal:** Remove manual processing bottleneck

**Timeline:** 2-3 weeks development + testing

### File Upload System

**Recommended: Cloudflare Workers + R2**

**Architecture:**
```
User uploads file 
  → Cloudflare Worker validates and stores in R2
  → Worker sends notification email
  → Processing queue picks up job
  → Results uploaded to R2
  → Download link emailed to user
```

**Why:**
- Serverless (no server management)
- Cheap (generous free tier)
- Fast (edge computing)
- Scalable (automatic)

**Implementation:**
- Cloudflare Workers for upload API
- R2 for file storage
- Email notification system
- Queue system (Redis or R2-based)

**Cost:** ~$5-10/month

### Processing Queue

**Option 1: Simple Cron + R2**

**How:**
- R2 bucket for pending jobs
- Cron job (every 30 min) checks for new files
- Process locally on your Mac
- Upload results to R2
- Email customer

**Why:**
- Simple to build
- Uses existing CLI
- No new infrastructure
- Can handle 10-50 videos/month

**Cost:** $0 (run on existing hardware)

**Option 2: Modal (Cloud Processing)**

**How:**
- Upload triggers Modal function
- Modal runs ClipScribe processing
- Results uploaded to R2
- Email sent automatically

**Why:**
- Fully automated
- Scales to high volume
- No local processing needed
- GPU available if needed

**Cost:** ~$10-50/month depending on volume

**Recommendation:** Start with Option 1, move to Option 2 at scale

### Payment Integration

**Stripe Checkout API**

**How:**
- User selects tier
- Create Checkout session
- Redirect to Stripe
- Webhook confirms payment
- Trigger processing automatically

**Why:**
- Professional checkout flow
- Handles taxes and compliance
- Automatic receipts
- Webhook automation

**Implementation:**
- Stripe API keys
- Webhook endpoint (Cloudflare Worker)
- Order confirmation emails

**Cost:** Stripe fees only (~3%)

### Download Portal

**Simple R2 + Signed URLs**

**How:**
- Results uploaded to R2
- Generate signed URL (expires in 7 days)
- Email URL to customer
- No login required

**Why:**
- Simple to implement
- Secure (expiring links)
- No user accounts needed
- Privacy-friendly (auto-delete)

**Cost:** $0 (within R2 free tier)

---

## Phase 3: Scale (Mar+ 2026)

**Goal:** Enterprise features and optimization

### API Access (Enterprise)

**Recommended: FastAPI + Cloudflare Workers**

**Endpoints:**
- POST /process - Submit video for processing
- GET /status/{id} - Check processing status
- GET /results/{id} - Download results

**Authentication:**
- API keys
- Rate limiting
- Usage tracking

**Cost:** $20-50/month (Workers + R2)

### Faster Processing

**GPU Processing via Modal**

**Why:**
- WhisperX runs faster on GPU
- Can offer 4-hour turnaround
- Premium tier pricing

**Cost:** $10-30 per video (GPU costs)

**Pricing:** Charge $100-200 for 4-hour turnaround

### White-Label

**Custom Branding in Outputs**

**Implementation:**
- Accept client logo
- Replace ClipScribe branding in DOCX/PPTX
- Custom footer text
- Enterprise feature only

**Cost:** Development time only

---

## Domain & DNS

**Domain:** clipscribe.ai (already owned)

**DNS:** Cloudflare

**Records Needed:**
```
A     @              192.0.2.1        (Cloudflare Pages)
CNAME www            clipscribe.ai    (Alias)
MX    @              route.mx.cloud   (Email routing)
TXT   @              "v=spf1..."      (Email auth)
```

**SSL:** Auto via Cloudflare (free)

---

## Email Configuration

### Cloudflare Email Routing

**Setup:**
1. Add domain to Cloudflare
2. Enable Email Routing
3. Create address: trials@clipscribe.ai
4. Route to: zforristall@gmail.com

**Gmail Setup:**
1. Create labels: "ClipScribe - Single", "ClipScribe - Series", "ClipScribe - Enterprise"
2. Create filters to auto-label
3. Create templates for common replies
4. Set up signatures

**Templates Needed:**
- Payment link email (single video)
- Custom quote email (series)
- Order confirmation
- Processing complete notification
- Refund confirmation

**Cost:** $0/month

---

## Performance Requirements

### Page Speed

**Targets (Lighthouse):**
- Performance: >90
- Accessibility: 100
- Best Practices: >90
- SEO: 100

**Metrics:**
- First Contentful Paint: <1.5s
- Largest Contentful Paint: <2.5s
- Time to Interactive: <3.5s
- Cumulative Layout Shift: <0.1

### Optimization Checklist

**Images:**
- [ ] WebP format with JPEG fallback
- [ ] Lazy loading below fold
- [ ] Proper sizing (srcset)
- [ ] Compressed (<100KB each)

**Code:**
- [ ] Minified CSS
- [ ] Minified JavaScript
- [ ] Critical CSS inline
- [ ] Defer non-critical JS

**Fonts:**
- [ ] System fonts (best performance) OR
- [ ] Max 2 web fonts, preloaded
- [ ] font-display: swap

**Caching:**
- [ ] Static assets cached (1 year)
- [ ] HTML cached briefly (1 hour)
- [ ] Cloudflare CDN cache

---

## Security Requirements

### SSL/TLS

- Force HTTPS (Cloudflare setting)
- TLS 1.2+ only
- HSTS header

### Email

- SPF record configured
- DKIM signing (via Cloudflare)
- DMARC policy (quarantine or reject)

### File Uploads (Phase 2)

- File type validation (video/audio only)
- Size limits (max 2GB)
- Virus scanning (ClamAV or service)
- Rate limiting (prevent abuse)

### Data Handling

- Videos deleted within 7 days
- No logs with sensitive data
- Stripe handles payment data (PCI compliant)
- No tracking beyond basic analytics

---

## Monitoring & Uptime

### Phase 1 (MVP)

**Manual Monitoring:**
- Check email daily
- Process orders manually
- Respond to support

**Uptime:**
- Cloudflare Pages (99.9%+ uptime)
- No SLA commitments

### Phase 2 (Automated)

**Recommended: UptimeRobot**

**Monitor:**
- Website availability
- API endpoints (if built)
- Email deliverability

**Alerts:**
- Email if down >5 minutes
- SMS for critical (optional)

**Cost:** Free tier sufficient

### Phase 3 (Enterprise)

**Status Page:**
- Create status.clipscribe.ai
- Show current status
- Incident history
- Uptime stats

**Tools:** Statuspage.io or self-hosted

---

## Development Workflow

### MVP Build Process

**1. Design Phase (Designer):**
- Create Figma designs
- Review and approve
- Export assets

**2. Development Phase (Developer or contractor):**
- Convert Figma to HTML/CSS
- Add content (from copy guidelines)
- Test responsive
- Optimize performance

**3. Deployment:**
- Push to GitHub
- Cloudflare Pages auto-deploys
- Test on live domain
- Configure DNS

**Timeline:** 1-2 weeks

### Ongoing Updates

**Content Changes:**
- Edit HTML files
- Push to GitHub
- Auto-deploys in ~1 minute

**Pricing Changes:**
- Update pricing page
- Update Stripe products
- Announce changes

---

## Infrastructure Costs Summary

### Phase 1 (MVP)

| Service | Cost | Purpose |
|---------|------|---------|
| Cloudflare Pages | $0/mo | Hosting |
| Cloudflare Email | $0/mo | trials@clipscribe.ai |
| Stripe | 3% per transaction | Payments |
| Plausible Analytics | $9/mo | Privacy-friendly analytics |
| **Total** | **$9/mo + payment fees** | |

### Phase 2 (Automated)

| Service | Cost | Purpose |
|---------|------|---------|
| Cloudflare Workers | $5/mo | Upload API, webhooks |
| Cloudflare R2 | $0-5/mo | File storage |
| UptimeRobot | $0/mo | Monitoring |
| Everything from Phase 1 | $9/mo | |
| **Total** | **$14-19/mo + payment fees** | |

### Phase 3 (Enterprise)

| Service | Cost | Purpose |
|---------|------|---------|
| Modal (processing) | $10-50/mo | Automated processing |
| Statuspage | $29/mo | Status page |
| Support tool (optional) | $0-50/mo | Customer support |
| Everything from Phase 2 | $14-19/mo | |
| **Total** | **$53-148/mo + payment fees** | |

**Sustainable:** Single $25 customer per month covers all costs

---

## Technical Stack Recommendations

### MVP (Recommended)

```
Frontend:     Plain HTML/CSS/JS or Astro
Hosting:      Cloudflare Pages
Email:        Cloudflare Email Routing → Gmail
Payments:     Stripe Payment Links
Analytics:    Plausible
Downloads:    GitHub (sample files)
Processing:   Manual (your Mac)
```

**Total complexity:** Low  
**Total cost:** $9/month  
**Build time:** 1-2 weeks

### Automated (Phase 2)

```
Frontend:     Same as MVP
Hosting:      Cloudflare Pages
Email:        Cloudflare Email Routing
Payments:     Stripe Checkout API
Analytics:    Plausible
Downloads:    Cloudflare R2 + signed URLs
Uploads:      Cloudflare Workers + R2
Processing:   Cron job (local) or Modal (cloud)
Queue:        R2-based or Redis
Notifications: Email via Sendgrid/Postmark
```

**Total complexity:** Medium  
**Total cost:** $20-50/month  
**Build time:** 2-3 weeks

### Enterprise (Phase 3)

```
Everything from Phase 2 PLUS:

API:          FastAPI + Cloudflare Workers
Auth:         API keys + rate limiting
Processing:   Modal (GPU for speed)
Support:      Help Scout or Intercom
Status:       Statuspage.io
Monitoring:   Sentry + UptimeRobot
Integrations: Zapier or custom webhooks
```

**Total complexity:** High  
**Total cost:** $100-200/month  
**Build time:** 4-6 weeks

---

## Page-Specific Requirements

### Landing Page (/)

**Static Content:**
- All sections server-rendered
- No dynamic content
- Fast load priority

**Interactive Elements:**
- Expandable FAQ (JavaScript)
- Smooth scrolling (optional)
- CTA button tracking (analytics event)

**Performance:**
- Hero image: <200KB
- Total page: <500KB
- Load time: <2 seconds

### Pricing Page (/pricing)

**Interactive Elements:**
- Expandable tier details (accordion)
- Expandable FAQ
- Table sticky header (scroll)

**No Backend Required:**
- All content static
- Prices hardcoded (update rarely)

### Samples Page (/samples)

**Interactive Elements:**
- Expandable "View Files" sections
- Download tracking (analytics events)
- Format tabs or sections

**Downloads:**
- Direct links to GitHub or R2
- Track downloads in analytics
- ZIP files for "Download All"

### Contact Page (/contact)

**MVP:**
- mailto: links for email
- Direct link to GitHub
- Calendly embed for enterprise (optional)

**Phase 2:**
- Simple contact form (Cloudflare Workers)
- File upload form (for video files)
- Automated email responses

---

## Email System Requirements

### Phase 1: Manual Gmail

**Folder Structure:**
```
ClipScribe/
├─ Single Video/
│  ├─ Pending Payment
│  ├─ Payment Received
│  ├─ Processing
│  └─ Delivered
├─ Series/
│  ├─ Quote Requested
│  ├─ Quote Sent
│  ├─ Processing
│  └─ Delivered
└─ Enterprise/
   ├─ Inquiry
   ├─ In Discussion
   └─ Customer
```

**Templates:**
- Payment link email
- Order confirmation
- Processing started
- Results delivered
- Refund confirmation

**Process:**
1. Receive email
2. Label appropriately
3. Send payment link template
4. Process when paid
5. Deliver results
6. Move to "Delivered"

### Phase 2: Automated Emails

**Tool:** Sendgrid or Postmark

**Automated Emails:**
- Order confirmation (immediate)
- Payment received (immediate)
- Processing started (when queued)
- Results ready (with download links)
- Download link expiring soon (6 days after)

**Cost:** $0-15/month (free tier sufficient initially)

---

## File Management

### Sample Files

**Current:**
- 24 files in `examples/sample_outputs/`
- Hosted on GitHub
- Total size: ~1.5MB

**MVP Hosting:**
- Link directly from GitHub
- OR: Copy to R2 for faster delivery

**Phase 2:**
- R2 bucket for all files
- Public access with custom domain
- samples.clipscribe.ai or clipscribe.ai/samples/

### Customer Results (Phase 2)

**Storage:**
- Cloudflare R2
- Separate bucket per customer order
- Signed URLs (expire after 7 days)

**Cleanup:**
- Automatic deletion after 7 days
- Customer has download window
- No long-term storage

**Backup:**
- None needed (customer downloads)
- Processing can be re-run if needed

---

## Development Environment

### Local Development

**Requirements:**
- Modern browser (Chrome, Firefox, Safari)
- Text editor (VS Code recommended)
- Local server (for testing, optional)
- Git (version control)

**Setup:**
```bash
git clone https://github.com/[designer-repo]/clipscribe-website
cd clipscribe-website
# If using framework:
npm install
npm run dev
# If plain HTML:
python3 -m http.server 8000
# Open http://localhost:8000
```

### Testing

**Browsers:**
- Chrome (desktop + mobile)
- Firefox
- Safari (desktop + mobile)
- Edge

**Devices:**
- Desktop (1440px)
- Laptop (1024px)
- Tablet (768px)
- Mobile (375px, 414px)

**Accessibility:**
- Screen reader (NVDA or VoiceOver)
- Keyboard navigation
- Color contrast checks
- WAVE accessibility tool

### Deployment

**Cloudflare Pages:**

1. Connect GitHub repo
2. Configure build settings:
   - Framework: [None] or [Astro/Next.js]
   - Build command: `npm run build` (if needed)
   - Output directory: `dist` or `build`
3. Deploy automatically on push to main

**Domain:**
- Add clipscribe.ai to Cloudflare
- Configure DNS
- Enable SSL (automatic)

---

## Security Checklist

### MVP Requirements

- [ ] Force HTTPS
- [ ] Security headers (CSP, X-Frame-Options, etc.)
- [ ] No sensitive data in frontend code
- [ ] Email validation (basic spam protection)
- [ ] Rate limiting on contact form (Phase 2)

### Phase 2 Requirements

- [ ] File upload validation (type, size)
- [ ] Virus scanning on uploads
- [ ] Rate limiting on API endpoints
- [ ] CORS configuration
- [ ] API authentication

### Enterprise Requirements

- [ ] SOC 2 compliance (in progress)
- [ ] HIPAA compliance (if needed)
- [ ] Custom security questionnaires
- [ ] Penetration testing
- [ ] Audit logging

---

## Compliance Requirements

### GDPR

**MVP:**
- Privacy policy (simple)
- No tracking cookies (Plausible is cookieless)
- Email opt-in only (no spam)
- Data deletion on request

**Phase 2:**
- Automated deletion (7 days)
- Data export on request
- Processing records for compliance

### CCPA

**Requirements:**
- Privacy policy disclosure
- Data deletion on request
- No selling data (we don't anyway)

### Email Compliance

- CAN-SPAM compliant
- Physical address in emails (your choice)
- Unsubscribe mechanism (if doing newsletters)
- No misleading subject lines

---

## Maintenance Requirements

### Daily (Phase 1)

- [ ] Check trials@clipscribe.ai
- [ ] Process orders
- [ ] Respond to inquiries
- [ ] Monitor for spam

### Weekly

- [ ] Review analytics
- [ ] Check for errors
- [ ] Update GitHub samples (if new)
- [ ] Respond to GitHub issues

### Monthly

- [ ] Review pricing
- [ ] Update content (if needed)
- [ ] Check competitor landscape
- [ ] Analyze metrics

---

## Technology Constraints for Designer

### Frontend Constraints

**Must Work Without JavaScript:**
- All content visible
- Basic navigation functional
- Forms have fallback (mailto)

**Progressive Enhancement:**
- JavaScript enhances experience
- Animations are optional
- Core function works without

**Responsive Required:**
- Mobile-first approach
- Test on real devices
- Touch-friendly (44px tap targets)

### Performance Constraints

**Images:**
- Max 200KB per image
- WebP with fallback
- Lazy load below fold

**Total Page Size:**
- Landing: <500KB
- Pricing: <400KB
- Samples: <800KB (excludes downloads)

**Load Time:**
- <3 seconds on 3G
- <1.5 seconds on broadband

### Browser Support

**Must Support:**
- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

**Nice to Have:**
- IE 11 (graceful degradation)
- Older mobile browsers

---

## Development Handoff Checklist

**From Designer to Developer:**

- [ ] Figma file with all pages (desktop + mobile)
- [ ] Design system (colors, typography, components)
- [ ] Exported assets (optimized images, icons)
- [ ] Measurement specifications
- [ ] Interaction specifications
- [ ] Responsive behavior notes

**From Developer to Launch:**

- [ ] HTML/CSS implemented
- [ ] Responsive tested
- [ ] Accessibility tested
- [ ] Performance optimized
- [ ] Cross-browser tested
- [ ] Content proofread
- [ ] Analytics configured
- [ ] DNS configured
- [ ] SSL verified
- [ ] Final QA

---

## Launch Checklist

**Pre-Launch:**

- [ ] Domain configured (clipscribe.ai)
- [ ] Email routing working (trials@clipscribe.ai)
- [ ] Stripe account setup (payment links created)
- [ ] Analytics installed (Plausible)
- [ ] Sample files downloadable
- [ ] All links working
- [ ] Mobile tested on real devices
- [ ] Accessibility validated
- [ ] Performance >90 Lighthouse score
- [ ] Legal pages (Privacy, Terms)

**Launch Day:**

- [ ] Announce on Hacker News
- [ ] Post on Reddit (r/OSINT, r/datascience)
- [ ] Tweet from personal account
- [ ] GitHub release announcement
- [ ] Monitor for issues
- [ ] Respond to feedback

**Post-Launch:**

- [ ] Daily email checks
- [ ] Process orders promptly
- [ ] Collect feedback
- [ ] Fix bugs quickly
- [ ] Plan Phase 2 automation

---

## Recommended Development Partner (If Hiring)

**For Frontend Development:**
- Freelancer with HTML/CSS/JS skills
- NOT needed if designer can code
- Budget: $500-1500 for MVP

**Where to Find:**
- Upwork
- Freelancer.com
- Personal network
- Hacker News "Who's Hiring"

**What to Provide:**
- Figma designs
- Copy guidelines (this document)
- Sample files
- GitHub repo access

---

## Questions for Implementation

**Before building, decide:**

1. **Framework or plain HTML/CSS/JS?**
   - Recommendation: Plain HTML for MVP, framework later
   
2. **Designer codes or hire developer?**
   - If designer codes: Provide Figma + copy, they build
   - If hire developer: Provide Figma + copy + this doc

3. **Phase 1 or build Phase 2 immediately?**
   - Recommendation: Phase 1 MVP, validate, then automate

4. **Custom domain email or Gmail only?**
   - Recommendation: Cloudflare routing to Gmail (simplest)

---

**Document Status:** Complete  
**Next:** Assemble Complete Handoff Package  
**Purpose:** Technical constraints and stack recommendations  
**Compiled by:** AI Assistant  
**Date:** November 13, 2025

