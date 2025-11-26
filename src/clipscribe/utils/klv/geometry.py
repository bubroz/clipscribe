"""
KLV Geometry Utilities.

Calculates geospatial relationships, look vectors, and sensor footprints
based on MISB ST 0601 metadata.
"""

import math
from typing import Dict, List, Tuple, Optional

def calculate_look_vector(sensor_lat: float, sensor_lon: float, sensor_alt: float,
                          target_lat: float, target_lon: float, target_elev: float = 0) -> Dict:
    """
    Calculate the look vector from sensor to target.
    
    Args:
        sensor_lat: Latitude of the drone (degrees)
        sensor_lon: Longitude of the drone (degrees)
        sensor_alt: Altitude of the drone (meters MSL)
        target_lat: Latitude of the frame center (degrees)
        target_lon: Longitude of the frame center (degrees)
        target_elev: Elevation of the frame center (meters MSL, default 0)
        
    Returns:
        Dict containing:
        - distance: Slant range in meters
        - bearing: Azimuth from sensor to target (degrees)
        - depression_angle: Angle down from horizon (degrees)
    """
    # Simple Haversine/Trig approximation for short distances (flat earth assumption locally)
    # For high precision long-range, would need WGS84 geodetic libs (like pyproj),
    # but we want to keep this zero-dependency if possible.
    
    # Radius of Earth (mean)
    R = 6371000.0
    
    d_lat = math.radians(target_lat - sensor_lat)
    d_lon = math.radians(target_lon - sensor_lon)
    lat1 = math.radians(sensor_lat)
    lat2 = math.radians(target_lat)
    
    # Ground distance (Haversine)
    a = math.sin(d_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    ground_dist = R * c
    
    # Altitude difference
    alt_diff = sensor_alt - target_elev
    
    # Slant range (Pythagorean)
    slant_range = math.sqrt(ground_dist**2 + alt_diff**2)
    
    # Bearing (Forward Azimuth)
    y = math.sin(d_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    bearing = math.degrees(math.atan2(y, x))
    bearing = (bearing + 360) % 360
    
    # Depression Angle
    # tan(angle) = opp/adj = alt_diff / ground_dist
    if ground_dist > 0:
        depression_angle = math.degrees(math.atan(alt_diff / ground_dist))
    else:
        depression_angle = 90.0 if alt_diff > 0 else -90.0
        
    return {
        "slant_range": slant_range,
        "ground_range": ground_dist,
        "bearing": bearing,
        "depression_angle": depression_angle
    }

def interpolate_location(p1: Dict, p2: Dict, fraction: float) -> Dict:
    """
    Linearly interpolate between two telemetry points.
    Useful for finding drone location between 1Hz updates.
    
    Args:
        p1, p2: Dicts with 'SensorLatitude', 'SensorLongitude', 'SensorTrueAltitude'
        fraction: 0.0 to 1.0
        
    Returns:
        Interpolated point dict
    """
    result = {}
    keys = ['SensorLatitude', 'SensorLongitude', 'SensorTrueAltitude', 
            'FrameCenterLatitude', 'FrameCenterLongitude']
            
    for key in keys:
        v1 = p1.get(key)
        v2 = p2.get(key)
        
        if v1 is not None and v2 is not None:
            result[key] = v1 + (v2 - v1) * fraction
            
    return result

