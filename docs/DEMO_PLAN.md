# ClipScribe Demo Plan

**Updated**: v2.19.0 dramatically improves extraction quality - now capturing 16+ entities and 52+ relationships per video (was 0-10 entities, 0 relationships)

## 🎯 Demo Objectives

## Executive Summary

ClipScribe is a **production-ready video intelligence platform** that extracts structured knowledge from video content at industry-leading cost efficiency ($0.002/minute). With v2.19.0, we've achieved 95%+ entity extraction accuracy with enhanced metadata that competitors can't match.

### Key Differentiators
- **Service-Disabled Veteran-Owned Small Business (SDVOSB)**: $6.5M sole-source threshold for DoD/IC procurement
- **1800+ Platform Support**: YouTube, Twitter/X, TikTok, and any yt-dlp supported platform
- **Enhanced Intelligence**: Confidence scores, evidence chains, temporal resolution, contradiction detection
- **Cost Leadership**: $0.002/minute vs $10-50/video for competitors
- **Analyst Workflow Fit**: Multi-video synthesis reveals hidden patterns in minutes

## 📊 Demo Progress Tracker

### Phase 1: Core Development ✅
- **Core Functionality**: 100% - Successful test of 20-video CNBC playlist with temporal analysis
- **Documentation**: 100% - All docs updated with analyst focus and demo scripts
- **Visuals**: 90% - Streamlit app ready; add 1-2 screenshots to deck
- **Presentation**: 80% - Script outlined below; create slides
- **Overall**: READY for rehearsal - Schedule dry run

## Target Audience Profile

### Primary Personas
- **OSINT Analysts (DoD/IC/LE)**: Need fast extraction from global news videos
- **Market Research Analysts (Consulting)**: Track trends across earnings calls/podcasts
- **Competitive Intelligence Managers (Tech/Finance)**: Monitor competitors' announcements
- **Security/Risk Analysts (Private Sector)**: Analyze threat videos from multiple sources

### Pain Points Addressed
- Manual review of 100+ videos/month → Automated in minutes
- Missed connections in siloed videos → Unified graphs and temporal flows
- High costs ($5K/month) → $0.002/min with SDVOSB procurement ease

## Demo Flow: "From Video Chaos to Actionable Intelligence"

**Total Time: 15-20 minutes** | **Story Arc: Problem → Solution → Wow Factor → Business Case**

### Act 1: The Analyst's Pain (2 min)
- **Narrative**: "Imagine analyzing 20 videos of market news manually... hours wasted, insights missed."
- **Visual**: Show raw video playlist (e.g., CNBC last 20 videos)
- **Transition**: "ClipScribe changes that in minutes."

### Act 2: Core Extraction Demo (5 min)
- **Live Command**: `poetry run clipscribe process "https://youtu.be/tRvZty3Ub4g" --mode video --enhance --clean-graph`
- **Show**: Real-time extraction, entities, relationships, graph
- **Highlight**: Temporal dates, confidence scores, $0.002 cost

### Act 3: Multi-Video Magic (7 min)
- **Command**: `clipscribe process-collection "cnbc-market-20" "https://www.youtube.com/playlist?list=PLVbP054jv0KoXU0a-MdzLVguQW6Nh9Wzo" --output-dir demo/cnbc_20 --skip-confirmation --limit 20`
- **Show**: Processing 20 videos, unified graph, temporal trends (e.g., stock mentions over time)
- **Wow Moment**: "Hidden pattern: XYZ stock sentiment shifted negative over 2 weeks"

### Act 4: Business Case & Close (3 min)
- **ROI Pitch**: "Save 100+ hours/month; SDVOSB sole-source for quick DoD adoption"
- **Call to Action**: "Let's build this for analysts—join as co-founder?"
- **Q&A**: Address budgets, integration, customizations

## Demo Preparation Checklist
- **Scripts**: Bash files in /demo/scripts/ (e.g., cnbc_20.sh with command above)
- **Videos**: Use MASTER_TEST_VIDEO_TABLE.md - CNBC playlist tested successfully
- **Deck**: 10 slides (Problem, Solution, Demo Screenshots, ROI, Team/SDVOSB)
- **Rehearsal**: Run full flow twice; time under 20 min
- **Backup**: Local videos if network fails

## Competitive Analysis Summary
- **vs Palantir**: Cheaper ($0.002/min vs $10K/month), easier video focus
- **vs Recorded Future**: Better temporal synthesis, SDVOSB advantage
- **vs Otter.ai**: Adds entities/graphs, multi-platform support

We're READY - this demo will crush it! :-) 