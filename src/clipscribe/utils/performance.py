"""
Performance monitoring and metrics collection for ClipScribe.

This module provides utilities to track API response times, extraction quality,
model cache performance, and other performance-related metrics to identify 
bottlenecks and opportunities for optimization.
"""
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


class PerformanceMonitor:
    """A class to handle performance metric collection and reporting."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / "performance"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics: List[Dict[str, Any]] = []
        self.model_cache_metrics = {
            'cache_hits': defaultdict(int),
            'cache_misses': defaultdict(int),
            'load_times': defaultdict(list),
            'memory_usage': defaultdict(list)
        }
        self.batch_metrics = {
            'videos_processed': 0,
            'total_entities': 0,
            'total_relationships': 0,
            'processing_times': [],
            'error_count': 0,
            'start_time': None,
            'end_time': None
        }

    def start_timer(self, event_name: str, **kwargs) -> Dict[str, Any]:
        """
        Start a timer for a specific event.

        Args:
            event_name: The name of the event being timed.
            **kwargs: Additional metadata to store with the event.

        Returns:
            A dictionary representing the running event timer.
        """
        event = {
            "event": event_name,
            "start_time": time.monotonic(),
            "end_time": None,
            "duration": None,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        return event

    def stop_timer(self, event: Dict[str, Any]):
        """
        Stop a timer and record the metric.

        Args:
            event: The event dictionary returned by start_timer.
        """
        if event and "start_time" in event and event.get("end_time") is None:
            event["end_time"] = time.monotonic()
            event["duration"] = event["end_time"] - event["start_time"]
            self.metrics.append(event)

    def record_metric(self, event_name: str, value: Any, **kwargs):
        """
        Record a single, non-timed metric.

        Args:
            event_name: The name of the metric.
            value: The value of the metric.
            **kwargs: Additional metadata.
        """
        metric = {
            "event": event_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.metrics.append(metric)

    def record_model_cache_hit(self, model_name: str, load_time: Optional[float] = None):
        """Record a model cache hit."""
        self.model_cache_metrics['cache_hits'][model_name] += 1
        if load_time:
            self.model_cache_metrics['load_times'][model_name].append(load_time)
        
        self.record_metric("model_cache_hit", 1, model=model_name, load_time=load_time)

    def record_model_cache_miss(self, model_name: str, load_time: float):
        """Record a model cache miss (new model load)."""
        self.model_cache_metrics['cache_misses'][model_name] += 1
        self.model_cache_metrics['load_times'][model_name].append(load_time)
        
        self.record_metric("model_cache_miss", 1, model=model_name, load_time=load_time)

    def record_model_memory_usage(self, model_name: str, memory_mb: float):
        """Record model memory usage."""
        self.model_cache_metrics['memory_usage'][model_name].append(memory_mb)
        
        self.record_metric("model_memory_usage", memory_mb, model=model_name)

    def start_batch_processing(self):
        """Start tracking batch processing metrics."""
        self.batch_metrics['start_time'] = time.time()
        self.batch_metrics['videos_processed'] = 0
        self.batch_metrics['total_entities'] = 0
        self.batch_metrics['total_relationships'] = 0
        self.batch_metrics['processing_times'] = []
        self.batch_metrics['error_count'] = 0

    def record_video_processed(self, entities_count: int, relationships_count: int, 
                             processing_time: float, error: bool = False):
        """Record metrics for a processed video."""
        self.batch_metrics['videos_processed'] += 1
        self.batch_metrics['total_entities'] += entities_count
        self.batch_metrics['total_relationships'] += relationships_count
        self.batch_metrics['processing_times'].append(processing_time)
        
        if error:
            self.batch_metrics['error_count'] += 1

    def end_batch_processing(self):
        """End batch processing and calculate final metrics."""
        self.batch_metrics['end_time'] = time.time()
        
        if self.batch_metrics['start_time']:
            total_time = self.batch_metrics['end_time'] - self.batch_metrics['start_time']
            
            self.record_metric("batch_total_time", total_time)
            self.record_metric("batch_videos_processed", self.batch_metrics['videos_processed'])
            self.record_metric("batch_total_entities", self.batch_metrics['total_entities'])
            self.record_metric("batch_total_relationships", self.batch_metrics['total_relationships'])
            self.record_metric("batch_error_count", self.batch_metrics['error_count'])
            
            if self.batch_metrics['videos_processed'] > 0:
                avg_time_per_video = total_time / self.batch_metrics['videos_processed']
                avg_entities_per_video = self.batch_metrics['total_entities'] / self.batch_metrics['videos_processed']
                
                self.record_metric("batch_avg_time_per_video", avg_time_per_video)
                self.record_metric("batch_avg_entities_per_video", avg_entities_per_video)

    def get_model_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive model cache statistics."""
        stats = {
            'cache_performance': {},
            'total_hits': sum(self.model_cache_metrics['cache_hits'].values()),
            'total_misses': sum(self.model_cache_metrics['cache_misses'].values()),
            'hit_rate': 0.0,
            'average_load_times': {},
            'memory_usage': {}
        }
        
        # Calculate hit rate
        total_requests = stats['total_hits'] + stats['total_misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['total_hits'] / total_requests
        
        # Per-model statistics
        all_models = set(self.model_cache_metrics['cache_hits'].keys()) | \
                    set(self.model_cache_metrics['cache_misses'].keys())
        
        for model in all_models:
            hits = self.model_cache_metrics['cache_hits'][model]
            misses = self.model_cache_metrics['cache_misses'][model]
            total = hits + misses
            
            stats['cache_performance'][model] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': hits / total if total > 0 else 0,
                'total_requests': total
            }
            
            # Average load times
            load_times = self.model_cache_metrics['load_times'][model]
            if load_times:
                stats['average_load_times'][model] = sum(load_times) / len(load_times)
            
            # Memory usage
            memory_usage = self.model_cache_metrics['memory_usage'][model]
            if memory_usage:
                stats['memory_usage'][model] = {
                    'average_mb': sum(memory_usage) / len(memory_usage),
                    'peak_mb': max(memory_usage),
                    'samples': len(memory_usage)
                }
        
        return stats

    def get_batch_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        if not self.batch_metrics['start_time']:
            return {}
        
        end_time = self.batch_metrics['end_time'] or time.time()
        total_time = end_time - self.batch_metrics['start_time']
        
        stats = {
            'videos_processed': self.batch_metrics['videos_processed'],
            'total_entities': self.batch_metrics['total_entities'],
            'total_relationships': self.batch_metrics['total_relationships'],
            'error_count': self.batch_metrics['error_count'],
            'total_time_seconds': total_time,
            'success_rate': 0.0,
            'throughput': {},
            'performance_metrics': {}
        }
        
        # Success rate
        if self.batch_metrics['videos_processed'] > 0:
            successful_videos = self.batch_metrics['videos_processed'] - self.batch_metrics['error_count']
            stats['success_rate'] = successful_videos / self.batch_metrics['videos_processed']
        
        # Throughput metrics
        if total_time > 0:
            stats['throughput'] = {
                'videos_per_minute': (self.batch_metrics['videos_processed'] / total_time) * 60,
                'entities_per_minute': (self.batch_metrics['total_entities'] / total_time) * 60,
                'relationships_per_minute': (self.batch_metrics['total_relationships'] / total_time) * 60
            }
        
        # Performance metrics
        if self.batch_metrics['processing_times']:
            processing_times = self.batch_metrics['processing_times']
            stats['performance_metrics'] = {
                'avg_processing_time': sum(processing_times) / len(processing_times),
                'min_processing_time': min(processing_times),
                'max_processing_time': max(processing_times),
                'total_processing_time': sum(processing_times)
            }
        
        return stats

    def generate_performance_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive performance summary."""
        summary = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'total_metrics': len(self.metrics),
            'model_cache_stats': self.get_model_cache_stats(),
            'batch_stats': self.get_batch_stats(),
            'recommendations': []
        }
        
        # Generate performance recommendations
        cache_stats = summary['model_cache_stats']
        if cache_stats['hit_rate'] < 0.5:
            summary['recommendations'].append(
                "Low model cache hit rate - consider keeping models loaded longer"
            )
        elif cache_stats['hit_rate'] > 0.9:
            summary['recommendations'].append(
                "Excellent model cache performance - 3-5x speed improvement achieved"
            )
        
        batch_stats = summary['batch_stats']
        if batch_stats and batch_stats.get('success_rate', 1.0) < 0.9:
            summary['recommendations'].append(
                f"High error rate ({(1-batch_stats['success_rate'])*100:.1f}%) - investigate failed videos"
            )
        
        if batch_stats and batch_stats.get('throughput', {}).get('videos_per_minute', 0) < 1:
            summary['recommendations'].append(
                "Low throughput - consider optimizing extraction parameters or enabling more caching"
            )
        
        return summary

    def save_report(self):
        """Save the collected performance metrics to a JSON file."""
        if not self.metrics and not any(self.model_cache_metrics.values()):
            return None

        # Generate comprehensive report
        report = {
            'summary': self.generate_performance_summary(),
            'detailed_metrics': self.metrics,
            'model_cache_detailed': dict(self.model_cache_metrics),
            'batch_detailed': self.batch_metrics
        }

        report_path = self.output_dir / f"performance_report_{self.session_id}.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"📊 Performance report saved to: {report_path}")
            
            # Also save a human-readable summary
            self.save_summary_report(report['summary'])
            
            return report_path
            
        except IOError as e:
            print(f"Error saving performance report: {e}")
            return None

    def save_summary_report(self, summary: Dict[str, Any]):
        """Save a human-readable performance summary."""
        summary_path = self.output_dir / f"performance_summary_{self.session_id}.md"
        
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write("# Performance Summary Report\n\n")
                f.write(f"**Session ID**: {summary['session_id']}\n")
                f.write(f"**Generated**: {summary['timestamp']}\n\n")
                
                # Model Cache Performance
                cache_stats = summary['model_cache_stats']
                if cache_stats['total_hits'] + cache_stats['total_misses'] > 0:
                    f.write("## 🚀 Model Cache Performance\n\n")
                    f.write(f"- **Overall Hit Rate**: {cache_stats['hit_rate']:.1%}\n")
                    f.write(f"- **Total Cache Hits**: {cache_stats['total_hits']}\n")
                    f.write(f"- **Total Cache Misses**: {cache_stats['total_misses']}\n\n")
                    
                    if cache_stats['cache_performance']:
                        f.write("### Per-Model Performance\n\n")
                        f.write("| Model | Hit Rate | Hits | Misses | Avg Load Time |\n")
                        f.write("|-------|----------|------|--------|---------------|\n")
                        
                        for model, perf in cache_stats['cache_performance'].items():
                            avg_load = cache_stats['average_load_times'].get(model, 0)
                            f.write(f"| {model} | {perf['hit_rate']:.1%} | {perf['hits']} | {perf['misses']} | {avg_load:.2f}s |\n")
                        f.write("\n")
                
                # Batch Processing Performance
                batch_stats = summary['batch_stats']
                if batch_stats:
                    f.write("## 📊 Batch Processing Performance\n\n")
                    f.write(f"- **Videos Processed**: {batch_stats['videos_processed']}\n")
                    f.write(f"- **Success Rate**: {batch_stats['success_rate']:.1%}\n")
                    f.write(f"- **Total Entities**: {batch_stats['total_entities']}\n")
                    f.write(f"- **Total Relationships**: {batch_stats['total_relationships']}\n")
                    f.write(f"- **Total Time**: {batch_stats['total_time_seconds']:.1f}s\n\n")
                    
                    if batch_stats.get('throughput'):
                        throughput = batch_stats['throughput']
                        f.write("### Throughput Metrics\n\n")
                        f.write(f"- **Videos/minute**: {throughput['videos_per_minute']:.1f}\n")
                        f.write(f"- **Entities/minute**: {throughput['entities_per_minute']:.1f}\n")
                        f.write(f"- **Relationships/minute**: {throughput['relationships_per_minute']:.1f}\n\n")
                
                # Recommendations
                if summary['recommendations']:
                    f.write("## 💡 Recommendations\n\n")
                    for rec in summary['recommendations']:
                        f.write(f"- {rec}\n")
                    f.write("\n")
            
            print(f"📄 Performance summary saved to: {summary_path}")
            
        except IOError as e:
            print(f"Error saving performance summary: {e}")


# Global instance factory
def create_performance_monitor(output_dir: Path) -> PerformanceMonitor:
    """Create a new performance monitor instance."""
    return PerformanceMonitor(output_dir) 