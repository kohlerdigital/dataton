import pandas as pd
import numpy as np
from shapely.geometry import Point
from .data_loader import DataLoader

class Statistics:
    def __init__(self):
        self.data_loader = DataLoader()

    def calculate_station_metrics(self, station_coord, radius):
        """Calculate metrics for a given station and radius"""
        try:
            stats = self.data_loader.get_station_statistics(station_coord, radius)
            
            # Add additional analysis
            if stats['affected_areas'] > 0:
                stats['population_density'] = stats['total_population'] / (np.pi * (radius/1000)**2)  # per km²
            else:
                stats['population_density'] = 0
            
            # Calculate age group percentages
            total_pop = sum(stats['age_distribution'].values()) if stats['age_distribution'] else 0
            if total_pop > 0:
                stats['age_percentages'] = {
                    age: (count/total_pop)*100 
                    for age, count in stats['age_distribution'].items()
                }
            else:
                stats['age_percentages'] = {}
            
            return stats
        except Exception as e:
            print(f"Error in calculate_station_metrics: {e}")
            return {
                'total_population': 0,
                'age_distribution': {},
                'affected_areas': 0,
                'population_density': 0,
                'age_percentages': {}
            }

    def calculate_line_metrics(self, line_coords, radius):
        """Calculate metrics for an entire line"""
        try:
            total_stats = {
                'total_population': 0,
                'age_distribution': {},
                'affected_areas': set(),
                'total_coverage': 0
            }
            
            # Calculate metrics for each station
            for coord in line_coords:
                station_stats = self.data_loader.get_station_statistics(coord, radius)
                
                # Aggregate statistics
                total_stats['total_population'] += station_stats['total_population']
                
                # Aggregate age distribution
                for age, count in station_stats['age_distribution'].items():
                    if age not in total_stats['age_distribution']:
                        total_stats['age_distribution'][age] = 0
                    total_stats['age_distribution'][age] += count
                
                # Track affected areas
                if isinstance(station_stats['affected_areas'], (list, set)):
                    total_stats['affected_areas'].update(station_stats['affected_areas'])
                elif isinstance(station_stats['affected_areas'], int):
                    total_stats['affected_areas'].add(station_stats['affected_areas'])
            
            # Calculate coverage area (approximate, considering overlaps)
            total_stats['total_coverage'] = len(total_stats['affected_areas'])
            total_stats['affected_areas'] = list(total_stats['affected_areas'])
            
            return total_stats
        except Exception as e:
            print(f"Error in calculate_line_metrics: {e}")
            return {
                'total_population': 0,
                'age_distribution': {},
                'affected_areas': [],
                'total_coverage': 0
            }

    def get_population_density_map(self, small_areas=None):
        """Create population density data for small areas"""
        try:
            if small_areas is None:
                small_areas = self.data_loader.load_small_areas()
            
            population_data = self.data_loader.load_population_data()
            
            # Calculate total population per area
            area_population = population_data.groupby('smasvaedi')['fjoldi'].sum().reset_index()
            
            # Merge with small areas
            small_areas_with_density = small_areas.merge(
                area_population,
                left_on='smsv',
                right_on='smasvaedi',
                how='left'
            )
            
            # Fill NaN values with 0
            small_areas_with_density['fjoldi'] = small_areas_with_density['fjoldi'].fillna(0)
            
            # Calculate area in km²
            small_areas_with_density['area_km2'] = small_areas_with_density.geometry.area / 1_000_000
            
            # Calculate density (handle division by zero)
            small_areas_with_density['density'] = np.where(
                small_areas_with_density['area_km2'] > 0,
                small_areas_with_density['fjoldi'] / small_areas_with_density['area_km2'],
                0
            )
            
            return small_areas_with_density
        except Exception as e:
            print(f"Error in get_population_density_map: {e}")
            return small_areas

    def get_age_distribution_chart_data(self, area_ids=None):
        """Get age distribution data formatted for plotting"""
        try:
            age_dist = self.data_loader.get_age_distribution(area_ids)
            
            if not age_dist:
                return {
                    'ages': [],
                    'counts': []
                }
            
            return {
                'ages': list(age_dist.keys()),
                'counts': list(age_dist.values())
            }
        except Exception as e:
            print(f"Error in get_age_distribution_chart_data: {e}")
            return {
                'ages': [],
                'counts': []
            }

    def get_coverage_statistics(self, year, radius):
        """Calculate coverage statistics for a given year"""
        try:
            cityline = self.data_loader.load_cityline_data(year)
            small_areas = self.data_loader.load_small_areas()
            
            # Get all affected areas
            affected_areas = set()
            for _, station in cityline.iterrows():
                point = Point(station.geometry.coords[0])
                areas = self.data_loader.get_areas_within_radius(point, radius, small_areas)
                affected_areas.update(areas.index)
            
            # Calculate statistics
            total_areas = len(small_areas) if not small_areas.empty else 0
            covered_areas = len(affected_areas)
            
            coverage_percentage = (covered_areas / total_areas * 100) if total_areas > 0 else 0
            
            return {
                'total_areas': total_areas,
                'covered_areas': covered_areas,
                'coverage_percentage': coverage_percentage,
                'affected_area_ids': list(affected_areas)
            }
        except Exception as e:
            print(f"Error in get_coverage_statistics: {e}")
            return {
                'total_areas': 0,
                'covered_areas': 0,
                'coverage_percentage': 0,
                'affected_area_ids': []
            }
