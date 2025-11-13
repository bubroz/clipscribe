# Sitemap & Content Strategy
**ClipScribe v3.0.0 Web Presence**  
**Date:** November 13, 2025  
**Purpose:** Define site structure, content blocks, and user journeys

---

## Site Structure

```
clipscribe.ai/
├─ / (Landing Page)
├─ /pricing
├─ /samples
├─ /docs (→ links to GitHub docs)
├─ /github (→ links to repo)
├─ /contact
├─ /privacy
└─ /terms
```

**Total Pages:** 8 (5 core content pages + 3 legal pages)

---

## Page 1: Landing Page (/)

**Purpose:** Convert visitors to either "try free (GitHub)" or "buy service (email)"

**User Journey:**
1. Arrive from social/search
2. Understand what ClipScribe is (5 seconds)
3. See their use case (10 seconds)
4. Choose their path (free vs paid)
5. Take action (GitHub or email)

**Key Metrics:**
- Time to understand: <10 seconds
- Click-through to GitHub or email: >20%
- Scroll depth: >60% reach pricing preview

### Content Blocks

#### Block 1: Hero Section

**Layout:**
- Left: Headline + Subheadline + CTAs
- Right: Visual (screenshot or demo)

**Content:**

**Headline (H1):**
"Video Intelligence Extraction"

**Subheadline:**
"Extract entities, relationships, topics, and insights from videos. Run it yourself (free) or let us handle it ($25+)."

**Primary CTAs:**
- [Download Free CLI] (GitHub link, button)
- [Upload Video ($25)] (Email link, button)

**Visual:**
- Screenshot of sample output (DOCX or JSON)
- OR: Diagram showing: Video → Intelligence → Multiple Formats

**Social Proof:**
- "MIT Licensed • Open Source • No Vendor Lock-In"
- GitHub stars counter (if >100)

---

#### Block 2: Problem/Solution

**Headline (H2):**
"Replace 10 Hours of Manual Analysis with 10 Minutes"

**Content (3-column comparison):**

**Column 1: Manual Work**
- 10 hours watching + taking notes
- $500-2000 if hiring analyst
- Inconsistent quality
- Hard to query/analyze

**Column 2: Transcription Only**
- $7.50-90/hour for text
- No entities or relationships
- No structured data
- Still manual analysis

**Column 3: ClipScribe**
- 10 minutes upload → results
- $0 (self-host) or $25-50 (service)
- Structured intelligence
- Queryable data

**CTA:** "See sample outputs →"

---

#### Block 3: How It Works

**Headline (H2):**
"From Video to Intelligence in Three Steps"

**Content (3-step process):**

**Step 1: Input**
- Upload video (service)
- OR: Run CLI (self-hosted)
- Supports 1800+ platforms (yt-dlp)
- Or upload MP4/MP3

**Step 2: Processing**
- WhisperX transcription
- Speaker diarization (up to 12 speakers)
- Grok intelligence extraction
- Cost: $0.003-0.06 per video

**Step 3: Output**
- All formats delivered:
  - JSON (complete data)
  - DOCX (professional report)
  - CSV (5 files for analysis)
  - PPTX (7-slide executive deck)
  - Markdown (searchable docs)

**Visual:** Flow diagram or icons

---

#### Block 4: Output Formats

**Headline (H2):**
"Five Formats, Every Use Case"

**Content (5-column grid):**

**JSON**
- For developers
- Complete structured data
- API integration
- Import to databases

**DOCX**
- For stakeholders
- Professional reports
- Google Docs/Word/Pages
- Edit and annotate

**CSV**
- For analysis
- Excel/Sheets/Numbers
- Pandas/SQL import
- Pivot tables

**PPTX**
- For executives
- 7-slide deck
- Slides/PowerPoint/Keynote
- Presentations

**Markdown**
- For documentation
- GitHub-flavored
- VS Code/Obsidian
- Version control

**CTA:** "Download sample outputs →"

---

#### Block 5: Sample Outputs Preview

**Headline (H2):**
"See Real Examples - No Sanitization, No Cherry-Picking"

**Content (3-card grid):**

**Card 1: Multi-Speaker Panel (36min)**
- 12 speakers detected
- 45 entities extracted
- 11 relationships mapped
- 5 topics identified
- All formats: [Download]

**Card 2: Business Interview (30min)**
- 2 speakers
- 17 entities (executives, companies)
- 10 relationships
- Competitive intelligence
- All formats: [Download]

