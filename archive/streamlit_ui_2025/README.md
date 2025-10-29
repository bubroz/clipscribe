# Streamlit UI Archive

**Archived:** October 28, 2025  
**Reason:** Replaced by planned Next.js web interface (Week 9-12)

## Contents

**Streamlit Application:**
- `streamlit_app/ClipScribe_Mission_Control.py` - Main UI application
- `streamlit_app/pages/` - Multi-page UI (Analytics, Collections, Information Flows)
- `streamlit_app/components/` - Reusable UI components
- `streamlit_app/README.md` - UI documentation (last updated July 20, 2025)

**Frontend Assets:**
- `lib/bindings/` - JavaScript bindings
- `lib/tom-select/` - Dropdown select library
- `lib/vis-9.1.2/` - Vis.js network visualization library

## Status When Archived

**Last Updated:** July 1, 2025 (v2.19.0)  
**Features:**
- Entity visualization with network graphs
- Collection management
- Processing monitor
- Analytics dashboard

**Why Deprecated:**
- Uses old entity extraction (pre-Modal, pre-Grok)
- References Voxtral + Gemini pipeline (replaced by WhisperX + Grok-4)
- Outdated data models (pre-validation refactor)

## Replacement Plan

**Next.js Web Interface (Week 9-12):**
- Modern React-based UI
- Upload interface with drag-and-drop
- Live processing status with real-time updates
- Results viewer (transcript, entities, clips, knowledge graph)
- Entity graph explorer with interactive visualization

**Status:** Planned for Week 9-12 (post-intelligence features)

## Future Use

Can reference for:
- UI/UX patterns
- Visualization approaches
- Component structure ideas

Don't use directly - data models and APIs have changed.

