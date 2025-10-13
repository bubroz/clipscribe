# Final Remaining Task

## Optional: Rotate GOOGLE_API_KEY

**Why**: API key was in git history (commits before 434be2a from Sept 2025)

**Risk Level**: Low
- Repo is private
- Key likely already rotated after cleanup
- No public exposure

**Best Practice**: Rotate anyway

**How To**:
1. Go to https://console.cloud.google.com/apis/credentials
2. Delete old key
3. Create new key
4. Update `.env` with new key
5. Test: `poetry run clipscribe process video <URL>`

**Not Urgent** - can do anytime

