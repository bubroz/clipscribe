# ClipScribe Output File Standards

*Last Updated: July 24, 2025*
*Version: v2.20.0*

## Overview

This document establishes quality standards for ClipScribe output files based on comprehensive validation of professional military intelligence content. These standards ensure consistent, high-quality extraction across all video types.

## 📊 Quality Benchmarks (Based on Military Series Validation)

### Baseline Performance Standards
- **Key Points**: 25-35 per video (intelligence briefing style)
- **Entities**: 25-50 per video depending on content density
- **Relationships**: 60-90 per video with evidence chains
- **Processing Cost**: $0.015-0.030 per video (varies by length)
- **Processing Time**: 2-4 minutes per video

### Validated Against: 3-Video Military Training Series
- **Total**: 92 key points, 113 entities, 236 relationships
- **Cost**: $0.0611 total ($0.0203 average per video)
- **Quality**: Professional intelligence analyst standards

## 📝 Key Points Standards

### ✅ **EXCELLENT Quality Indicators**
- **Professional intelligence briefing style**
- **Specific, actionable information** (not generic summaries)
- **Direct quotes of critical facts**
- **Strategic and tactical details included**

#### Examples of EXCELLENT Key Points:
```
✅ "The main three operational Tier 1 units discussed are SEAL Team Six, Delta Force, and the Intelligence Support Activity."
✅ "Tier two selections are characterized by negative reinforcement and team-oriented events."
✅ "The right fitness involves familiarity with water, as many selections include water events."
```

### ❌ **POOR Quality Indicators**
- Generic summaries without specifics
- Repetitive information
- Vague statements without context

#### Examples of POOR Key Points:
```
❌ "The video discusses military topics."
❌ "Various things are mentioned."
❌ "Selection processes are different."
```

### Required Format:
```json
{
  "text": "Specific, actionable insight - intelligence briefing style",
  "importance": 0.9,
  "context": null
}
```

## 👤 PERSON Entity Standards

### ✅ **EXCELLENT Quality Indicators**
- **Specific military roles and backgrounds**
- **Professional descriptors beyond generic titles**
- **Experience and qualification descriptors**

#### Examples of EXCELLENT PERSON Entities:
```
✅ "Former Special Forces operator"
✅ "Tier one instructor"  
✅ "Selection cadre"
✅ "Combat veteran"
✅ "MARSOC Raiders (personnel)"
✅ "Forward Air Controllers"
```

### ❌ **POOR Quality Indicators**
- Only generic "Speaker" entities
- No role-specific extraction
- Missing military background descriptors

#### Examples of POOR PERSON Entities:
```
❌ "Speaker" (only entity extracted)
❌ "Person"
❌ "Individual"
```

## 🏢 ORGANIZATION Entity Standards

### ✅ **EXCELLENT Quality Indicators**
- **Military units correctly classified as ORGANIZATION**
- **Full unit names with proper designation**
- **Sub-units and specialized divisions identified**

#### Examples of EXCELLENT ORGANIZATION Entities:
```
✅ "1st Special Forces Operational Detachment-Delta (Delta Force)"
✅ "Naval Special Warfare Development Group (DEVGRU)"
✅ "Air Force Special Operations Command (AFSOC)"
✅ "Black Side SEALs" (sub-unit correctly classified)
✅ "Marine Force Recon"
```

### ❌ **POOR Quality Indicators**
- Military units classified as PRODUCT
- Generic organization names without specificity
- Missing specialized sub-units

#### Examples of POOR ORGANIZATION Classification:
```
❌ "SEAL Team Six" classified as PRODUCT (should be ORGANIZATION)
❌ "Military" (too generic)
❌ "Unit" (too vague)
```

## 🔗 Relationship Standards

### ✅ **EXCELLENT Quality Indicators**
- **Specific, meaningful predicates** (not generic "related_to")
- **Clear subject-predicate-object structure**
- **Evidence chains with supporting quotes**

#### Examples of EXCELLENT Relationships:
```
✅ "Former Special Forces operator" → "is_role_of" → "Speaker"
✅ "Speaker" → "served_as_cadre_for" → "Tier one selection"  
✅ "Tier 1 units" → "modeled_after" → "British SAS"
```

### ❌ **POOR Quality Indicators**
- Generic predicates like "related_to", "associated_with"
- Unclear or ambiguous relationships
- No supporting evidence

#### Examples of POOR Relationships:
```
❌ "Speaker" → "related_to" → "Military"
❌ "Video" → "discusses" → "Topics"
❌ "Things" → "connected_to" → "Other things"
```

