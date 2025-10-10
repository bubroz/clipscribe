# Tweet Style Learning System

## Vision

**Phase 1**: 3 generic styles (Analyst, Alarm, Educator)

**Phase 2**: Learn from successful accounts
- Scrape accounts user admires
- Analyze top-performing tweets (>X likes)
- Extract style patterns
- Generate in that learned style

## Accounts to Research (User Suggested):

1. **@eigenrobot** - Need to verify handle
2. **@powerbottomdad** - Need to verify handle
3. **@BillAckman** - Verified, known account
4. **@balajis** - Verified, tech/crypto
5. **@elonmusk** - Verified, but style might be too unique

## Pattern Extraction

For each account, extract:
- Average tweet length
- Opener patterns ("Let me explain:", "Interesting:", one-word, etc.)
- Structure (numbered lists, bullets, paragraphs)
- Question usage (%, position, type)
- Tone (analytical, provocative, casual, formal)
- Entity density (how many names per tweet)
- Use of punctuation (!!, ?, em-dashes)

## Auto-Matching

Match style to content:
- Military/Defense → Direct, tactical style
- Politics/Policy → Analytical, wonk style
- Local government → Accessible, community style
- Breaking news → Urgent, alarm style

## Performance Tracking

Track which styles perform:
- Likes per style
- Replies per style
- Engagement rate
- Time-to-engage metrics

Auto-recommend best style per content type.

## Implementation Later

Not building now, but architecture:
```python
class StyleLearner:
    def scrape_account(handle, min_likes)
    def analyze_patterns(tweets)
    def generate_with_style(summary, entities, style)
    def track_performance(tweet_id, style, metrics)
    def recommend_style(video_metadata)
```

---

**For now**: 3 generic styles to validate the multi-style UX works.
**Later**: Build the learning system when user provides style database.
