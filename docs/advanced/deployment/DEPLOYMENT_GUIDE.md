# 🚀 ClipScribe Deployment Guide

## 📋 Deployment Options Overview

| Option | Best For | Setup Time | Cost | Pros | Cons |
|--------|----------|------------|------|------|------|
| **Streamlit Cloud** | Quick demos | 5 min | Free | Zero config, instant sharing | Limited resources |
| **Railway** | Production-ready | 10 min | $5-20/mo | Scalable, custom domains | Requires credit card |
| **Heroku** | Traditional hosting | 15 min | $7-25/mo | Well-documented, addons | Slower cold starts |
| **DigitalOcean App Platform** | Custom control | 20 min | $12-50/mo | More control, better performance | More complex setup |

## 🎯 Recommended: Streamlit Cloud (Fastest Demo)

### Prerequisites
- GitHub account  
- FREE Google API key (get at https://makersuite.google.com/app/apikey)
- ClipScribe repository pushed to GitHub

### Step 1: Prepare Repository
```bash
# Ensure your repo is clean and pushed
git add .
git commit -m "feat: prepare for deployment"
git push origin main
```

### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your `clipscribe` repository
5. Set:
   - **Main file path**: `app.py`
   - **Python version**: `3.11`

### Step 3: Configure Secrets
In Streamlit Cloud dashboard:
1. Go to your app settings
2. Click "Secrets"
3. Add:
```toml
GOOGLE_API_KEY = "your_actual_api_key_here"

# Optional: Cost Controls
COST_WARNING_THRESHOLD=1.0
```

### Step 4: Test Deployment
- Your app will be available at: `https://your-app-name.streamlit.app`
- Test with the demo data first
- Try processing a real video

## 🛠️ Alternative: Railway (Production-Ready)

### Step 1: Install Railway CLI
```bash
# macOS
brew install railway

# Or via npm
npm install -g @railway/cli
```

### Step 2: Prepare for Railway
Create `railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run streamlit_app/ClipScribe_Mission_Control.py --server.port $PORT --server.address 0.0.0.0"

[env]
PYTHONPATH = "/app/src"
```

Create `Procfile`:
```
web: streamlit run streamlit_app/ClipScribe_Mission_Control.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

### Step 3: Deploy
```bash
# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set GOOGLE_API_KEY="your_key_here"
railway variables set PYTHONPATH="/app/src"
```

## 🐳 Docker Deployment (Any Platform)

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app/ClipScribe_Mission_Control.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

### Deploy with Docker
```bash
# Build image
docker build -t clipscribe .

# Run locally
docker run -p 8501:8501 -e GOOGLE_API_KEY="your_key" clipscribe

# Or deploy to any container platform
```

## 🔧 Environment Configuration

### Required Environment Variables
Create a `.env` file in your project root:
```bash
# Essential
GOOGLE_API_KEY=AIza...

# Optional Performance Tuning
CLIPSCRIBE_LOG_LEVEL=INFO

# Optional Cost Controls
COST_WARNING_THRESHOLD=1.0
```

### Platform-Specific Settings

#### Streamlit Cloud
- Memory limit: 1GB
- CPU: Shared
- Best for: Demos, light usage

#### Railway
- Memory: 512MB-8GB
- CPU: Shared to dedicated
- Best for: Production usage

#### Heroku
- Memory: 512MB-14GB
- CPU: Shared to dedicated
- Best for: Traditional web apps

## 📊 Performance Optimization

### For Low-Memory Environments (< 1GB)
```python
# In app.py, add these optimizations:
import streamlit as st

# Cache model loading
@st.cache_resource
def load_models():
    # Your model loading code
    pass

# Limit concurrent processing
MAX_CONCURRENT_VIDEOS = 1
```

### For Production Environments
```python
# Enable all optimizations
ENABLE_CACHING = True
MAX_BATCH_SIZE = 10
PERFORMANCE_MONITORING = True
```

## 🔒 Security Best Practices

### API Key Management
- ✅ Use .env files, never export in shell
- ✅ Add .env to .gitignore (already done in ClipScribe)
- ✅ Rotate keys regularly
- ✅ Monitor usage in Google Cloud Console
- ❌ Never use export GOOGLE_API_KEY in documentation
- ❌ Never commit keys to version control

### Access Control
```python
# Add basic authentication (optional)
import streamlit_authenticator as stauth

# Configure in app.py
authenticator = stauth.Authenticate(
    credentials,
    'clipscribe_auth',
    'auth_key',
    cookie_expiry_days=30
)
```

## 📈 Monitoring & Analytics

### Basic Monitoring
```python
# Add to app.py
import logging

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Advanced Monitoring
- **Streamlit Cloud**: Built-in analytics
- **Railway**: Built-in metrics dashboard
- **Custom**: Add Google Analytics or Plausible

## 🚨 Troubleshooting Deployment

### Common Issues

#### Memory Errors
```bash
# Reduce model size
export GLINER_MODEL="urchade/gliner_small"

# Or disable heavy models
export DISABLE_REBEL="true"
```

#### Slow Cold Starts
```python
# Pre-load models in app.py
@st.cache_resource
def preload_models():
    from clipscribe.extractors.model_manager import ModelManager
    ModelManager.get_instance()
```

#### Build Failures
```bash
# Clear Poetry cache
poetry cache clear . --all

# Or use pip requirements
poetry export -f requirements.txt --output requirements.txt
```

### Platform-Specific Issues

#### Streamlit Cloud
- **Issue**: App sleeping after inactivity
- **Solution**: Use Streamlit's built-in pinging

#### Railway
- **Issue**: Build timeouts
- **Solution**: Increase build timeout in railway.toml

#### Heroku
- **Issue**: Slug size too large
- **Solution**: Use .slugignore to exclude unnecessary files

## 📱 Mobile Optimization

### Responsive Design
The Streamlit interface is automatically mobile-responsive, but for better UX:

```python
# Add mobile-friendly styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)
```

## 🎯 Demo-Ready Deployment Checklist

### Before Sharing with Colleagues:
- [ ] App loads without errors
- [ ] Demo data works (run `poetry run python demo.py`)
- [ ] Live video processing works with API key
- [ ] All visualizations render correctly
- [ ] Export functions work (Excel, CSV, Markdown)
- [ ] Performance dashboard shows data
- [ ] Mobile interface is usable
- [ ] Error handling is graceful

### Demo Script for Colleagues:
```markdown
# ClipScribe Demo

1. **Visit**: https://your-app-name.streamlit.app
2. **Try Demo Data**: Upload files from demo_output/
3. **Process Live Video**: Use "PBS NewsHour" search
4. **Explore Features**: 
   - Real-time progress tracking
   - Interactive visualizations
   - Multi-format exports
   - Performance analytics
```

## 🔄 Continuous Deployment

### GitHub Actions (Optional)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

---

## 🎉 Quick Start Commands

### Streamlit Cloud (Recommended)
1. Push to GitHub
2. Connect at share.streamlit.io
3. Add GOOGLE_API_KEY to secrets
4. Share the URL!

### Local Testing
```bash
# Test deployment locally
poetry install

# Create .env file (SECURE)
echo "GOOGLE_API_KEY=your_key" > .env

# Test the app
streamlit run streamlit_app/ClipScribe_Mission_Control.py

# Test with demo data
poetry run python demo.py
```

### Production Deployment
```bash
# Railway
railway init && railway up

# Docker
docker build -t clipscribe . && docker run -p 8501:8501 clipscribe
```

**Ready to demo!** 🚀 

# Add enterprise option
## Kubernetes Deployment
For thousands of users 