"""Email templates for ClipScribe trial and delivery system.

Templates for all three customer tiers with appropriate messaging and CTAs.
"""

from typing import Dict, List


def tier1_researcher_email(
    filename: str,
    entities_count: int,
    relationships_count: int,
    topics_count: int,
    cost: float,
    trial_number: int = 1,
) -> Dict[str, str]:
    """Email template for Tier 1 (Researcher) - Technical focus.

    Returns dict with 'subject', 'body_text', 'body_html'
    """
    subject = f"Your ClipScribe Results - {filename}"

    body_text = f"""Hi,

Your intelligence extraction is complete!

DATA EXTRACTED:
- {entities_count} entities with evidence quotes
- {relationships_count} relationships mapped
- {topics_count} topics with time ranges
- Processing cost: ${cost:.4f}

ATTACHED FILES:
- transcript.json (complete data structure)
- entities.csv (import to Pandas, Sheets, SQL)
- relationships.csv (subject-predicate-object structure)
- topics.csv (themes with time ranges)
- segments.csv (speaker-attributed transcript)

QUICK START (Python):
```python
import pandas as pd

# Load entities
entities = pd.read_csv('entities.csv')
print(entities[['name', 'type', 'confidence']].head())

# Load relationships
rels = pd.read_csv('relationships.csv')
print(rels[['subject', 'predicate', 'object']])
```

TRIAL STATUS:
Trial {trial_number}/3 used.

NEXT STEPS:
→ Send another file: trials@clipscribe.ai
→ Pay for unlimited: https://buy.stripe.com/researcher-tier (${25}/video)
→ Self-host FREE: github.com/bubroz/clipscribe

Questions? Reply to this email.

-Zac Forristall
ClipScribe.ai
"""

    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px;">
<h2>Your ClipScribe Results</h2>

<p><strong>File:</strong> {filename}</p>

<h3>📊 Data Extracted:</h3>
<ul>
<li><strong>{entities_count}</strong> entities with evidence quotes</li>
<li><strong>{relationships_count}</strong> relationships mapped</li>
<li><strong>{topics_count}</strong> topics with time ranges</li>
<li>Processing cost: <strong>${cost:.4f}</strong></li>
</ul>

<h3>📎 Attached Files:</h3>
<ul>
<li><code>transcript.json</code> - Complete data structure</li>
<li><code>entities.csv</code> - Import to Pandas, Sheets, SQL</li>
<li><code>relationships.csv</code> - Graph-ready format</li>
<li><code>topics.csv</code> - Themes with time ranges</li>
<li><code>segments.csv</code> - Speaker-attributed transcript</li>
</ul>

<h3>🔬 Quick Start:</h3>
<pre><code>import pandas as pd
entities = pd.read_csv('entities.csv')
print(entities[['name', 'type', 'confidence']])</code></pre>

<hr>
<p><strong>Trial {trial_number}/3 used</strong></p>

<p><strong>Next Steps:</strong></p>
<ul>
<li>Send another file: <a href="mailto:trials@clipscribe.ai">trials@clipscribe.ai</a></li>
<li>Pay for unlimited: <a href="https://buy.stripe.com/researcher">$25/video</a></li>
<li>Self-host FREE: <a href="https://github.com/bubroz/clipscribe">GitHub</a></li>
</ul>

<p>Questions? Reply to this email.</p>

<p>-Zac<br>
<a href="https://clipscribe.ai">ClipScribe.ai</a></p>
</body>
</html>"""

    return {"subject": subject, "body_text": body_text, "body_html": body_html}


def tier2_analyst_email(
    filename: str,
    entities_count: int,
    relationships_count: int,
    speakers: int,
    cost: float,
    trial_number: int = 1,
    top_entities: List[str] = None,
) -> Dict[str, str]:
    """Email template for Tier 2 (Analyst) - Professional focus with insights."""

    subject = f"Your Intelligence Report - {filename}"

    top_entities_text = "\n".join([f"  • {e}" for e in (top_entities or [])[:5]])

    body_text = f"""Hi,

Your video has been analyzed. Here are the key findings:

📊 SUMMARY:
- {entities_count} entities identified
- {relationships_count} relationships mapped
- {speakers} speakers attributed
- Processing cost: ${cost:.4f}

🎯 TOP ENTITIES:
{top_entities_text}

📎 DELIVERABLES:
- intelligence_report.docx (executive summary - edit in Docs/Word)
- entities.csv (import to Sheets/Excel)
- relationships.csv (network data)
- report.md (searchable markdown)
- transcript.json (full technical data)

💡 HOW TO USE:
1. Open intelligence_report.docx in Google Docs or Word
2. Edit for your presentation/report needs
3. Import CSVs to Sheets/Excel for analysis