## 📁 File Structure Standards

### Required Files Per Video:
```
output/YYYYMMDD_platform_videoID/
├── transcript.txt                 # Plain text transcript
├── transcript.json               # Full analysis with metadata
├── entities.json                 # Entity details with sources
├── entities.csv                  # Spreadsheet format
├── relationships.json            # Relationship details with evidence
├── relationships.csv            # Spreadsheet format  
├── knowledge_graph.json         # Graph structure
├── knowledge_graph.gexf         # Gephi-compatible format
├── report.md                    # Human-readable intelligence report
├── facts.txt                    # Key points in plain text
├── chimera_format.json          # Chimera-compatible format
└── manifest.json                # File inventory and metadata
```

### File Size Guidelines:
- **transcript.json**: 50-200KB (varies by video length)
- **entities.json**: 10-50KB 
- **relationships.json**: 20-100KB
- **knowledge_graph.gexf**: 20-100KB

## 🎯 Content Type Performance Expectations

### **Military/News Content** (EXCELLENT Performance Expected)
- **Entities**: 40-50 per video
- **Key Points**: 30-35 per video
- **Relationships**: 80-90 per video
- **Quality**: Professional intelligence analyst standards

### **Educational Content** (GOOD Performance Expected)  
- **Entities**: 25-40 per video
- **Key Points**: 20-30 per video
- **Relationships**: 60-80 per video

### **Entertainment Content** (ACCEPTABLE Performance)
- **Entities**: 15-25 per video (often abstract concepts)
- **Key Points**: 15-25 per video
- **Relationships**: 40-60 per video
- **Note**: Quality may vary due to abstract content

### **Music/Lyrical Content** (LIMITED Performance)
- **Entities**: 5-15 per video (mostly abstract)
- **Key Points**: 10-20 per video
- **Quality**: Lower due to artistic/metaphorical content

## 🚨 Quality Validation Checklist

Before approving output, verify:

### Key Points Validation:
- [ ] 25+ key points extracted
- [ ] Intelligence briefing style (specific, actionable)
- [ ] No generic summaries or repetitive content
- [ ] Strategic and tactical details included

### Entity Validation:
- [ ] PERSON entities include roles/backgrounds (not just "Speaker")
- [ ] ORGANIZATION entities properly classified (military units NOT as PRODUCT)
- [ ] 25+ total entities for substantive content
- [ ] Entity types align with content (military = specific units/roles)

### Relationship Validation:
- [ ] 60+ relationships with specific predicates
- [ ] No generic "related_to" relationships
- [ ] Evidence chains present for key relationships
- [ ] Clear subject-predicate-object structure

### File Validation:
- [ ] All 12 required files generated
- [ ] JSON files validate (no syntax errors)  
- [ ] CSV files open correctly in spreadsheet software
- [ ] GEXF files load in Gephi without errors
- [ ] Report.md is human-readable with proper formatting

## 💰 Cost Efficiency Standards

### Target Costs (Based on v2.20.0 Performance):
- **Short videos (3-5 min)**: $0.015-0.020
- **Medium videos (5-8 min)**: $0.020-0.030  
- **Long videos (8+ min)**: $0.030-0.050

### Cost Per Metric:
- **Per key point**: ~$0.0007
- **Per entity**: ~$0.0005
- **Per relationship**: ~$0.0003

## 🔄 Continuous Improvement

### Monthly Review Process:
1. **Sample 10 random videos** from different content types
2. **Validate against these standards**
3. **Identify patterns in quality degradation**
4. **Update prompts and extraction logic as needed**
5. **Revise standards based on performance data**

### Quality Metrics Tracking:
- Average entities per video by content type
- Key points quality score (manual review)
- Relationship specificity ratio (specific vs generic predicates)
- User satisfaction scores
- Processing cost trends

## 📈 Performance Benchmarks

### v2.20.0 Validated Benchmarks:
- **Military Content**: 31-34 key points, 25-44 entities, 64-89 relationships
- **Processing Speed**: 2-4 minutes per video
- **Cost Efficiency**: $0.0167-0.0263 per video
- **Quality Standard**: Professional intelligence analyst level

These standards ensure ClipScribe consistently delivers professional-grade intelligence extraction suitable for research, analysis, and decision-making workflows.

---

*These standards are based on comprehensive validation using a 3-part military training series and represent the quality baseline for ClipScribe v2.20.0 and beyond.* 