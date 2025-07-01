# ClipScribe Feature Roadmap & Ideas

*Last Updated: July 1, 2025*

## 🚀 High Priority Features

### Timeline Intelligence v2.0 Model Alignment
- **Status**: In Progress (event extraction working, model alignment needed)
- **Priority**: Critical
- **Description**: Fix model mismatch between TemporalEvent and pipeline components
- **Current State**:
  - ✅ Timeline v2.0 extracts 117 temporal events successfully
  - ✅ Video duration bug fixed (uses real 600s instead of estimate 79.6s)
  - ✅ Date extraction from content working
  - ❌ Quality filter expects wrong model structure
  - ❌ Cross-video synthesizer expects wrong model structure
- **Next Steps**:
  - Create adapter layer or update downstream components
  - Test full Timeline v2.0 pipeline end-to-end
  - Validate with real video collections

## 📊 Medium Priority Features

### TimelineJS3 Export Format
- **Status**: Planned
- **Priority**: Medium
- **Prerequisites**: Timeline v2.0 must be working
- **Description**: Export timeline data to TimelineJS3 format for beautiful, interactive visualizations
- **Benefits**:
  - Professional timeline visualizations
  - Embeddable in websites
  - Media-rich with video timestamp links
  - Shareable and engaging output
- **Implementation**:
  - New export format: `--format timeline-js`
  - Transform Timeline v2.0 events to TimelineJS JSON
  - Include video thumbnails and timestamp links
  - Generate both JSON and HTML embed code
- **Resources**:
  - [TimelineJS3](https://timeline.knightlab.com/)
  - [JSON Format](https://timeline.knightlab.com/docs/json-format.html)

## 💡 Future Ideas

### Mission Control Web UI
- **Status**: Conceptual
- **Description**: Web-based dashboard for ClipScribe operations

### Chimera Integration API
- **Status**: Planned
- **Description**: Direct API integration with Chimera Researcher

## 📝 Notes

This file tracks feature ideas and roadmap items. For active development tasks, create GitHub issues following the workflow in `.cursor/rules/README.mdc`. 