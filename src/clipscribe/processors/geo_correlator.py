"""
Geo-Spatial Correlator.

Fuses audio transcript segments with KLV telemetry to create
geospatially aware intelligence events.
"""

import logging
from typing import List, Dict, Optional
from ..utils.klv.geometry import calculate_look_vector, interpolate_location

logger = logging.getLogger(__name__)

class GeoCorrelator:
    """
    Correlates time-based events (transcript) with space-based data (telemetry).
    """
    
    def __init__(self, telemetry: List[Dict]):
        """
        Args:
            telemetry: List of decoded KLV packets (must be sorted by time)
        """
        self.telemetry = sorted(
            [p for p in telemetry if 'PrecisionTimeStamp' in p],
            key=lambda x: x['PrecisionTimeStamp']
        )
        
        if not self.telemetry:
            logger.warning("GeoCorrelator initialized with no valid time-stamped telemetry.")
            self.start_time = 0
            self.end_time = 0
        else:
            self.start_time = self.telemetry[0]['PrecisionTimeStamp']
            self.end_time = self.telemetry[-1]['PrecisionTimeStamp']
            
            # Convert micros to seconds for easier math
            self.start_time_sec = self.start_time / 1_000_000.0

    def correlate(self, transcript_segments: List[Dict]) -> List[Dict]:
        """
        Enrich transcript segments with geospatial context.
        """
        if not self.telemetry:
            return transcript_segments
            
        enriched = []
        
        for segment in transcript_segments:
            # Deep copy to avoid mutating original
            seg = segment.copy()
            
            # Segment time is relative to video start (seconds)
            rel_start = seg.get('start', 0)
            rel_end = seg.get('end', 0)
            mid_point = (rel_start + rel_end) / 2
            
            # Find telemetry at this moment
            # Absolute time = Video Start Time (from KLV) + Relative Offset
            target_abs_time = self.start_time + (mid_point * 1_000_000)
            
            point = self._find_point_at_time(target_abs_time)
            
            if point:
                # Calculate derived geometry
                geo_context = self._build_geo_context(point)
                seg['geoint'] = geo_context
                
                # Heuristic: Was this a "Target Sighting"?
                # If the pilot speaks while the camera is zoomed in (narrow FOV)
                # or looking down (high depression angle), it's likely visual.
                if geo_context.get('fov', 90) < 10:
                    seg['geoint']['likely_visual_observation'] = True
                    
            enriched.append(seg)
            
        return enriched

    def _find_point_at_time(self, target_micros: float) -> Optional[Dict]:
        """
        Find the telemetry packet closest to the given timestamp.
        Uses binary search for efficiency.
        """
        # Bisect left
        low = 0
        high = len(self.telemetry) - 1
        
        while low <= high:
            mid = (low + high) // 2
            mid_val = self.telemetry[mid]['PrecisionTimeStamp']
            
            if mid_val < target_micros:
                low = mid + 1
            elif mid_val > target_micros:
                high = mid - 1
            else:
                return self.telemetry[mid]
        
        # 'low' is the insertion point. Check neighbors.
        if low >= len(self.telemetry):
            return self.telemetry[-1]
        if low == 0:
            return self.telemetry[0]
            
        # Interpolate or return closest?
        # For now, return closest.
        p1 = self.telemetry[low - 1]
        p2 = self.telemetry[low]
        
        if abs(p1['PrecisionTimeStamp'] - target_micros) < abs(p2['PrecisionTimeStamp'] - target_micros):
            return p1
        else:
            return p2

    def _build_geo_context(self, point: Dict) -> Dict:
        """
        Construct the GEOINT context object for a point.
        """
        context = {
            "timestamp": point.get('PrecisionTimeStamp'),
            "sensor": {
                "lat": point.get('SensorLatitude'),
                "lon": point.get('SensorLongitude'),
                "alt": point.get('SensorTrueAltitude'),
                "heading": point.get('PlatformHeadingAngle')
            },
            "target": {
                "lat": point.get('FrameCenterLatitude'),
                "lon": point.get('FrameCenterLongitude'),
                "elev": point.get('FrameCenterElevation', 0)
            }
        }
        
        # Calculate Look Vector if we have both points
        if (context['sensor']['lat'] is not None and 
            context['target']['lat'] is not None):
            
            vector = calculate_look_vector(
                context['sensor']['lat'], context['sensor']['lon'], context['sensor']['alt'],
                context['target']['lat'], context['target']['lon'], context['target']['elev']
            )
            context['vector'] = vector
            
        # Add FOV context
        if 'SensorHorizontalFOV' in point:
            context['fov'] = point['SensorHorizontalFOV']
            
        return context

