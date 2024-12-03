# src/transformation.py

import json
import os
from pathlib import Path
from pyproj import Transformer
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoordinateTransformer:
    def __init__(self):
        self.transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")
        
    def transform_coordinates(self, x: float, y: float) -> tuple:
        """Transform coordinates from EPSG:3857 to EPSG:4326."""
        try:
            lat, lon = self.transformer.transform(x, y)
            return [lon, lat]  # GeoJSON standard is [longitude, latitude]
        except Exception as e:
            logger.error(f"Error transforming coordinates {x}, {y}: {str(e)}")
            raise

    def transform_geometry(self, geometry: dict) -> dict:
        """Transform geometry coordinates based on geometry type."""
        if geometry['type'] == 'Point':
            geometry['coordinates'] = self.transform_coordinates(
                geometry['coordinates'][0],
                geometry['coordinates'][1]
            )
        elif geometry['type'] == 'LineString':
            geometry['coordinates'] = [
                self.transform_coordinates(x, y) 
                for x, y in geometry['coordinates']
            ]
        elif geometry['type'] == 'Polygon':
            geometry['coordinates'] = [
                [self.transform_coordinates(x, y) for x, y in ring]
                for ring in geometry['coordinates']
            ]
        elif geometry['type'] == 'MultiPoint':
            geometry['coordinates'] = [
                self.transform_coordinates(x, y) 
                for x, y in geometry['coordinates']
            ]
        elif geometry['type'] == 'MultiLineString':
            geometry['coordinates'] = [
                [self.transform_coordinates(x, y) for x, y in line]
                for line in geometry['coordinates']
            ]
        elif geometry['type'] == 'MultiPolygon':
            geometry['coordinates'] = [
                [[self.transform_coordinates(x, y) for x, y in ring]
                 for ring in polygon]
                for polygon in geometry['coordinates']
            ]
        return geometry

    def transform_geojson(self, geojson_data: dict) -> dict:
        """Transform all geometries in a GeoJSON object."""
        transformed_geojson = geojson_data.copy()
        
        # Update CRS to WGS84
        transformed_geojson['crs'] = {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::4326"
            }
        }
        
        # Transform each feature's geometry
        for feature in transformed_geojson['features']:
            feature['geometry'] = self.transform_geometry(feature['geometry'])
            
        return transformed_geojson

def process_files():
    """Process all GeoJSON files in the data/raw/geo directory."""
    # Setup paths
    current_dir = Path(__file__).parent.parent  # Get project root directory
    input_dir = current_dir / 'data' / 'raw' / 'geo'
    output_dir = current_dir / 'data' / 'processed'
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize transformer
    transformer = CoordinateTransformer()
    
    # Process each .geojson file in the input directory
    for file_path in input_dir.glob('*.geojson'):
        try:
            logger.info(f"Processing file: {file_path.name}")
            
            # Read input file
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            # Transform coordinates
            transformed_data = transformer.transform_geojson(geojson_data)
            
            # Write output file
            output_path = output_dir / f"{file_path.stem}_4326.geojson"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transformed_data, f, indent=2)
            
            logger.info(f"Successfully transformed {file_path.name} to {output_path.name}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")

if __name__ == "__main__":
    process_files()