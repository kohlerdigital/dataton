import pandas as pd
import os
from .station_coverage import calculate_station_coverage

def calculate_age_group_percentages(station_coords, radius_meters, small_areas):
    """
    Calculate population statistics for specific age groups affected by a station's radius.
    
    Args:
        station_coords (tuple): Station coordinates (lon, lat)
        radius_meters (float): Coverage radius in meters
        small_areas (list): List of small area geometries with their coordinates
        
    Returns:
        dict: Population statistics for each age group
    """
    try:
        # Get covered areas and their percentages
        covered_areas = calculate_station_coverage(small_areas, station_coords, radius_meters)
        
        # Read population data for 2024
        population_path = os.path.join('data', 'processed', 'habitants', 'habitant_2024.csv')
        population_df = pd.read_csv(population_path, encoding='utf-8')
        
        # Define age groups we're interested in
        target_age_groups = ['10-14 ára', '15-19 ára', '20-24 ára']
        
        # Initialize results dictionary
        result = {age_group: {'total': 0, 'within_radius': 0} for age_group in target_age_groups}
        
        # Calculate total population for each age group (across all areas)
        for age_group in target_age_groups:
            # Sum fjoldi for this age group across all areas and both genders
            total = population_df[population_df['aldursflokkur'] == age_group]['fjoldi'].sum()
            result[age_group]['total'] = total
        
        # Calculate population within radius for each age group
        for area in covered_areas:
            area_id = area['id']
            coverage_percent = area['area_coverage_percent'] / 100  # Convert percentage to decimal
            
            # Filter population data for this specific area
            area_pop = population_df[population_df['smasvaedi'].astype(str) == str(area_id)]
            
            # Calculate affected population for each age group
            for age_group in target_age_groups:
                # Sum fjoldi for this age group in this area (both genders)
                age_pop = area_pop[area_pop['aldursflokkur'] == age_group]['fjoldi'].sum()
                # Multiply by coverage percentage to get population within radius
                result[age_group]['within_radius'] += age_pop * coverage_percent
        
        return result
        
    except Exception as e:
        print(f"Error calculating age group statistics: {e}")
        import traceback
        traceback.print_exc()
        return {}

def format_age_group_info(data):
    """
    Format age group data into display lines.
    
    Args:
        data (dict): Dictionary containing total and within_radius counts for each age group
        
    Returns:
        list: Formatted strings for each age group
    """
    # Calculate totals across all age groups
    total_within_radius = sum(int(group_data['within_radius']) for group_data in data.values())
    total_population = sum(group_data['total'] for group_data in data.values())
    
    return [
        "In the affected small areas, there are:",
        f"{int(data['10-14 ára']['total'])} of age group 10-14 ; {int(data['10-14 ára']['within_radius'])} is within the radius",
        f"{int(data['15-19 ára']['total'])} of age group 15-19 ; {int(data['15-19 ára']['within_radius'])} is within the radius",
        f"{int(data['20-24 ára']['total'])} of age group 20-24 ; {int(data['20-24 ára']['within_radius'])} is within the radius",
        f"{total_population} total ; {total_within_radius} total within radius"
    ]
