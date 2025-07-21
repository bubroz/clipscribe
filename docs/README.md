# ClipScribe Documentation Hub

Welcome to ClipScribe - Transform video content into structured knowledge! 🚀

## 🎯 Quick Links by User Type

### New Users
- [**Getting Started Guide**](GETTING_STARTED.md) - Install and run your first extraction
- [**CLI Reference**](CLI_REFERENCE.md) - All commands and options
- [**Supported Platforms**](PLATFORMS.md) - 1800+ video sites supported

### Regular Users  
- [**Output Formats**](OUTPUT_FORMATS.md) - JSON, CSV, Excel, GEXF explained
- [**Visualizing Knowledge Graphs**](VISUALIZING_GRAPHS.md) - Gephi, Obsidian, and more
- [**Troubleshooting Guide**](TROUBLESHOOTING.md) - Common issues and solutions

### Power Users
- [**Cost Analysis**](COST_ANALYSIS.md) - Optimize API costs
- [**Advanced Guides**](advanced/) - Vertex AI, architecture, development

## 📋 Common Tasks

| I want to... | Go here |
|-------------|----------|
| Extract knowledge from a YouTube video | [Getting Started](GETTING_STARTED.md#basic-usage) |
| Process multiple videos | [CLI Reference - Collections](CLI_REFERENCE.md#process-collection) |
| Use with Obsidian | [Visualizing Graphs](VISUALIZING_GRAPHS.md#obsidian-integration) |
| Reduce costs | [Cost Analysis](COST_ANALYSIS.md) |
| Deploy to production | [Deployment Guide](advanced/DEPLOYMENT_GUIDE.md) |

## 🏗️ Advanced Topics

- [**Vertex AI Integration**](advanced/VERTEX_AI_GUIDE.md) - Enterprise-scale processing
- [**Deployment Guide**](advanced/DEPLOYMENT_GUIDE.md) - Deploy to Streamlit Cloud or Google Cloud Run
- [**Architecture Overview**](advanced/architecture/) - System design and components
- [**Development Setup**](advanced/DEVELOPMENT.md) - Contributing to ClipScribe
- [**Testing Guide**](advanced/testing/) - Comprehensive test suite

## 📚 Quick Examples

### Basic Video Processing
```bash
clipscribe process "https://youtube.com/watch?v=..."
```

### Batch Processing with Cost Control
```bash
clipscribe process-collection videos.txt \
  --max-cost 5.00 \
  --output-format all
```

### Research Mode (Web + Video)
```bash
clipscribe research "quantum computing" \
  --max-results 5 \
  --include-web
```

## 🔍 Looking for Something Specific?

Use the search function in your editor or browser to find topics across all documentation files. Common search terms:

- **API keys** → [Getting Started](GETTING_STARTED.md#prerequisites)
- **Error messages** → [Troubleshooting](TROUBLESHOOTING.md)
- **File formats** → [Output Formats](OUTPUT_FORMATS.md)
- **Costs** → [Cost Analysis](COST_ANALYSIS.md)

---

*Need help? Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or file an issue on GitHub!* 