**Card 3: Technical Presentation (16min)**
- 1 speaker
- 20 entities (medical terms)
- 6 relationships
- Single-speaker format
- All formats: [Download]

**CTA:** "See all samples →" (links to /samples)

---

#### Block 6: Open Source + Paid Service

**Headline (H2):**
"Run It Yourself (Free) or Let Us Handle It (Paid)"

**Content (2-column comparison):**

**Open Source (Free)**
- Download from GitHub
- MIT License (use anywhere)
- Full CLI access
- Bring your own API keys
- Community support
- Unlimited usage
- **[Get Started (GitHub)] →**

**Managed Service (Paid)**
- Upload via email
- No setup required
- All formats delivered
- 24-72 hour turnaround
- $25-500 based on volume
- **[Upload Video ($25)] →**

**Quote:** "90%+ of companies use self-hosted for free. That's fine - we built this to be useful." - Zac, Founder

---

#### Block 7: Pricing Preview

**Headline (H2):**
"Transparent Pricing - Free to Enterprise"

**Content (4-tier quick preview):**

**Free**
- Self-hosted (MIT)
- $0 forever
- Unlimited usage
- [GitHub →]

**Single Video**
- $25-50/video
- All formats
- 24-48hr
- [Pricing →]

**Series (5-20 videos)**
- $200-500
- Cross-video intel
- 48-72hr
- [Pricing →]

**Enterprise**
- Custom
- API access
- White-glove
- [Contact →]

**CTA:** "See full pricing →" (links to /pricing)

---

#### Block 8: Trust Signals

**Headline (H3):**
"Built in the Open, Designed to Last"

**Content (3-column trust signals):**

**Open Source**
- MIT License
- Full source on GitHub
- No vendor lock-in
- See how it works

**Proven Technology**
- WhisperX (open source)
- Grok (xAI)
- WhisperX (local option)
- Production-tested

**Honest Business**
- Transparent costs
- No hidden fees
- Sustainable margins
- No VC pressure

---

#### Block 9: Final CTA

**Headline (H2):**
"Start Extracting Intelligence from Videos"

**Content:**

**Subheadline:**
"Choose your path: Free open-source tool or managed service."

**CTAs (side-by-side):**
- [Download Free CLI (GitHub)] - Large button
- [Upload Video ($25)] - Large button

**Below CTAs:**
- "No credit card required for free tier"
- "Email delivery within 24-48 hours for paid"

---

#### Block 10: Footer

**Content (4-column):**

**Column 1: Product**
- Pricing
- Samples
- Documentation (GitHub link)
- GitHub Repository

**Column 2: Company**
- Contact
- Privacy Policy
- Terms of Service
- Status (if we add uptime monitoring)

**Column 3: Resources**
- GitHub Issues (Support)
- Sample Outputs
- CLI Documentation
- API Documentation (future)

**Column 4: Connect**
- trials@clipscribe.ai
- GitHub (@bubroz/clipscribe)
- Twitter/X (if created)
- Built by Zac Forristall

---

## Page 2: Pricing (/pricing)

**Purpose:** Clearly explain all tiers, convert to appropriate tier

**User Journey:**
1. Understand tier differences
2. Find their use case
3. See exact pricing
4. Read FAQ to address concerns
5. Choose tier and take action

### Content Blocks

#### Block 1: Pricing Hero

**Headline (H1):**
"Transparent Pricing - Free to Enterprise"

**Subheadline:**
"Pay only for what you need. No subscription. No hidden fees. Honest margins."

