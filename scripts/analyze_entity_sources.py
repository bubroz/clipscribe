#!/usr/bin/env python3
"""
Entity Source Analysis Tool for ClipScribe

This script analyzes entity extraction effectiveness across different methods
(SpaCy, GLiNER, REBEL) and provides detailed insights into extraction quality.

Usage:
    python scripts/analyze_entity_sources.py --output-dir output/research
    python scripts/analyze_entity_sources.py --single-video output/video_20250101
    python scripts/analyze_entity_sources.py --compare-methods --output-dir output/batch
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime

# Optional Plotly imports for visualization
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class EntitySourceAnalyzer:
    """Comprehensive entity source analysis for ClipScribe outputs."""
    
    def __init__(self, output_dir: Path):
        """Initialize analyzer with output directory."""
        self.output_dir = Path(output_dir)
        self.analysis_results = {}
        self.videos_analyzed = []
        
    def find_entity_source_files(self) -> List[Path]:
        """Find all entity_sources.json files in the output directory."""
        source_files = []
        
        # Search recursively for entity_sources.json files
        for json_file in self.output_dir.rglob("entity_sources.json"):
            source_files.append(json_file)
        
        # Also check for video_intelligence.json files as fallback
        for json_file in self.output_dir.rglob("video_intelligence.json"):
            # Only include if no entity_sources.json exists in same directory
            entity_sources_file = json_file.parent / "entity_sources.json"
            if not entity_sources_file.exists():
                source_files.append(json_file)
        
        return sorted(source_files)
    
    def load_video_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load video data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different file formats
            if 'summary' in data and 'all_entities' in data:
                # This is an entity_sources.json file
                return data
            elif 'entities' in data:
                # This is a video_intelligence.json file - convert format
                return self._convert_video_intelligence_format(data, file_path)
            else:
                print(f"  Unknown format in {file_path}")
                return None
                
        except Exception as e:
            print(f" Error loading {file_path}: {e}")
            return None
    
    def _convert_video_intelligence_format(self, data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Convert video_intelligence.json format to entity_sources format."""
        converted = {
            'video_url': data.get('metadata', {}).get('url', str(file_path.parent)),
            'title': data.get('metadata', {}).get('title', 'Unknown'),
            'summary': data.get('summary', ''),
            'all_entities': []
        }
        
        # Convert entities to entity_sources format
        for entity in data.get('entities', []):
            entity_data = {
                'text': entity.get('text', ''),
                'type': entity.get('type', 'UNKNOWN'),
                'confidence': entity.get('confidence', 0.0),
                'source': entity.get('properties', {}).get('source', 'Unknown')
            }
            converted['all_entities'].append(entity_data)
        
        return converted
    
    def analyze_single_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze entity sources for a single video."""
        entities = video_data.get('all_entities', [])
        
        analysis = {
            'video_info': {
                'title': video_data.get('title', 'Unknown'),
                'url': video_data.get('video_url', ''),
                'total_entities': len(entities)
            },
            'source_breakdown': defaultdict(int),
            'type_breakdown': defaultdict(int),
            'confidence_stats': {},
            'quality_metrics': {}
        }
        
        if not entities:
            return analysis
        
        # Analyze sources and types
        confidences = []
        for entity in entities:
            source = entity.get('source', 'Unknown')
            entity_type = entity.get('type', 'UNKNOWN')
            confidence = float(entity.get('confidence', 0.0))
            
            analysis['source_breakdown'][source] += 1
            analysis['type_breakdown'][entity_type] += 1
            confidences.append(confidence)
        
        # Confidence statistics
        if confidences:
            analysis['confidence_stats'] = {
                'average': sum(confidences) / len(confidences),
                'min': min(confidences),
                'max': max(confidences),
                'high_confidence_count': len([c for c in confidences if c > 0.8]),
                'medium_confidence_count': len([c for c in confidences if 0.5 <= c <= 0.8]),
                'low_confidence_count': len([c for c in confidences if c < 0.5])
            }
        
        # Quality metrics
        total_entities = len(entities)
        analysis['quality_metrics'] = {
            'high_confidence_ratio': analysis['confidence_stats'].get('high_confidence_count', 0) / total_entities,
            'source_diversity': len(analysis['source_breakdown']),
            'type_diversity': len(analysis['type_breakdown']),
            'avg_confidence': analysis['confidence_stats'].get('average', 0.0)
        }
        
        return analysis
    
    def analyze_batch(self, video_files: List[Path]) -> Dict[str, Any]:
        """Analyze entity sources across multiple videos."""
        batch_analysis = {
            'summary': {
                'total_videos': len(video_files),
                'successful_analyses': 0,
                'failed_analyses': 0,
                'total_entities': 0
            },
            'aggregated_stats': {
                'source_distribution': defaultdict(int),
                'type_distribution': defaultdict(int),
                'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0}
            },
            'video_analyses': [],
            'method_comparison': {},
            'quality_insights': []
        }
        
        all_confidences = []
        
        for file_path in video_files:
            print(f" Analyzing {file_path.parent.name}...")
            
            video_data = self.load_video_data(file_path)
            if not video_data:
                batch_analysis['summary']['failed_analyses'] += 1
                continue
            
            video_analysis = self.analyze_single_video(video_data)
            batch_analysis['video_analyses'].append(video_analysis)
            batch_analysis['summary']['successful_analyses'] += 1
            
            # Aggregate statistics
            entities_count = video_analysis['video_info']['total_entities']
            batch_analysis['summary']['total_entities'] += entities_count
            
            for source, count in video_analysis['source_breakdown'].items():
                batch_analysis['aggregated_stats']['source_distribution'][source] += count
            
            for entity_type, count in video_analysis['type_breakdown'].items():
                batch_analysis['aggregated_stats']['type_distribution'][entity_type] += count
            
            # Confidence distribution
            conf_stats = video_analysis.get('confidence_stats', {})
            batch_analysis['aggregated_stats']['confidence_distribution']['high'] += conf_stats.get('high_confidence_count', 0)
            batch_analysis['aggregated_stats']['confidence_distribution']['medium'] += conf_stats.get('medium_confidence_count', 0)
            batch_analysis['aggregated_stats']['confidence_distribution']['low'] += conf_stats.get('low_confidence_count', 0)
        
        # Method comparison analysis
        batch_analysis['method_comparison'] = self._analyze_method_effectiveness(batch_analysis)
        
        # Generate quality insights
        batch_analysis['quality_insights'] = self._generate_quality_insights(batch_analysis)
        
        return batch_analysis
    
    def _analyze_method_effectiveness(self, batch_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the effectiveness of different extraction methods."""
        source_dist = batch_analysis['aggregated_stats']['source_distribution']
        total_entities = batch_analysis['summary']['total_entities']
        
        if total_entities == 0:
            return {}
        
        method_scores = {}
        
        for source, count in source_dist.items():
            percentage = (count / total_entities) * 100
            
            # Calculate effectiveness score based on various factors
            video_analyses = batch_analysis['video_analyses']
            method_confidences = []
            
            for video in video_analyses:
                for entity in video.get('entities', []):  # This would need actual entity data
                    if entity.get('source') == source:
                        method_confidences.append(entity.get('confidence', 0))
            
            avg_confidence = sum(method_confidences) / len(method_confidences) if method_confidences else 0
            
            method_scores[source] = {
                'entity_count': count,
                'percentage': percentage,
                'average_confidence': avg_confidence,
                'effectiveness_score': (percentage * 0.6) + (avg_confidence * 40)  # Weighted score
            }
        
        return method_scores
    
    def _generate_quality_insights(self, batch_analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about extraction quality."""
        insights = []
        
        summary = batch_analysis['summary']
        source_dist = batch_analysis['aggregated_stats']['source_distribution']
        conf_dist = batch_analysis['aggregated_stats']['confidence_distribution']
        
        # Success rate insight
        if summary['total_videos'] > 0:
            success_rate = summary['successful_analyses'] / summary['total_videos']
            if success_rate < 0.9:
                insights.append(f"  Low success rate: {success_rate:.1%} of videos analyzed successfully")
            else:
                insights.append(f" High success rate: {success_rate:.1%} of videos analyzed successfully")
        
        # Source diversity insight
        source_count = len(source_dist)
        if source_count >= 3:
            insights.append(f" Good method diversity: {source_count} extraction methods active")
        elif source_count == 2:
            insights.append(f" Moderate method diversity: {source_count} extraction methods active")
        else:
            insights.append(f"  Low method diversity: Only {source_count} extraction method(s) active")
        
        # Confidence distribution insight
        total_entities = sum(conf_dist.values())
        if total_entities > 0:
            high_conf_ratio = conf_dist['high'] / total_entities
            if high_conf_ratio > 0.7:
                insights.append(f" High confidence extractions: {high_conf_ratio:.1%} of entities")
            elif high_conf_ratio > 0.4:
                insights.append(f" Moderate confidence extractions: {high_conf_ratio:.1%} of entities")
            else:
                insights.append(f"  Low confidence extractions: {high_conf_ratio:.1%} of entities")
        
        # Top performing method
        if source_dist:
            top_method = max(source_dist.items(), key=lambda x: x[1])
            percentage = (top_method[1] / summary['total_entities']) * 100
            insights.append(f" Top performing method: {top_method[0]} ({percentage:.1f}% of entities)")
        
        return insights
    
    def create_visualizations(self, analysis: Dict[str, Any], output_dir: Path) -> List[Path]:
        """Create interactive Plotly visualizations for the analysis."""
        if not PLOTLY_AVAILABLE:
            print("  Plotly not available. Install with: pip install plotly")
            return []
        
        viz_files = []
        
        if 'video_analyses' in analysis:
            # Batch analysis visualizations
            viz_files.extend(self._create_batch_visualizations(analysis, output_dir))
        else:
            # Single video visualizations
            viz_files.extend(self._create_single_video_visualizations(analysis, output_dir))
        
        return viz_files
    
    def _create_batch_visualizations(self, analysis: Dict[str, Any], output_dir: Path) -> List[Path]:
        """Create visualizations for batch analysis."""
        viz_files = []
        
        # 1. Source Distribution Pie Chart
        source_dist = analysis['aggregated_stats']['source_distribution']
        if source_dist:
            fig = go.Figure(data=[go.Pie(
                labels=list(source_dist.keys()),
                values=list(source_dist.values()),
                hole=0.3,
                title="Entity Extraction Method Distribution"
            )])
            
            fig.update_layout(
                title="Entity Source Distribution Across All Videos",
                annotations=[dict(text='Methods', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            pie_file = output_dir / "source_distribution_pie.html"
            fig.write_html(pie_file)
            viz_files.append(pie_file)
        
        # 2. Confidence Distribution Bar Chart
        conf_dist = analysis['aggregated_stats']['confidence_distribution']
        if any(conf_dist.values()):
            fig = go.Figure(data=[
                go.Bar(
                    x=['High (>0.8)', 'Medium (0.5-0.8)', 'Low (<0.5)'],
                    y=[conf_dist['high'], conf_dist['medium'], conf_dist['low']],
                    marker_color=['green', 'orange', 'red']
                )
            ])
            
            fig.update_layout(
                title="Confidence Distribution Across All Entities",
                xaxis_title="Confidence Level",
                yaxis_title="Number of Entities"
            )
            
            conf_file = output_dir / "confidence_distribution.html"
            fig.write_html(conf_file)
            viz_files.append(conf_file)
        
        # 3. Video Comparison Chart
        video_analyses = analysis['video_analyses']
        if len(video_analyses) > 1:
            video_names = [v['video_info']['title'][:30] + "..." if len(v['video_info']['title']) > 30 
                          else v['video_info']['title'] for v in video_analyses]
            entity_counts = [v['video_info']['total_entities'] for v in video_analyses]
            avg_confidences = [v['quality_metrics']['avg_confidence'] for v in video_analyses]
            
            # Create subplot with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(x=video_names, y=entity_counts, name="Entity Count", marker_color='lightblue'),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=video_names, y=avg_confidences, mode='lines+markers', 
                          name="Avg Confidence", line=dict(color='red', width=3)),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="Videos")
            fig.update_yaxes(title_text="Number of Entities", secondary_y=False)
            fig.update_yaxes(title_text="Average Confidence", secondary_y=True)
            fig.update_layout(title_text="Video Comparison: Entity Count vs Average Confidence")
            
            comparison_file = output_dir / "video_comparison.html"
            fig.write_html(comparison_file)
            viz_files.append(comparison_file)
        
        # 4. Entity Type Distribution (Top 10)
        type_dist = analysis['aggregated_stats']['type_distribution']
        if type_dist:
            # Get top 10 entity types
            top_types = dict(sorted(type_dist.items(), key=lambda x: x[1], reverse=True)[:10])
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(top_types.values()),
                    y=list(top_types.keys()),
                    orientation='h',
                    marker_color='lightcoral'
                )
            ])
            
            fig.update_layout(
                title="Top 10 Entity Types Across All Videos",
                xaxis_title="Number of Entities",
                yaxis_title="Entity Type",
                height=600
            )
            
            types_file = output_dir / "entity_types_top10.html"
            fig.write_html(types_file)
            viz_files.append(types_file)
        
        # 5. Method Effectiveness Radar Chart
        method_comparison = analysis.get('method_comparison', {})
        if method_comparison:
            methods = list(method_comparison.keys())
            percentages = [method_comparison[m]['percentage'] for m in methods]
            confidences = [method_comparison[m]['average_confidence'] * 100 for m in methods]  # Scale to 0-100
            effectiveness = [method_comparison[m]['effectiveness_score'] for m in methods]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=percentages + [percentages[0]],  # Close the polygon
                theta=methods + [methods[0]],
                fill='toself',
                name='Coverage %',
                line_color='blue'
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=confidences + [confidences[0]],
                theta=methods + [methods[0]],
                fill='toself',
                name='Avg Confidence (scaled)',
                line_color='red'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Method Effectiveness Comparison"
            )
            
            radar_file = output_dir / "method_effectiveness_radar.html"
            fig.write_html(radar_file)
            viz_files.append(radar_file)
        
        return viz_files
    
    def _create_single_video_visualizations(self, analysis: Dict[str, Any], output_dir: Path) -> List[Path]:
        """Create visualizations for single video analysis."""
        viz_files = []
        
        # 1. Source Breakdown Donut Chart
        source_breakdown = analysis['source_breakdown']
        if source_breakdown:
            fig = go.Figure(data=[go.Pie(
                labels=list(source_breakdown.keys()),
                values=list(source_breakdown.values()),
                hole=0.4,
                textinfo='label+percent',
                marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            )])
            
            fig.update_layout(
                title=f"Entity Sources: {analysis['video_info']['title'][:50]}...",
                annotations=[dict(text='Sources', x=0.5, y=0.5, font_size=16, showarrow=False)]
            )
            
            donut_file = output_dir / "source_breakdown_donut.html"
            fig.write_html(donut_file)
            viz_files.append(donut_file)
        
        # 2. Entity Type Distribution
        type_breakdown = analysis['type_breakdown']
        if type_breakdown:
            fig = go.Figure(data=[
                go.Bar(
                    x=list(type_breakdown.keys()),
                    y=list(type_breakdown.values()),
                    marker_color='lightseagreen'
                )
            ])
            
            fig.update_layout(
                title="Entity Types Distribution",
                xaxis_title="Entity Type",
                yaxis_title="Count",
                xaxis_tickangle=-45
            )
            
            types_file = output_dir / "entity_types_bar.html"
            fig.write_html(types_file)
            viz_files.append(types_file)
        
        # 3. Quality Metrics Gauge
        quality = analysis['quality_metrics']
        if quality:
            fig = go.Figure()
            
            # Average confidence gauge
            fig.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = quality['avg_confidence'],
                domain = {'x': [0, 0.5], 'y': [0.5, 1]},
                title = {'text': "Average Confidence"},
                delta = {'reference': 0.8},
                gauge = {
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 0.5], 'color': "lightgray"},
                        {'range': [0.5, 0.8], 'color': "gray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9}}))
            
            # High confidence ratio gauge
            fig.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = quality['high_confidence_ratio'],
                domain = {'x': [0.5, 1], 'y': [0.5, 1]},
                title = {'text': "High Confidence Ratio"},
                delta = {'reference': 0.7},
                gauge = {
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 0.4], 'color': "lightgray"},
                        {'range': [0.4, 0.7], 'color': "gray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.8}}))
            
            # Source diversity indicator
            fig.add_trace(go.Indicator(
                mode = "number+delta",
                value = quality['source_diversity'],
                domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                title = {'text': "Source Diversity"},
                delta = {'reference': 3}))
            
            # Type diversity indicator
            fig.add_trace(go.Indicator(
                mode = "number+delta",
                value = quality['type_diversity'],
                domain = {'x': [0.5, 1], 'y': [0, 0.5]},
                title = {'text': "Type Diversity"},
                delta = {'reference': 5}))
            
            fig.update_layout(
                title="Quality Metrics Dashboard",
                height=600
            )
            
            gauge_file = output_dir / "quality_metrics_dashboard.html"
            fig.write_html(gauge_file)
            viz_files.append(gauge_file)
        
        return viz_files
    
    def save_analysis_report(self, analysis: Dict[str, Any], output_file: Path):
        """Save analysis results to a JSON file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f" Analysis report saved to: {output_file}")
        except Exception as e:
            print(f" Error saving report: {e}")
    
    def save_csv_report(self, analysis: Dict[str, Any], output_file: Path):
        """Save analysis results to a CSV file."""
        try:
            csv_data = []
            
            if 'video_analyses' in analysis:
                # Batch analysis
                for video in analysis['video_analyses']:
                    video_info = video['video_info']
                    quality = video['quality_metrics']
                    
                    row = {
                        'Video Title': video_info['title'],
                        'Total Entities': video_info['total_entities'],
                        'Source Diversity': quality['source_diversity'],
                        'Type Diversity': quality['type_diversity'],
                        'Average Confidence': quality['avg_confidence'],
                        'High Confidence Ratio': quality['high_confidence_ratio']
                    }
                    
                    # Add source breakdown
                    for source, count in video['source_breakdown'].items():
                        row[f'{source}_Count'] = count
                    
                    csv_data.append(row)
            else:
                # Single video analysis
                video_info = analysis['video_info']
                quality = analysis['quality_metrics']
                
                row = {
                    'Video Title': video_info['title'],
                    'Total Entities': video_info['total_entities'],
                    'Source Diversity': quality['source_diversity'],
                    'Type Diversity': quality['type_diversity'],
                    'Average Confidence': quality['avg_confidence'],
                    'High Confidence Ratio': quality['high_confidence_ratio']
                }
                
                for source, count in analysis['source_breakdown'].items():
                    row[f'{source}_Count'] = count
                
                csv_data = [row]
            
            df = pd.DataFrame(csv_data)
            df.to_csv(output_file, index=False)
            print(f" CSV report saved to: {output_file}")
            
        except Exception as e:
            print(f" Error saving CSV report: {e}")
    
    def save_excel_report(self, analysis: Dict[str, Any], output_file: Path):
        """Save analysis results to an Excel file with multiple sheets."""
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                
                if 'video_analyses' in analysis:
                    # Batch analysis - multiple sheets
                    
                    # Summary sheet
                    summary_data = {
                        'Metric': ['Total Videos', 'Successful Analyses', 'Failed Analyses', 'Total Entities'],
                        'Value': [
                            analysis['summary']['total_videos'],
                            analysis['summary']['successful_analyses'], 
                            analysis['summary']['failed_analyses'],
                            analysis['summary']['total_entities']
                        ]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Source distribution sheet
                    source_dist = analysis['aggregated_stats']['source_distribution']
                    if source_dist:
                        source_df = pd.DataFrame([
                            {'Extraction Method': source, 'Entity Count': count, 
                             'Percentage': f"{(count/analysis['summary']['total_entities']*100):.1f}%"}
                            for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True)
                        ])
                        source_df.to_excel(writer, sheet_name='Source Distribution', index=False)
                    
                    # Video details sheet
                    video_data = []
                    for video in analysis['video_analyses']:
                        video_info = video['video_info']
                        quality = video['quality_metrics']
                        
                        row = {
                            'Video Title': video_info['title'],
                            'Total Entities': video_info['total_entities'],
                            'Source Diversity': quality['source_diversity'],
                            'Type Diversity': quality['type_diversity'],
                            'Average Confidence': round(quality['avg_confidence'], 3),
                            'High Confidence Ratio': round(quality['high_confidence_ratio'], 3)
                        }
                        
                        # Add source breakdown
                        for source, count in video['source_breakdown'].items():
                            row[f'{source}_Count'] = count
                        
                        video_data.append(row)
                    
                    pd.DataFrame(video_data).to_excel(writer, sheet_name='Video Details', index=False)
                    
                    # Quality insights sheet
                    if analysis.get('quality_insights'):
                        insights_df = pd.DataFrame({
                            'Insight': analysis['quality_insights']
                        })
                        insights_df.to_excel(writer, sheet_name='Quality Insights', index=False)
                
                else:
                    # Single video analysis
                    video_info = analysis['video_info']
                    quality = analysis['quality_metrics']
                    
                    # Main metrics
                    main_data = {
                        'Metric': ['Video Title', 'Total Entities', 'Source Diversity', 'Type Diversity', 
                                  'Average Confidence', 'High Confidence Ratio'],
                        'Value': [video_info['title'], video_info['total_entities'], quality['source_diversity'],
                                 quality['type_diversity'], round(quality['avg_confidence'], 3), 
                                 round(quality['high_confidence_ratio'], 3)]
                    }
                    pd.DataFrame(main_data).to_excel(writer, sheet_name='Overview', index=False)
                    
                    # Source breakdown
                    if analysis['source_breakdown']:
                        source_df = pd.DataFrame([
                            {'Source': source, 'Count': count, 
                             'Percentage': f"{(count/video_info['total_entities']*100):.1f}%"}
                            for source, count in analysis['source_breakdown'].items()
                        ])
                        source_df.to_excel(writer, sheet_name='Source Breakdown', index=False)
                    
                    # Type breakdown
                    if analysis['type_breakdown']:
                        type_df = pd.DataFrame([
                            {'Entity Type': entity_type, 'Count': count}
                            for entity_type, count in sorted(analysis['type_breakdown'].items(), 
                                                           key=lambda x: x[1], reverse=True)
                        ])
                        type_df.to_excel(writer, sheet_name='Type Breakdown', index=False)
            
            print(f" Excel report saved to: {output_file}")
            
        except Exception as e:
            print(f" Error saving Excel report: {e}")
            print(" Make sure openpyxl is installed: pip install openpyxl")
    
    def generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive markdown report."""
        report = ["# Entity Source Analysis Report\n"]
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if 'video_analyses' in analysis:
            # Batch analysis report
            summary = analysis['summary']
            report.append("##  Batch Analysis Summary\n")
            report.append(f"- **Total Videos**: {summary['total_videos']}")
            report.append(f"- **Successfully Analyzed**: {summary['successful_analyses']}")
            report.append(f"- **Failed Analyses**: {summary['failed_analyses']}")
            report.append(f"- **Total Entities Extracted**: {summary['total_entities']}\n")
            
            # Source distribution
            source_dist = analysis['aggregated_stats']['source_distribution']
            if source_dist:
                report.append("##  Extraction Method Performance\n")
                report.append("| Method | Entity Count | Percentage |\n")
                report.append("|--------|--------------|------------|\n")
                
                total_entities = summary['total_entities']
                for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_entities) * 100 if total_entities > 0 else 0
                    report.append(f"| {source} | {count} | {percentage:.1f}% |\n")
                report.append("")
            
            # Quality insights
            if analysis.get('quality_insights'):
                report.append("##  Quality Insights\n")
                for insight in analysis['quality_insights']:
                    report.append(f"- {insight}")
                report.append("")
            
            # Method comparison
            if analysis.get('method_comparison'):
                report.append("##  Method Effectiveness\n")
                for method, stats in analysis['method_comparison'].items():
                    report.append(f"### {method}")
                    report.append(f"- **Entities**: {stats['entity_count']}")
                    report.append(f"- **Coverage**: {stats['percentage']:.1f}%")
                    report.append(f"- **Avg Confidence**: {stats['average_confidence']:.2f}")
                    report.append(f"- **Effectiveness Score**: {stats['effectiveness_score']:.1f}")
                    report.append("")
        else:
            # Single video analysis report
            video_info = analysis['video_info']
            report.append("##  Single Video Analysis\n")
            report.append(f"- **Title**: {video_info['title']}")
            report.append(f"- **Total Entities**: {video_info['total_entities']}\n")
            
            # Source breakdown
            if analysis['source_breakdown']:
                report.append("###  Source Breakdown\n")
                for source, count in analysis['source_breakdown'].items():
                    percentage = (count / video_info['total_entities']) * 100 if video_info['total_entities'] > 0 else 0
                    report.append(f"- **{source}**: {count} entities ({percentage:.1f}%)")
                report.append("")
            
            # Quality metrics
            quality = analysis['quality_metrics']
            report.append("###  Quality Metrics\n")
            report.append(f"- **Average Confidence**: {quality['avg_confidence']:.2f}")
            report.append(f"- **High Confidence Ratio**: {quality['high_confidence_ratio']:.1%}")
            report.append(f"- **Source Diversity**: {quality['source_diversity']} methods")
            report.append(f"- **Type Diversity**: {quality['type_diversity']} entity types")
        
        return "\n".join(report)


def main():
    """Main entry point for the entity source analysis tool."""
    parser = argparse.ArgumentParser(description="Analyze entity extraction effectiveness in ClipScribe outputs")
    parser.add_argument("--output-dir", type=Path, help="Directory containing ClipScribe outputs")
    parser.add_argument("--single-video", type=Path, help="Analyze a single video directory")
    parser.add_argument("--compare-methods", action="store_true", help="Compare extraction method effectiveness")
    parser.add_argument("--save-csv", action="store_true", help="Save results as CSV file")
    parser.add_argument("--save-excel", action="store_true", help="Save results as Excel file")
    parser.add_argument("--save-markdown", action="store_true", help="Save results as Markdown report")
    parser.add_argument("--create-visualizations", action="store_true", default=True, help="Create interactive Plotly visualizations (default: True)")
    
    args = parser.parse_args()
    
    if not args.output_dir and not args.single_video:
        print(" Please specify either --output-dir or --single-video")
        return
    
    if args.single_video:
        # Single video analysis
        analyzer = EntitySourceAnalyzer(args.single_video.parent)
        
        # Look for entity source files in the specific directory
        source_files = []
        for json_file in args.single_video.glob("*.json"):
            if json_file.name in ["entity_sources.json", "video_intelligence.json"]:
                source_files.append(json_file)
        
        if not source_files:
            print(f" No entity source files found in {args.single_video}")
            return
        
        video_data = analyzer.load_video_data(source_files[0])
        if not video_data:
            print(" Failed to load video data")
            return
        
        analysis = analyzer.analyze_single_video(video_data)
        
        # Save results
        output_file = args.single_video / "entity_source_analysis.json"
        analyzer.save_analysis_report(analysis, output_file)
        
        if args.save_csv:
            csv_file = args.single_video / "entity_source_analysis.csv"
            analyzer.save_csv_report(analysis, csv_file)
        
        if args.save_excel:
            excel_file = args.single_video / "entity_source_analysis.xlsx"
            analyzer.save_excel_report(analysis, excel_file)
        
        if args.save_markdown:
            md_file = args.single_video / "entity_source_analysis.md"
            md_content = analyzer.generate_markdown_report(analysis)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f" Markdown report saved to: {md_file}")
        
        if args.create_visualizations:
            viz_files = analyzer.create_visualizations(analysis, args.single_video)
            if viz_files:
                print(f" Created {len(viz_files)} visualization files:")
                for viz_file in viz_files:
                    print(f"    {viz_file}")
        
        print(f"\n Analysis Complete!")
        print(f" Found {analysis['video_info']['total_entities']} entities")
        print(f" {analysis['quality_metrics']['source_diversity']} extraction methods used")
        print(f" Average confidence: {analysis['quality_metrics']['avg_confidence']:.2f}")
        
    else:
        # Batch analysis
        analyzer = EntitySourceAnalyzer(args.output_dir)
        source_files = analyzer.find_entity_source_files()
        
        if not source_files:
            print(f" No entity source files found in {args.output_dir}")
            return
        
        print(f" Found {len(source_files)} videos to analyze...")
        analysis = analyzer.analyze_batch(source_files)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = args.output_dir / f"batch_entity_analysis_{timestamp}.json"
        analyzer.save_analysis_report(analysis, output_file)
        
        if args.save_csv:
            csv_file = args.output_dir / f"batch_entity_analysis_{timestamp}.csv"
            analyzer.save_csv_report(analysis, csv_file)
        
        if args.save_excel:
            excel_file = args.output_dir / f"batch_entity_analysis_{timestamp}.xlsx"
            analyzer.save_excel_report(analysis, excel_file)
        
        if args.save_markdown:
            md_file = args.output_dir / f"batch_entity_analysis_{timestamp}.md"
            md_content = analyzer.generate_markdown_report(analysis)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f" Markdown report saved to: {md_file}")
        
        if args.create_visualizations:
            viz_files = analyzer.create_visualizations(analysis, args.output_dir)
            if viz_files:
                print(f" Created {len(viz_files)} visualization files:")
                for viz_file in viz_files:
                    print(f"    {viz_file}")
        
        # Display summary
        summary = analysis['summary']
        print(f"\n Batch Analysis Complete!")
        print(f" Analyzed {summary['successful_analyses']}/{summary['total_videos']} videos")
        print(f" Total entities: {summary['total_entities']}")
        
        if analysis.get('quality_insights'):
            print("\n Key Insights:")
            for insight in analysis['quality_insights'][:3]:  # Show top 3 insights
                print(f"   {insight}")


if __name__ == "__main__":
    main()
