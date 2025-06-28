# ClipScribe Mission Control

Interactive web interface for managing and visualizing ClipScribe video intelligence collections.

## 🚀 Quick Start

### Launch the Interface
```bash
# From the project root
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

The interface will open in your browser at `http://localhost:8501`

### Prerequisites
- ClipScribe installed with `poetry install`
- Google API key configured (`GOOGLE_API_KEY` environment variable)
- Some processed videos or collections (optional for testing)

## 📱 Interface Overview

### 🏠 Dashboard
The main landing page provides:
- **Quick Stats**: Collection and video counts in the sidebar
- **Feature Cards**: Overview of Collections and Information Flows
- **Recent Activity**: Shows your 5 most recently processed videos/collections
- **Success Banner**: Celebrates the v2.15.0 release with complete synthesis features

### 📹 Collections
Browse and manage multi-video collections:

**Overview Tab**:
- Collection metrics (videos, entities, relationships, duration)
- Collection summary with AI-generated insights

**Videos Tab**:
- Complete list of videos in each collection
- Individual video metadata and statistics

**Entities Tab**:
- Cross-video entity analysis
- Entities that appear across multiple videos
- Entity aliases and confidence scores

**Knowledge Synthesis Tab**:
- Timeline synthesis with chronological events
- Links to Information Flow Maps and Analytics
- Integration status for synthesis features



### 🔄 Information Flows
Concept evolution and learning progression:

**Overview Tab**:
- Flow statistics (concepts, paths, clusters)
- Flow pattern analysis and strategic insights

**Concept Explorer Tab**:
- Search concepts by name
- Filter by maturity level (mentioned → evolved)
- Maturity indicators with emoji visualization
- Concept dependencies

**Evolution Paths Tab**:
- Concept progression journeys
- Step-by-step maturity development
- Key dependencies for concept understanding

**Clusters Tab**:
- Thematic concept groupings
- Cluster descriptions and maturity distribution

**Video Flows Tab**:
- Per-video concept introduction/development/conclusion
- Flow breakdowns and statistics

**Visualization Tab**:
- Maturity distribution analysis
- Concept dependency mapping (simplified view)

### 📊 Analytics
Cost tracking and performance monitoring:

**Cost Overview Tab**:
- Total spending and video processing metrics
- Average cost per video calculations
- Recent processing cost history

**Performance Tab**:
- System information (Python, PyTorch, GPU status)
- Disk space monitoring
- Model cache status and sizes

**API Usage Tab**:
- Google API key status and preview
- Usage estimates and monthly projections
- Cost optimization insights

**Quality Tab**:
- Extraction quality metrics
- Entity and relationship extraction averages
- Confidence score tracking

**Optimization Tab**:
- Personalized recommendations
- Cost optimization suggestions
- System improvement advice

### ⚙️ Settings
Configuration and API management:

**API Configuration**:
- Google API key input and status
- Masked key display for security

**Processing Settings**:
- Model selection (Flash vs Pro)
- Confidence thresholds
- Cost warning thresholds

## 💡 Key Features

### 🔍 Data Integration
- **Automatic Detection**: Finds all processed videos and collections
- **JSON Loading**: Loads ClipScribe's comprehensive JSON outputs
- **Error Handling**: Graceful fallbacks when data is missing
- **Real-time Updates**: Refresh functionality to pick up new processing

### 📥 Download Options
- **JSON Exports**: Download complete analysis data
- **Markdown Summaries**: Human-readable reports
- **Collection Data**: Multi-video intelligence exports
- **Individual Panels**: Entity-specific analysis downloads

### 🎨 User Experience
- **Beautiful UI**: Gradient headers, emoji indicators, professional styling
- **Responsive Design**: Works on desktop and tablet
- **Interactive Elements**: Expandable sections, tabs, search/filter
- **Progress Feedback**: Loading spinners and success messages

### 🔐 Security
- **API Key Protection**: Masked display of sensitive keys
- **Local Processing**: All data stays on your system
- **No External Calls**: Interface only reads local ClipScribe outputs

## 🛠️ Troubleshooting

### "No collections found"
- Process some multi-video collections first:
  ```bash
  poetry run clipscribe process-collection "topic name" --urls "url1" "url2"
  ```

### "Error loading data"
- Check that JSON files are valid
- Ensure proper file permissions
- Look for error messages in the interface

### "API key not found"
- Set your environment variable:
  ```bash
  echo "GOOGLE_API_KEY=your_key_here" >> .env
  ```

### Import errors
- Ensure you're running from the project root
- Check that all dependencies are installed: `poetry install`

## 🚧 Future Enhancements (Phase 2)

### Interactive Visualizations
- Network graphs for entity relationships
- Flow diagrams for Information Maps
- Interactive charts with Plotly

### Real-time Processing
- Live progress monitoring for CLI commands
- WebSocket integration for status updates
- Queue management for batch jobs

### Advanced Analytics
- Cost trend charts
- Performance benchmarking
- Quality improvement tracking

### Export Hub
- Multiple export formats
- Sharing capabilities
- Report generation

## 🎯 Best Practices

### For Best Performance
1. **Process Related Videos**: Use collections for better insights
2. **Regular Cleanup**: Archive old outputs to keep interface fast
3. **Monitor Costs**: Use the Analytics page to track spending

### For Better Analysis
1. **Use News Content**: Better entity extraction than music videos [[memory:3676380518053530236]]
2. **Collection Types**: Choose appropriate collection types for your use case
3. **Download Reports**: Save markdown summaries for offline review

## 📞 Support

For issues or questions:
- Check the main ClipScribe documentation
- Review error messages in the interface
- Ensure ClipScribe CLI is working correctly first

---

**ClipScribe Mission Control v2.16.0 Phase 1** - Interactive video intelligence at your fingertips! 🎬✨ 