Trial {trial_number}/3 used.

UPGRADE OPTIONS:
→ Unlimited processing: https://buy.stripe.com/analyst-tier (${50}/video)
→ 10-video pack: ${400} (save ${100})
→ Or send another trial: trials@clipscribe.ai

Questions? Reply anytime.

-Zac Forristall
ClipScribe Intelligence Extraction
clipscribe.ai
"""

    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px;">
<h2>Your Intelligence Report</h2>

<p><strong>File:</strong> {filename}</p>

<h3>📊 Summary:</h3>
<ul>
<li><strong>{entities_count}</strong> entities identified</li>
<li><strong>{relationships_count}</strong> relationships mapped</li>
<li><strong>{speakers}</strong> speakers attributed</li>
<li>Cost: <strong>${cost:.4f}</strong></li>
</ul>

<h3>🎯 Top Entities:</h3>
<ul>
{''.join([f'<li>{e}</li>' for e in (top_entities or [])[:5]])}
</ul>

<h3>📎 Deliverables:</h3>
<ul>
<li><strong>intelligence_report.docx</strong> - Executive summary (edit in Docs/Word)</li>
<li><strong>entities.csv</strong> - Import to Sheets/Excel</li>
<li><strong>relationships.csv</strong> - Network data</li>
<li><strong>report.md</strong> - Searchable markdown</li>
<li><strong>transcript.json</strong> - Full technical data</li>
</ul>

<h3>💡 How to Use:</h3>
<ol>
<li>Open <code>intelligence_report.docx</code> in Google Docs or Word</li>
<li>Edit for your needs (add notes, modify formatting)</li>
<li>Import CSVs to Sheets/Excel for deeper analysis</li>
</ol>

<hr>
<p><strong>Trial {trial_number}/3 used</strong></p>

<p><strong>Upgrade Options:</strong></p>
<ul>
<li><a href="https://buy.stripe.com/analyst">Unlimited: $50/video</a></li>
<li>10-video pack: $400 (save $100)</li>
<li>Send another trial: <a href="mailto:trials@clipscribe.ai">trials@clipscribe.ai</a></li>
</ul>

<p>-Zac<br>
<a href="https://clipscribe.ai">ClipScribe.ai</a></p>
</body>
</html>"""

    return {"subject": subject, "body_text": body_text, "body_html": body_html}


def tier3_executive_email(
    filename: str,
    entities_count: int,
    relationships_count: int,
    speakers: int,
    insights: List[str],
    calendly_link: str = "https://calendly.com/zforristall/clipscribe-consultation",
) -> Dict[str, str]:
    """Email template for Tier 3 (Executive) - High-level insights."""

    subject = f"Executive Intelligence Report - {filename}"

    insights_text = "\n".join([f"  • {insight}" for insight in insights[:5]])

    body_text = f"""Hi,

Your executive intelligence report is ready.

🎯 KEY INSIGHTS:
{insights_text}

📊 METRICS:
- {entities_count} entities tracked
- {relationships_count} competitive relationships
- {speakers} speakers identified

📎 DELIVERABLES:
- executive_summary.pptx (presentation-ready, 7 slides)
- intelligence_report.docx (detailed analysis, editable)
- entities.csv (sortable data)
- relationships.csv (network analysis)

💡 NEXT STEPS:
1. Review PPTX presentation (opens in Slides/PowerPoint)
2. Edit DOCX for your specific needs
3. Import CSVs for deeper analysis

📅 CONSULTATION INCLUDED:
Schedule your 30-minute analysis consultation:
{calendly_link}

We'll discuss:
- Key findings and implications
- How to use the data in your workflow
- Next steps for analysis

💰 SERIES PRICING:
For multiple video analysis:
- 10 videos: $500 (includes aggregate intelligence)
- 50 videos: $2,000 (includes trend analysis)
- 100+ videos: Custom pricing

Contact: zforristall@gmail.com

-Zac Forristall
Founder, ClipScribe Intelligence
clipscribe.ai
"""

    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px;">
<h2>Executive Intelligence Report</h2>

<h3>🎯 Key Insights:</h3>
<ul>
{''.join([f'<li>{insight}</li>' for insight in insights[:5]])}
</ul>

<h3>📊 Metrics:</h3>
<ul>
<li><strong>{entities_count}</strong> entities tracked</li>
<li><strong>{relationships_count}</strong> competitive relationships</li>
<li><strong>{speakers}</strong> speakers identified</li>
</ul>

<h3>📎 Deliverables:</h3>
<ul>
<li><strong>executive_summary.pptx</strong> - Presentation-ready (7 slides)</li>
<li><strong>intelligence_report.docx</strong> - Detailed analysis (editable)</li>
<li><strong>entities.csv</strong> - Sortable data</li>
<li><strong>relationships.csv</strong> - Network analysis</li>
</ul>

