from typing import List, Dict, Tuple
from shapely.geometry import Point, shape, Polygon
from shapely.validation import make_valid
import pyproj
from functools import partial
import numpy as np

def create_geodesic_buffer(center: Point, radius_meters: float) -> Polygon:
    """
    Create a circular buffer using a local azimuthal equidistant projection.
    
    Args:
        center (Point): Center point of the circle (lon, lat)
        radius_meters (float): Radius in meters
    
    Returns:
        Polygon: A circular buffer using geodesic distances
    """
    # Create the projection centered on our point of interest
    proj_str = f"+proj=aeqd +lat_0={center.y} +lon_0={center.x} +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
    
    # Create projection transformers
    wgs84 = pyproj.CRS('EPSG:4326')
    aeqd = pyproj.CRS(proj_str)
    project = pyproj.Transformer.from_crs(wgs84, aeqd, always_xy=True).transform
    unproject = pyproj.Transformer.from_crs(aeqd, wgs84, always_xy=True).transform
    
    # Create a circle in projected coordinates
    angles = np.linspace(0, 2*np.pi, 64)
    circle_points = [(radius_meters*np.cos(θ), radius_meters*np.sin(θ)) for θ in angles]
    
    # Convert back to geographic coordinates
    buffer_points = [unproject(x, y) for x, y in circle_points]
    
    # Create and return the polygon
    return Polygon(buffer_points)

def calculate_area_coverage(geom1: Polygon, geom2: Polygon, center_lat: float) -> Tuple[float, float]:
    """
    Calculate the area of intersection and total area using a local projection.
    
    Args:
        geom1 (Polygon): First geometry
        geom2 (Polygon): Second geometry
        center_lat (float): Latitude for the local projection
    
    Returns:
        Tuple[float, float]: (intersection area, total area) in square meters
    """
    # Create a local projection centered on the area
    proj_str = f"+proj=laea +lat_0={center_lat} +lon_0={geom1.centroid.x} +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
    
    # Create projection transformer
    wgs84 = pyproj.CRS('EPSG:4326')
    local = pyproj.CRS(proj_str)
    project = pyproj.Transformer.from_crs(wgs84, local, always_xy=True).transform
    
    # Project both geometries
    geom1_proj = transform_geometry(geom1, project)
    geom2_proj = transform_geometry(geom2, project)
    
    # Calculate areas
    intersection_area = geom1_proj.intersection(geom2_proj).area
    total_area = geom1_proj.area
    
    return intersection_area, total_area

def transform_geometry(geom, project):
    """Transform a geometry using the given projection function."""
    if geom.is_empty:
        return geom
    if geom.geom_type == 'Polygon':
        shell = transform_coords(geom.exterior.coords, project)
        holes = [transform_coords(interior.coords, project) for interior in geom.interiors]
        return Polygon(shell, holes)
    raise ValueError(f"Unsupported geometry type: {geom.geom_type}")

def transform_coords(coords, project):
    """Transform a sequence of coordinates using the given projection function."""
    return [project(x, y) for x, y in coords]

def calculate_station_coverage(
    small_areas: List[Dict], 
    station_coords: Tuple[float, float], 
    radius_meters: float
) -> List[Dict]:
    """
    Calculate the coverage area of a station within its radius and identify intersecting small areas.

    Args:
        small_areas (List[Dict]): List of small area geometries with their coordinates.
        station_coords (Tuple[float, float]): Station coordinates (lon, lat) in EPSG:4326.
        radius_meters (float): Coverage radius in meters.

    Returns:
        List[Dict]: List of covered areas with their coverage percentages.
    """
    try:
        # Ensure station_coords is a single point
        if isinstance(station_coords, (list, tuple)):
            if len(station_coords) == 2 and all(isinstance(x, (int, float)) for x in station_coords):
                # Single point coordinates
                station_point = Point(station_coords)
            elif len(station_coords) > 2:
                # If it's a list of coordinates, use the first point
                station_point = Point(station_coords[0])
            else:
                raise ValueError(f"Invalid station coordinates format: {station_coords}")
        else:
            raise ValueError(f"Station coordinates must be a tuple or list, got {type(station_coords)}")

        # Create station buffer
        station_buffer = create_geodesic_buffer(station_point, radius_meters)
        
        covered_areas = []
        for area in small_areas:
            try:
                # Create polygon from coordinates
                if isinstance(area, str):
                    # If area is a string (area ID), skip it
                    continue
                    
                coordinates = area.get("geometry") if isinstance(area, dict) else area
                if not coordinates:
                    continue
                    
                area_geom = Polygon(coordinates)
                
                # Fix invalid geometries if needed
                if not area_geom.is_valid:
                    area_geom = make_valid(area_geom)
                
                # Check if area intersects with station buffer
                if area_geom.intersects(station_buffer):
                    # Calculate areas using proper projection
                    intersection_area, total_area = calculate_area_coverage(
                        area_geom,
                        station_buffer,
                        station_point.y  # Use station latitude for projection
                    )
                    
                    # Calculate coverage percentage
                    area_coverage = (intersection_area / total_area) * 100 if total_area > 0 else 0
                    
                    area_id = area.get("id") if isinstance(area, dict) else str(area)
                    covered_areas.append({
                        "id": area_id,
                        "area_coverage_percent": area_coverage
                    })
                    
                    print(f"Area {area_id}: {area_coverage:.1f}% coverage")  # Debug print
                    
            except Exception as e:
                print(f"Error processing area {area if isinstance(area, str) else area.get('id', 'unknown')}: {str(e)}")
                continue
        
        return covered_areas
        
    except Exception as e:
        print(f"Error in calculate_station_coverage: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def get_affected_areas_string(
    small_areas: List[Dict], 
    station_coords: Tuple[float, float], 
    radius_meters: float
) -> str:
    """
    Get a formatted string of affected area IDs and their coverage percentages.

    Args:
        small_areas (List[Dict]): List of small area geometries with their coordinates.
        station_coords (Tuple[float, float]): Station coordinates (lon, lat) in EPSG:4326.
        radius_meters (float): Coverage radius in meters.

    Returns:
        str: Formatted string of affected areas with percentages
    """
    covered_areas = calculate_station_coverage(small_areas, station_coords, radius_meters)
    area_strings = [
        f"{area['id']} ({area['area_coverage_percent']:.1f}%)" 
        for area in covered_areas
    ]
    return f"Affected areas: {', '.join(area_strings)}"
