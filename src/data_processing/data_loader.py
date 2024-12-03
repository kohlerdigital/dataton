import pandas as pd
import geopandas as gpd
import os
from pathlib import Path
import fiona
from shapely.geometry import shape, Point
from functools import lru_cache

class DataLoader:
    def __init__(self):
        self.base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.processed_path = self.base_path / 'data' / 'processed'
        # Cache for loaded data
        self._population_data = None
        self._small_areas = None
        self._affected_areas_cache = {}
        self._schools_data = None

    def load_schools_data(self, force=False):
        """Load schools data with caching"""
        if not force and self._schools_data is not None:
            return self._schools_data

        try:
            file_path = self.base_path / 'data' / 'raw' / 'geo' / 'schools.csv'
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Schools data not found at {file_path}")
            
            # Read CSV with latin1 encoding for Icelandic characters
            df = pd.read_csv(str(file_path), encoding='latin1')
            self._schools_data = gpd.GeoDataFrame(
                df,
                geometry=[Point(xy) for xy in zip(df['Location Lng'], df['Location Lat'])],
                crs="EPSG:4326"
            )
            return self._schools_data
        except Exception as e:
            print(f"Error loading schools data: {e}")
            return gpd.GeoDataFrame(columns=['Name', 'geometry'], crs="EPSG:4326")

    def load_cityline_data(self, year):
        """Load cityline GeoJSON data for a specific year"""
        try:
            file_path = str(self.processed_path / f'cityline_{year}_4326.geojson')
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Cityline data for year {year} not found at {file_path}")
            
            # Use fiona to read the file
            with fiona.open(file_path) as collection:
                features = list(collection)
                
            # Convert to GeoDataFrame
            geometries = [shape(feature['geometry']) for feature in features]
            properties = [feature['properties'] for feature in features]
            
            gdf = gpd.GeoDataFrame(properties, geometry=geometries, crs="EPSG:4326")
            return gdf
            
        except Exception as e:
            print(f"Error loading cityline data: {e}")
            # Return empty GeoDataFrame with expected columns
            return gpd.GeoDataFrame(columns=['geometry', 'line'], crs="EPSG:4326")

    def load_population_data(self, force=False):
        """Load population data with caching"""
        if not force and self._population_data is not None:
            return self._population_data

        try:
            file_path = self.processed_path / 'habitants' / 'habitant_2024.csv'
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Population data not found at {file_path}")
            self._population_data = pd.read_csv(str(file_path))
            # Convert smasvaedi to string to match small areas
            self._population_data['smasvaedi'] = self._population_data['smasvaedi'].astype(str)
            return self._population_data
        except Exception as e:
            print(f"Error loading population data: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['smasvaedi', 'aldursflokkur', 'fjoldi'])

    def load_small_areas(self, force=False):
        """Load small areas GeoJSON data with caching"""
        if not force and self._small_areas is not None:
            return self._small_areas

        try:
            print("\nLOADING SMALL AREAS")
            file_path = str(self.base_path / 'data' / 'smasvaedi_2021.json')
            print(f"File path: {file_path}")
            print(f"File exists: {os.path.exists(file_path)}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Small areas data not found at {file_path}")
            
            # Use fiona to read the file
            with fiona.open(file_path) as collection:
                print(f"Collection CRS: {collection.crs}")
                features = list(collection)
                print(f"Number of features: {len(features)}")
                
            # Convert to GeoDataFrame with original CRS
            geometries = [shape(feature['geometry']) for feature in features]
            properties = [feature['properties'] for feature in features]
            
            print("Creating GeoDataFrame...")
            gdf = gpd.GeoDataFrame(properties, geometry=geometries, crs="EPSG:3057")
            
            # Reproject to EPSG:4326
            print("Reprojecting to EPSG:4326...")
            self._small_areas = gdf.to_crs("EPSG:4326")
            
            print(f"GeoDataFrame shape: {self._small_areas.shape}")
            print(f"GeoDataFrame columns: {self._small_areas.columns}")
            print(f"GeoDataFrame CRS: {self._small_areas.crs}")
            
            # Convert smsv to string to match population data
            self._small_areas['smsv'] = self._small_areas['smsv'].astype(str)
            
            # Create spatial index for faster intersection queries
            self._small_areas = self._small_areas.set_index('smsv')
            print("Small areas loaded successfully")
            return self._small_areas
            
        except Exception as e:
            print(f"Error loading small areas data: {e}")
            import traceback
            traceback.print_exc()
            # Return empty GeoDataFrame with expected columns
            return gpd.GeoDataFrame(columns=['geometry', 'smsv'], crs="EPSG:4326")

    def get_age_distribution(self, area_ids=None):
        """Calculate age distribution for given areas"""
        try:
            if not area_ids:
                return {}

            population_data = self.load_population_data()
            if area_ids:
                population_data = population_data[population_data['smasvaedi'].isin(area_ids)]
            
            age_groups = population_data.groupby('aldursflokkur')['fjoldi'].sum()
            return age_groups.to_dict()
        except Exception as e:
            print(f"Error calculating age distribution: {e}")
            return {}

    def get_total_population(self, area_ids=None):
        """Calculate total population for given areas"""
        try:
            if not area_ids:
                return 0

            population_data = self.load_population_data()
            if area_ids:
                population_data = population_data[population_data['smasvaedi'].isin(area_ids)]
            return population_data['fjoldi'].sum()
        except Exception as e:
            print(f"Error calculating total population: {e}")
            return 0

    def _get_cache_key(self, point, radius):
        """Generate a cache key for affected areas"""
        return f"{point.wkt}_{radius}"

    def get_areas_within_radius(self, point, radius, small_areas=None):
        """Get all small areas within radius of a point"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(point, radius)
            if cache_key in self._affected_areas_cache:
                return self._affected_areas_cache[cache_key]

            if small_areas is None:
                small_areas = self.load_small_areas()
            
            # Create a buffer around the point
            point_buffer = point.buffer(radius / 111000)  # Convert meters to approximate degrees
            
            # Find all areas that intersect with the buffer
            intersecting_areas = small_areas[small_areas.intersects(point_buffer)].copy()
            
            # Cache the result
            self._affected_areas_cache[cache_key] = intersecting_areas
            
            # Limit cache size
            if len(self._affected_areas_cache) > 100:
                # Remove oldest entries
                oldest_keys = list(self._affected_areas_cache.keys())[:50]
                for key in oldest_keys:
                    del self._affected_areas_cache[key]
            
            return intersecting_areas
        except Exception as e:
            print(f"Error finding areas within radius: {e}")
            return gpd.GeoDataFrame(columns=['geometry', 'smsv'], crs="EPSG:4326")

    def get_station_statistics(self, station_coord, radius):
        """Get statistics for areas around a station"""
        try:
            # Convert station coordinates to Point
            point = Point(station_coord)
            
            # Get areas within radius
            small_areas = self.load_small_areas()
            affected_areas = self.get_areas_within_radius(point, radius, small_areas)
            area_ids = affected_areas.index.tolist()  # Using index since we set it to smsv

            # Calculate statistics
            stats = {
                'total_population': self.get_total_population(area_ids),
                'age_distribution': self.get_age_distribution(area_ids),
                'affected_areas': len(area_ids)
            }

            return stats
        except Exception as e:
            print(f"Error calculating station statistics: {e}")
            return {
                'total_population': 0,
                'age_distribution': {},
                'affected_areas': 0
            }

    def clear_caches(self):
        """Clear all cached data"""
        self._population_data = None
        self._small_areas = None
        self._affected_areas_cache.clear()
        self._schools_data = None