<h3>💡 How to Use:</h3>
<ol>
<li>Open PPTX in Google Slides or PowerPoint</li>
<li>Review key findings (slides 2-7)</li>
<li>Edit DOCX to add your analysis</li>
<li>Import CSVs for custom queries</li>
</ol>

<h3>📅 Your Consultation:</h3>
<p><a href="{calendly_link}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
Schedule 30-Min Analysis Call</a></p>

<p>We'll discuss findings, usage, and next steps.</p>

<hr>

<h3>💰 Series Analysis Pricing:</h3>
<ul>
<li>10 videos: $500 (aggregate intelligence)</li>
<li>50 videos: $2,000 (trend analysis)</li>
<li>100+ videos: Custom</li>
</ul>

<p>Contact: <a href="mailto:zforristall@gmail.com">zforristall@gmail.com</a></p>

<p>-Zac<br>
<a href="https://clipscribe.ai">ClipScribe.ai</a></p>
</body>
</html>"""

    return {"subject": subject, "body_text": body_text, "body_html": body_html}


def series_complete_email(
    series_name: str,
    total_videos: int,
    unique_entities: int,
    top_insights: List[str],
    total_cost: float,
) -> Dict[str, str]:
    """Email template for series analysis completion."""

    subject = f"Series Analysis Complete - {series_name}"

    insights_text = "\n".join([f"  {i+1}. {insight}" for i, insight in enumerate(top_insights[:5])])

    body_text = f"""Hi,

Your {total_videos}-video series analysis is complete.

🎯 SERIES INTELLIGENCE:
{insights_text}

📊 CORPUS METRICS:
- {unique_entities} unique entities across all videos
- {total_videos} videos processed
- Total investment: ${total_cost:.2f}

📎 COMPREHENSIVE DELIVERABLES:

AGGREGATE ANALYSIS:
- series_analysis.pptx (executive presentation, 10 slides)
- series_report.docx (comprehensive written analysis)
- entity_frequency.csv (cross-video statistics)
- relationship_network.csv (corpus-wide connections)

INDIVIDUAL REPORTS:
- One complete report per video (DOCX + CSVs)
- Speaker attribution throughout
- Evidence quotes for all extractions

📅 CONSULTATION INCLUDED:
Your 30-minute analysis consultation is included.
Schedule: https://calendly.com/zforristall/clipscribe-consultation

We'll review:
- Aggregate insights and trends
- Entity evolution across videos
- Relationship networks
- Recommendations for further analysis

💡 NEXT SERIES:
10% discount on your next corpus analysis.
Contact: zforristall@gmail.com

Thank you for choosing ClipScribe.

-Zac Forristall
Founder, ClipScribe Intelligence
clipscribe.ai
"""

    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px;">
<h2>Series Analysis Complete</h2>

<p><strong>Series:</strong> {series_name}<br>
<strong>Videos:</strong> {total_videos}<br>
<strong>Investment:</strong> ${total_cost:.2f}</p>

<h3>🎯 Key Insights:</h3>
<ol>
{''.join([f'<li>{insight}</li>' for insight in top_insights[:5]])}
</ol>

<h3>📊 Corpus Metrics:</h3>
<ul>
<li><strong>{unique_entities}</strong> unique entities</li>
<li><strong>{total_videos}</strong> videos analyzed</li>
</ul>

<h3>📎 Deliverables:</h3>

<p><strong>Aggregate Analysis:</strong></p>
<ul>
<li><code>series_analysis.pptx</code> - 10-slide presentation</li>
<li><code>series_report.docx</code> - Written analysis</li>
<li><code>entity_frequency.csv</code> - Cross-video stats</li>
<li><code>relationship_network.csv</code> - Corpus connections</li>
</ul>

<p><strong>Individual Reports:</strong></p>
<ul>
<li>Complete report per video (DOCX + CSVs)</li>
<li>All speaker-attributed</li>
<li>Evidence quotes included</li>
</ul>

<h3>📅 Your Consultation:</h3>
<p><a href="https://calendly.com/zforristall/clipscribe-consultation" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
Schedule Analysis Call (30min)</a></p>

<p>We'll review findings and recommendations.</p>

<hr>

<p><strong>Next Series:</strong> 10% discount<br>
Contact: <a href="mailto:zforristall@gmail.com">zforristall@gmail.com</a></p>

<p>-Zac<br>
<a href="https://clipscribe.ai">ClipScribe.ai</a></p>
</body>
</html>"""

    return {"subject": subject, "body_text": body_text, "body_html": body_html}