**Annual/Monthly Toggle:** N/A (we're pay-per-video, not subscription)

**Social Proof:**
- "641 people downloaded this week"
- GitHub stars counter

---

#### Block 2: Tier Comparison Table

**4-Column Table:**

|  | Free | Single Video | Series | Enterprise |
|--|------|--------------|--------|------------|
| **Price** | $0 | $25-50 | $200-500 | Custom |
| **Videos** | Unlimited | 1 | 5-20 | 20+ |
| **Turnaround** | Instant | 24-48hr | 48-72hr | 4-24hr |
| **Setup** | CLI + API keys | None | None | Custom |
| **Formats** | All (self-gen) | All | All | All + custom |
| **Cross-video** | Manual | No | Yes | Yes |
| **Support** | Community | Email | Email | Dedicated |
| **API Access** | CLI only | No | No | Yes |
| **SLA** | None | None | None | Custom |
| **CTA** | [GitHub] | [Upload] | [Upload] | [Contact] |

**"LAUNCH PRICING" badge on Series tier**

---

#### Block 3: Detailed Tier Breakdowns

**Free Tier (Expandable Section):**

**"Run It Yourself - Complete Control, Zero Cost"**

**What You Get:**
- MIT licensed CLI from GitHub
- Full source code access
- All features (no limits)
- Comprehensive documentation
- Community support (GitHub Issues)
- Unlimited video processing

**What You Need:**
- Technical skills (command line)
- Python 3.12+ environment
- API keys (Grok $20/month, Gemini free/paid)
- Your time to set up

**Your Total Cost:**
- ClipScribe: $0
- API costs: ~$0.003-0.06/video
- Setup time: 30-60 minutes

**[Get Started on GitHub →]**

---

**Single Video Tier:**

**"Upload Once, Get Results - No Setup Required"**

**Pricing:**
- Up to 30min: $25
- 30-60min: $50
- Payment via Stripe link (emailed)

**What You Get:**
- Upload 1 video (email or form)
- Full intelligence extraction
- All 5 formats (JSON, DOCX, CSV, PPTX, Markdown)
- 24-48 hour turnaround
- Email delivery
- Basic email support

**Perfect For:**
- Journalists analyzing interviews
- Researchers with occasional needs
- Small businesses
- One-off projects

**ROI:**
- Replaces: 5-10 hours manual work
- Analyst cost: $500-2000
- Your cost: $25-50
- Savings: ~95%

**[Upload Video →]** (links to /contact with "Single Video" pre-filled)

---

**Series Tier (with "LAUNCH PRICING" badge):**

**"Analyze Entire Video Series - Cross-Video Intelligence"**

**Launch Pricing (Limited Time):**
- 5-10 videos: $200
- 11-15 videos: $350
- 16-20 videos: $500

*"Competitors limit to 3-5 videos. We're being generous while building our reputation. Lock in launch pricing now."*

**What You Get:**
- All Single Video features per video
- PLUS cross-video intelligence:
  - Entity frequency tracking
  - Relationship patterns across videos
  - Topic evolution analysis
  - Aggregate series report (PPTX + DOCX)
- 48-72 hour turnaround
- Priority email support

**Perfect For:**
- Market researchers analyzing campaigns
- Journalists investigating series
- Academic researchers
- Content analysis projects

**[Request Series Analysis →]** (links to /contact with "Series" pre-filled)

---

**Enterprise Tier:**

**"Scale Intelligence Extraction - API, Integration, White-Glove"**

**Starting at $1000/month**

**What You Get:**
- High volume (20+ videos or ongoing)
- API access to managed service
- Custom integrations (CRM, webhooks)
- Faster turnaround (4-24 hours)
- Dedicated support (Slack/Teams)
- SLA guarantees
- SOC 2, HIPAA available
- White-label options

**Perfect For:**
- Law firms (deposition analysis)
- Consulting firms
- Media companies
- Government/Defense
- Enterprise research

**[Schedule Consultation →]** (Calendly link or email)

---

#### Block 4: Pricing Philosophy

**Headline (H2):**
"Why We Price This Way"

**Content (4 subsections):**

**1. Free Tier is Really Free**
- MIT licensed (use commercially)
- No time limits, no feature limits
- Not a trial, not bait-and-switch
- Builds community and trust
- 90%+ of users stay free (that's fine!)

**2. Paid Tiers Add Real Value**
- Convenience (no setup)
- Speed (fast turnaround)
- Support (email, consultation)
- Service, not just software

**3. Transparent About Margins**
- Processing cost: $0.003-0.06/video
- Service price: $25-500
- Margin: 99%+ (we're honest about this)
- You pay for convenience + expertise

**4. No Subscription Lock-In**
- Pay per video as needed
- No monthly fees
- No wasted spend
- Use when you need it

---

#### Block 5: FAQ

**Headline (H2):**
"Frequently Asked Questions"

**Questions (expandable):**

**How does the free tier work?**
> Download the open-source CLI from GitHub (MIT license). You'll need Python 3.12+ and API keys for Grok and Gemini. Follow our documentation to set up and run. No limits, no time restrictions, use it commercially - it's truly free.

**What video formats are supported?**
> Any format supported by yt-dlp (1800+ platforms including YouTube, Vimeo, TikTok) or direct MP4/MP3/WebM uploads. For managed service, send us a link or upload file.

**What's the turnaround time?**
> Single videos: 24-48 hours. Series: 48-72 hours. Enterprise: 4-24 hours based on agreement. Self-hosted is instant (as fast as your processing).

**Can I get a refund?**
> Yes. If you're unhappy with the output quality or we miss our turnaround commitment, we'll refund 100%. Just email trials@clipscribe.ai within 7 days.

**Do you offer discounts?**
> Yes for non-profits, academic researchers, and journalism organizations. Email trials@clipscribe.ai with details about your organization.

**How accurate is the extraction?**
> Intelligence extraction is powered by Grok (xAI) with evidence-based responses. Every entity and relationship includes source quotes from the transcript. We've validated outputs across hundreds of videos.

**Can I see examples before buying?**
> Absolutely! Check our [Samples page](/samples) for real outputs (DOCX, CSV, PPTX, Markdown, JSON) from 3 different video types. Download and inspect before deciding.

**What happens to my video after processing?**
> For paid service: We delete your video and intermediate files within 7 days of delivery. We never use your content for training or any other purpose. See our [Privacy Policy](/privacy).

**Why is launch pricing limited?**
> We're being extra generous (5-20 videos vs competitors' 3-5) while building our reputation. As we scale, we may adjust pricing. Lock in current rates by processing now.

**Do you have an API?**
> Enterprise customers get API access. Free/paid tiers use email/upload for now. API access for all tiers is on our roadmap for Q1 2026.

---

#### Block 6: Final CTA

**Headline (H2):**
"Ready to Extract Intelligence from Videos?"

**CTAs:**
- [Download Free CLI]
- [Upload Video ($25)]
- [Schedule Enterprise Demo]

---

## Page 3: Samples (/samples)

**Purpose:** Show quality, build trust, demonstrate value

**User Journey:**
1. See what outputs look like
2. Download and inspect real files
3. Gain confidence in quality
4. Return to pricing to buy

### Content Blocks

#### Block 1: Samples Hero

**Headline (H1):**
"Real Sample Outputs - Download and Inspect"

**Subheadline:**
"These are actual ClipScribe outputs from production processing. No sanitization, no cherry-picking. This is exactly what you get."

**Stats:**
- 3 sample videos processed
- 24 files across 5 formats
- 1.4MB total (JSON is verbose!)

---

#### Block 2: Sample Grid (3 samples)

**Each Sample Card:**

**Card Header:**
- Sample name (e.g., "Multi-Speaker Panel")
- Duration, speakers, entities count
- Use case tag

**Card Body:**
- Video metadata:
  - Duration: 36 min
  - Speakers: 12 detected
  - Entities: 45 extracted
  - Relationships: 11 mapped
  - Topics: 5 identified
  - Cost: $0.003 (self-hosted)
- Available formats with file sizes:
  - JSON (1.1MB)
  - DOCX (39KB)
  - CSV (5 files, 42KB)
  - PPTX (34KB)
  - Markdown (6.1KB)

**Card Footer:**
- [Download All Formats] button
- [View Individual Files] expandable

**Visual:**
- Screenshot previews of DOCX/PPTX
- Or file icons with formats

---

**Sample 1: Multi-Speaker Panel (36min)**
- Source: News panel discussion
- Speakers: 12
- Entities: 45 (President Trump, Marjorie Taylor Greene, Mike Johnson, etc.)
- Use case: Political intelligence, news monitoring
- All formats available

**Sample 2: Business Interview (30min)**
- Source: Executive interview (Palantir CEO)
- Speakers: 2
- Entities: 17 (Alex Karp, Palantir, Ukraine, ICE, etc.)
- Use case: Competitive intelligence, market research
- All formats available

**Sample 3: Technical Presentation (16min)**
- Source: Medical presentation
- Speakers: 1
- Entities: 20 (medical terms, procedures, organizations)
- Use case: Technical documentation, educational content
- All formats available

---

#### Block 3: Format Details

**Headline (H2):**
"What's in Each Format?"

**Content (5 expandable sections):**

**JSON (Complete Data)**
- Every entity with evidence quotes
- All relationships with confidence scores
- Topics with time ranges
- Key moments with timestamps
- Speaker-attributed transcript
- Processing metadata
- Use for: APIs, databases, custom processing

**DOCX (Professional Reports)**
- Executive summary
- Entities table (top 20)
- Relationships with evidence
- Topics analysis
- Key moments timeline
- Sentiment breakdown
- Use for: Stakeholder reports, editing, annotations

**CSV (Data Analysis)**
- 5 separate files:
  - entities.csv (all entities)
  - relationships.csv (all relationships)
  - topics.csv (topics with metadata)
  - key_moments.csv (timeline)
  - segments.csv (full transcript)
- UTF-8 with BOM (Excel-friendly)
- Use for: Excel, Sheets, Pandas, SQL import

**PPTX (Executive Presentations)**
- 7-slide deck:
  1. Title
  2. Executive summary
  3. Key entities
  4. Relationships
  5. Topics & timeline
  6. Key moments
  7. Sentiment
- Use for: Presentations, briefings, stakeholders

**Markdown (Documentation)**
- GitHub-flavored markdown
- Tables for entities/topics
- Blockquotes for evidence
- Clean heading hierarchy
- Use for: GitHub, VS Code, Obsidian, version control

---

#### Block 4: How to Use These Samples

**Headline (H2):**
"Inspect Before You Decide"

**Content (3-column guide):**

**View in Apps:**
- DOCX: Upload to Google Docs
- CSV: Open in Excel/Sheets
- PPTX: Upload to Slides
- Markdown: View in VS Code
- JSON: Any text editor

**Import to Tools:**
- Pandas: `pd.read_csv('entities.csv')`
- SQL: Import CSV to database
- Excel: Power Query
- R: read.csv()
- Notion: Import CSV

**Validate Quality:**
- Check evidence quotes (real transcripts)
- Verify entity names (specific, not generic)
- Inspect relationships (make sense?)
- Review timestamps (accurate?)
- Assess completeness (thorough?)

---

#### Block 5: CTA

**Headline (H2):**
"Seen Enough? Process Your Own Video"

**CTAs:**
- [Download Free CLI]
- [Upload Video ($25)]

---

## Page 4: Contact (/contact)

**Purpose:** Collect service inquiries, route to appropriate tier

**Content:**

**Headline (H1):**
"Get Started with ClipScribe"

**Subheadline:**
"Choose how you want to get started:"

**Option 1: Free (Self-Hosted)**
- [Go to GitHub →]
- Documentation and examples included
- Community support via GitHub Issues

**Option 2: Single Video ($25-50)**
- Email: trials@clipscribe.ai
- Subject: "Single Video Processing"
- Include:
  - Video link or file
  - Any special requirements
  - You'll receive Stripe payment link

**Option 3: Series Analysis ($200-500)**
- Email: trials@clipscribe.ai
- Subject: "Series Analysis"
- Include:
  - Number of videos
  - Video links or files
  - Analysis goals
  - You'll receive custom quote

**Option 4: Enterprise**
- Email: trials@clipscribe.ai
- OR: [Schedule Consultation] (Calendly)
- Subject: "Enterprise Inquiry"
- Include:
  - Company name
  - Use case
  - Estimated volume
  - Integration needs

**Response Time:**
- Expect reply within 24-48 hours
- Automated acknowledgment immediately

---

## Page 5: Privacy Policy (/privacy)

**Purpose:** Legal compliance, build trust

**Content (Simple, Honest Language):**

**Headline (H1):**
"Privacy Policy"

**Last Updated:** [Date]

**Summary (TL;DR):**
- We process videos, we don't store them long-term
- Paid service: Videos deleted within 7 days of delivery
- Self-hosted: Your data never touches our servers
- No analytics tracking beyond basics (Plausible, privacy-friendly)
- No selling data, no training on your content

**Sections:**

**1. What We Collect**
- Email address (for paid service delivery)
- Video files (temporarily for processing)
- Payment info (via Stripe, we don't store cards)
- Basic analytics (page views, no personal data)

**2. How We Use It**
- Process your video
- Deliver results
- Provide support
- Improve the service

**3. How Long We Keep It**
- Videos: Deleted within 7 days
- Results: You download, we don't keep copies
- Emails: Indefinitely (for support history)
- Analytics: 90 days

**4. Who We Share With**
- Nobody (except payment processor Stripe)
- No third-party analytics
- No advertising networks
- No data brokers

**5. Your Rights**
- Request data deletion
- Export your data
- Opt out of emails
- See what we have

**6. Self-Hosted**
- Your data never touches our servers
- You control everything
- We can't access it

**Contact:**
trials@clipscribe.ai

---

## Page 6: Terms of Service (/terms)

**Purpose:** Legal protection, set expectations

**Content (Simple Language):**

**Headline (H1):**
"Terms of Service"

**Last Updated:** [Date]

**Summary:**
- Service provided as-is
- You own your data
- We can refuse service
- Refunds available if unhappy

**Sections:**

**1. Service Description**
- Video intelligence extraction
- Multiple output formats
- Turnaround times are estimates

**2. Your Responsibilities**
- You own/have rights to videos
- No illegal content
- Accurate contact information

**3. Our Responsibilities**
- Process your video
- Deliver in agreed format
- Protect your data
- Provide support

**4. Payment**
- Pay before processing
- Refunds within 7 days if unhappy
- No recurring charges

**5. Limitations**
- No guarantee of 100% accuracy
- AI may make mistakes
- You should verify results

**6. Termination**
- We can refuse service
- You can cancel anytime
- Self-hosted unaffected

**Contact:**
trials@clipscribe.ai

---

## User Journeys

### Journey 1: Technical Researcher (Free Tier)

1. **Arrives:** Google search "open source video intelligence"
2. **Lands:** Homepage, reads hero
3. **Scrolls:** Sees "Open Source + Paid" section
4. **Clicks:** "Download Free CLI"
5. **Goes to:** GitHub, reads docs
6. **Downloads:** Clones repo, follows setup
7. **Becomes:** Active user, maybe contributor

**Conversion:** GitHub star, maybe paid upgrade later

---

### Journey 2: Journalist (Paid Single Video)

1. **Arrives:** Twitter/X post with sample output
2. **Lands:** Homepage
3. **Thinks:** "I need this for my investigation"
4. **Clicks:** "See sample outputs"
5. **Downloads:** DOCX sample, inspects quality
6. **Convinced:** Quality is good
7. **Clicks:** "Upload Video ($25)"
8. **Emails:** trials@clipscribe.ai with video link
9. **Receives:** Stripe payment link
10. **Pays:** $25
11. **Waits:** 24-48 hours
12. **Receives:** All formats via email

**Conversion:** Paid customer, possible repeat

---

### Journey 3: Research Firm (Enterprise)

1. **Arrives:** LinkedIn post or referral
2. **Lands:** Pricing page
3. **Reads:** Enterprise tier details
4. **Clicks:** "Schedule Consultation"
5. **Books:** Calendly call
6. **Call:** Discusses volume, needs, integration
7. **Receives:** Custom quote
8. **Negotiates:** Contract terms
9. **Signs:** Agreement
10. **Integrates:** API access, starts using

**Conversion:** Enterprise customer, ongoing

---

## Conversion Strategy

### Primary Conversions

**Free → Free (GitHub Star):**
- Goal: 1000+ stars in 6 months
- Build community
- Get feedback
- Possible paid upgrade later

**Unknown → Paid (Single Video):**
- Goal: 5-10 customers/month initially
- Show samples
- Make it easy (email)
- Deliver quality

**Paid → Repeat:**
- Goal: 30% repeat rate
- Deliver great results
- Fast turnaround
- Easy process

**Paid → Enterprise:**
- Goal: 2-3 enterprise deals in 12 months
- Identify high-volume users
- Proactive outreach
- Custom solutions

### Secondary Conversions

**Landing → Samples:**
- Build trust
- Show quality
- Reduce uncertainty

**Samples → Pricing:**
- Convinced of quality
- Ready to buy
- Understand options

**Pricing → Contact:**
- Chosen tier
- Ready to pay
- Have questions

---

## Content Tone & Voice

**Throughout Site:**

**Be Direct:**
- "Extract entities and relationships" (not "unlock insights")
- "$25 for processing that costs us $0.05" (not "affordable pricing")

**Be Honest:**
- "99%+ margin - that's running a service business"
- "90%+ of users stay free forever - that's fine"

**Be Confident:**
- "This is what ClipScribe delivers" (with samples)
- "Replace 10 hours with 10 minutes"

**Be Technical:**
- "WhisperX + Grok"
- "Speaker diarization with WhisperX"

**No Bullshit:**
- Show real samples
- Exact pricing
- Actual costs
- Honest limitations

---

## Next Steps

1. **Build wireframes** for these pages (next document)
2. **Write actual copy** (copy guidelines document)
3. **Design in Figma** (wireframes → hi-fi)
4. **Build in code** (HTML/CSS or framework)
5. **Deploy** (Cloudflare Pages)

---

**Document Status:** Complete  
**Next Document:** 04_figma_wireframes.md (creation notes) + actual Figma file  
**Compiled by:** AI Assistant  
**Date:** November 13, 2025

