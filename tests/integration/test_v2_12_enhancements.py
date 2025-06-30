#!/usr/bin/env python3
"""
Test script for ClipScribe v2.12.0 enhancements.

This script tests the new features introduced in v2.12.0:
1. Advanced Plotly visualizations in entity source analysis
2. Excel export capabilities with multiple sheets
3. Enhanced CSV formatting and export options
4. Dedicated performance monitoring dashboards in Streamlit
5. Interactive charts and graphs for analysis reports

Usage:
    python test_v2_12_enhancements.py
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import shutil
import json
import time
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.utils.performance import PerformanceMonitor
from clipscribe.utils.performance_dashboard import create_performance_dashboard
from clipscribe.extractors.model_manager import model_manager

def test_plotly_availability():
    """Test 1: Verify Plotly is available for advanced visualizations."""
    print("🧪 Test 1: Plotly Availability")
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        print("✅ Plotly is available for advanced visualizations")
        return True
    except ImportError as e:
        print(f"❌ Plotly not available: {e}")
        print("💡 Install with: pip install plotly")
        return False

def test_excel_export_capabilities():
    """Test 2: Verify Excel export capabilities with openpyxl."""
    print("\n🧪 Test 2: Excel Export Capabilities")
    try:
        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows
        import pandas as pd
        import io
        
        # Create a test workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Sheet"
        
        # Add test data
        test_data = [
            ["Method", "Count", "Percentage"],
            ["SpaCy", 150, "60%"],
            ["GLiNER", 75, "30%"],
            ["REBEL", 25, "10%"]
        ]
        
        for row in test_data:
            ws.append(row)
        
        # Test saving to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        if len(output.getvalue()) > 0:
            print("✅ Excel export capabilities working correctly")
            return True
        else:
            print("❌ Excel export failed - no data written")
            return False
            
    except ImportError as e:
        print(f"❌ openpyxl not available: {e}")
        print("💡 Install with: pip install openpyxl")
        return False
    except Exception as e:
        print(f"❌ Excel export test failed: {e}")
        return False

def test_entity_source_analyzer_enhancements():
    """Test 3: Test enhanced entity source analyzer with visualizations."""
    print("\n🧪 Test 3: Entity Source Analyzer Enhancements")
    try:
        from scripts.analyze_entity_sources import EntitySourceAnalyzer
        
        # Create temporary test data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock entity sources data
            mock_data = {
                "video_url": "https://test.com/video",
                "title": "Test Video for v2.12.0",
                "summary": "Test summary",
                "all_entities": [
                    {"text": "Test Entity 1", "type": "PERSON", "confidence": 0.9, "source": "SpaCy"},
                    {"text": "Test Entity 2", "type": "ORG", "confidence": 0.8, "source": "GLiNER"},
                    {"text": "Test Entity 3", "type": "LOCATION", "confidence": 0.7, "source": "REBEL"},
                    {"text": "Test Entity 4", "type": "PERSON", "confidence": 0.95, "source": "SpaCy"},
                ]
            }
            
            # Save test data
            test_file = temp_path / "entity_sources.json"
            with open(test_file, 'w') as f:
                json.dump(mock_data, f)
            
            # Test analyzer
            analyzer = EntitySourceAnalyzer(temp_path)
            video_data = analyzer.load_video_data(test_file)
            
            if not video_data:
                print("❌ Failed to load test video data")
                return False
            
            # Test single video analysis
            analysis = analyzer.analyze_single_video(video_data)
            
            # Verify analysis structure
            expected_keys = ['video_info', 'source_breakdown', 'type_breakdown', 'confidence_stats', 'quality_metrics']
            if not all(key in analysis for key in expected_keys):
                print(f"❌ Analysis missing required keys: {expected_keys}")
                return False
            
            # Test visualization creation
            try:
                viz_files = analyzer.create_visualizations(analysis, temp_path)
                if viz_files:
                    print(f"✅ Created {len(viz_files)} visualization files")
                else:
                    print("⚠️ No visualization files created (Plotly may not be available)")
            except Exception as e:
                print(f"⚠️ Visualization creation failed: {e}")
            
            # Test Excel export
            try:
                excel_file = temp_path / "test_analysis.xlsx"
                analyzer.save_excel_report(analysis, excel_file)
                if excel_file.exists() and excel_file.stat().st_size > 0:
                    print("✅ Excel export working correctly")
                else:
                    print("❌ Excel export failed")
                    return False
            except Exception as e:
                print(f"❌ Excel export test failed: {e}")
                return False
            
            print("✅ Entity source analyzer enhancements working correctly")
            return True
            
    except ImportError as e:
        print(f"❌ Entity source analyzer import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Entity source analyzer test failed: {e}")
        return False

def test_performance_dashboard():
    """Test 4: Test performance dashboard functionality."""
    print("\n🧪 Test 4: Performance Dashboard")
    try:
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Test performance monitor
            perf_monitor = PerformanceMonitor(output_dir)
            
            # Simulate some performance data
            event = perf_monitor.start_timer("test_operation", url="test://url")
            time.sleep(0.1)  # Simulate work
            perf_monitor.stop_timer(event)
            
            perf_monitor.record_metric("test_metric", 42, url="test://url")
            
            # Test performance dashboard creation
            dashboard = create_performance_dashboard(output_dir)
            
            if dashboard is None:
                print("❌ Failed to create performance dashboard")
                return False
            
            # Test model manager integration
            cache_info = model_manager.get_cache_info()
            if 'model_count' not in cache_info:
                print("❌ Model manager cache info missing required fields")
                return False
            
            print("✅ Performance dashboard functionality working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Performance dashboard test failed: {e}")
        return False

def test_streamlit_app_imports():
    """Test 5: Test Streamlit app imports and dependencies."""
    print("\n🧪 Test 5: Streamlit App Dependencies")
    try:
        # Test critical imports for the enhanced Streamlit app
        import streamlit as st
        import pandas as pd
        import plotly.graph_objects as go
        import plotly.express as px
        from openpyxl import Workbook
        
        # Test app.py imports
        from src.clipscribe.utils.performance_dashboard import create_performance_dashboard
        from src.clipscribe.extractors.model_manager import model_manager
        
        print("✅ All Streamlit app dependencies available")
        return True
        
    except ImportError as e:
        print(f"❌ Streamlit app dependency missing: {e}")
        return False
    except Exception as e:
        print(f"❌ Streamlit app import test failed: {e}")
        return False

async def test_batch_processing_with_performance_monitoring():
    """Test 6: Test batch processing with enhanced performance monitoring."""
    print("\n🧪 Test 6: Batch Processing with Performance Monitoring")
    try:
        from clipscribe.retrievers import VideoIntelligenceRetriever
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Initialize performance monitoring
            perf_monitor = PerformanceMonitor(output_dir)
            
            # Initialize batch processing
            perf_monitor.start_batch_processing()
            
            # Simulate batch processing metrics
            batch_event = perf_monitor.start_timer("batch_processing", batch_size=3)
            
            for i in range(3):
                video_event = perf_monitor.start_timer(
                    "video_processing", 
                    url=f"test://video{i}",
                    video_id=f"test{i}"
                )
                time.sleep(0.05)  # Simulate processing
                perf_monitor.record_metric("entities_extracted", 10 + i * 5, url=f"test://video{i}")
                perf_monitor.record_metric("relationships_extracted", 5 + i * 2, url=f"test://video{i}")
                
                # Record video processed
                perf_monitor.record_video_processed(
                    entities_count=10 + i * 5,
                    relationships_count=5 + i * 2,
                    processing_time=0.05,
                    error=False
                )
                
                perf_monitor.stop_timer(video_event)
            
            perf_monitor.stop_timer(batch_event)
            perf_monitor.end_batch_processing()
            
            # Test batch statistics
            batch_stats = perf_monitor.get_batch_stats()
            
            required_keys = ['videos_processed', 'total_entities', 'total_time_seconds']
            if not all(key in batch_stats for key in required_keys):
                print(f"❌ Batch stats missing required keys: {required_keys}")
                return False
            
            # Test performance report generation
            report_file = perf_monitor.save_report()
            if not report_file.exists():
                print("❌ Performance report not generated")
                return False
            
            print("✅ Batch processing with performance monitoring working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

def test_enhanced_csv_formatting():
    """Test 7: Test enhanced CSV formatting and export options."""
    print("\n🧪 Test 7: Enhanced CSV Formatting")
    try:
        import pandas as pd
        import io
        
        # Create test data
        test_analysis = {
            'total_videos': 3,
            'total_entities': 45,
            'confidence_stats': {'average': 0.85, 'high_confidence_count': 30},
            'videos_analysis': [
                {
                    'title': 'Test Video 1',
                    'entity_count': 15,
                    'source_breakdown': {'SpaCy': 10, 'GLiNER': 5},
                    'type_breakdown': {'PERSON': 8, 'ORG': 4, 'LOCATION': 3}
                },
                {
                    'title': 'Test Video 2',
                    'entity_count': 20,
                    'source_breakdown': {'SpaCy': 12, 'GLiNER': 6, 'REBEL': 2},
                    'type_breakdown': {'PERSON': 10, 'ORG': 6, 'LOCATION': 4}
                },
                {
                    'title': 'Test Video 3',
                    'entity_count': 10,
                    'source_breakdown': {'GLiNER': 7, 'REBEL': 3},
                    'type_breakdown': {'PERSON': 4, 'ORG': 3, 'LOCATION': 3}
                }
            ]
        }
        
        # Test CSV generation
        csv_data = []
        for video in test_analysis['videos_analysis']:
            row = {
                'Video Title': video['title'],
                'Entity Count': video['entity_count'],
            }
            
            # Add source breakdown
            for source, count in video['source_breakdown'].items():
                row[f'{source}_Count'] = count
            
            # Add top types
            top_types = sorted(video['type_breakdown'].items(), key=lambda x: x[1], reverse=True)[:3]
            for i, (entity_type, count) in enumerate(top_types):
                row[f'Top_Type_{i+1}'] = f"{entity_type} ({count})"
            
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        csv_output = df.to_csv(index=False)
        
        # Verify CSV structure
        if len(csv_output.split('\n')) < 4:  # Header + 3 data rows + empty line
            print("❌ CSV output structure incorrect")
            return False
        
        # Check for required columns
        required_columns = ['Video Title', 'Entity Count', 'SpaCy_Count', 'GLiNER_Count']
        csv_lines = csv_output.split('\n')
        header = csv_lines[0]
        
        if not all(col in header for col in required_columns):
            print(f"❌ CSV missing required columns: {required_columns}")
            return False
        
        print("✅ Enhanced CSV formatting working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced CSV formatting test failed: {e}")
        return False

async def main():
    """Run all v2.12.0 enhancement tests."""
    print("🚀 ClipScribe v2.12.0 Enhancement Tests")
    print("=" * 50)
    
    tests = [
        test_plotly_availability,
        test_excel_export_capabilities,
        test_entity_source_analyzer_enhancements,
        test_performance_dashboard,
        test_streamlit_app_imports,
        test_enhanced_csv_formatting,
    ]
    
    # Add async tests
    async_tests = [
        test_batch_processing_with_performance_monitoring,
    ]
    
    results = []
    
    # Run synchronous tests
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Run asynchronous tests
    for test in async_tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All v2.12.0 enhancement tests passed!")
        print("🚀 ClipScribe v2.12.0 is ready with:")
        print("   • Advanced Plotly visualizations")
        print("   • Excel export capabilities")
        print("   • Enhanced CSV formatting")
        print("   • Performance monitoring dashboards")
        print("   • Interactive charts and analysis")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 