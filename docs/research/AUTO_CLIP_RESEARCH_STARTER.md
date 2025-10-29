# Auto-Clip Algorithm Research - Week 1

**Research Lead:** User  
**Started:** October 29, 2025  
**Goal:** Understand how to automatically select and generate viral/newsworthy clips

---

## RESEARCH QUESTIONS

### 1. **How Does Opus Clip Work?**

**What to Research:**
- Visit opus.pro or opusclip.com
- How do they describe their algorithm?
- What's their "virality score"?
- Do they show what factors they consider?
- How accurate are their predictions?

**Key Questions:**
- Is it hook-based? (first 3 seconds important)
- Is it retention-based? (completion rate)
- Is it engagement-based? (likes, comments, shares)
- Do they use ML models? (trained on viral videos)

**Findings:** [TO BE FILLED IN BY YOU]

---

### 2. **What Makes a Clip "Viral"?**

**Factors to Research:**
- **Hook:** First 3 seconds capture attention
- **Retention:** Watch-through rate (% who finish)
- **Emotion:** Surprise, humor, outrage trigger shares
- **Pacing:** Quick cuts, energy level
- **Length:** TikTok sweet spot (21-34s?), YouTube Shorts (45-60s?)

**Research Sources:**
- TikTok algorithm breakdowns
- YouTube Shorts best practices
- MrBeast's clip philosophy
- Viral marketing case studies

**Findings:** [TO BE FILLED IN BY YOU]

---

### 3. **What Makes a Clip "Newsworthy"?**

**Journalism Standards:**
- **Timeliness:** Breaking news, recent events
- **Impact:** Affects many people
- **Prominence:** Important people involved
- **Proximity:** Local relevance
- **Conflict:** Controversy, debate
- **Human Interest:** Emotional stories

**For Our Use:**
- High significance scores (>0.9) = newsworthy
- Named entities (Trump, Biden, major orgs) = prominence
- Topics with high relevance (>0.9) = importance
- Negative sentiment + high significance = conflict/controversy

**Findings:** [TO BE FILLED IN BY YOU]

---

### 4. **What Makes a Clip "Info-Dense"?**

**Potential Metrics:**
- **Entities per second:** >2 entities/sec = dense information
- **Topic coverage:** Multiple topics in short time
- **Relationship complexity:** Many connections discussed
- **Evidence density:** Specific facts, numbers, quotes

**Our Advantage:**
- We extract entities with timestamps
- We identify key moments (info-dense points)
- We have evidence quotes (specific facts)

**Findings:** [TO BE FILLED IN BY YOU]

---

## PROPOSED SCORING ALGORITHM

**Multi-Objective Scoring (based on research):**

```python
def score_clip(key_moment, entities_in_clip, topics, sentiment):
    """
    Score clip potential on 3 dimensions:
    1. Newsworthy (significance, prominence, impact)
    2. Viral (emotion, hook potential, shareability)
    3. Info-dense (entities, facts, complexity)
    """
    
    # Newsworthy score (0-1)
    newsworthy = (
        key_moment['significance'] * 0.6 +  # Moment importance
        entity_prominence_score * 0.3 +      # Named people/orgs
        topic_relevance * 0.1                # Topic importance
    )
    
    # Viral score (0-1)  
    viral = (
        emotion_intensity * 0.4 +   # Strong sentiment = shareable
        hook_potential * 0.3 +      # First 3s compelling?
        controversy_score * 0.3     # Conflict/debate = engagement
    )
    
    # Info-dense score (0-1)
    info_dense = (
        entities_per_second * 0.4 +  # Information density
        evidence_count * 0.3 +        # Specific facts
        relationship_count * 0.3      # Complexity
    )
    
    # Weighted combination (customize per use case)
    final_score = (
        newsworthy * 0.4 +
        viral * 0.3 +
        info_dense * 0.3
    )
    
    return {
        'final_score': final_score,
        'newsworthy': newsworthy,
        'viral': viral,
        'info_dense': info_dense
    }
```

**Tunable Weights:**
- For journalists: Weight newsworthy higher (0.6)
- For social media: Weight viral higher (0.6)
- For analysts: Weight info-dense higher (0.6)

---

## IMPLEMENTATION NOTES

**What We Have (From Validation):**
- ✅ Key moments with significance scores
- ✅ Entities with timestamps
- ✅ Topics with relevance scores
- ✅ Sentiment (emotion proxy)
- ✅ Evidence quotes (fact density)

**What We Need to Calculate:**
- Entity prominence (is this Trump or random person?)
- Emotion intensity (strong positive/negative vs neutral)
- Hook potential (is opening compelling?)
- Controversy score (conflict, debate indicators)
- Entities per second (information density)

**Week 3 Implementation:**
- Use research findings to tune algorithm
- Implement scoring in Python
- Test on validated videos
- Compare to Opus Clip results

---

## YOUR ACTION ITEMS

**This Week:**
1. Visit opus.pro - analyze their features
2. Sign up for trial if available - test their algorithm
3. Research viral video characteristics (TikTok, YouTube)
4. Document findings in this file
5. Propose scoring weights based on research

**Deliverable:**
- Complete this document with research findings
- Proposed algorithm refinements
- Competitor comparison (our approach vs Opus)

**I'll support with:**
- Academic research on video virality
- Algorithm design
- Implementation planning

---

**Status:** RESEARCH IN PROGRESS  
**Next Update:** When you have Opus Clip findings

