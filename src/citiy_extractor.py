import json

def extract_locations(json_file_path, search_terms):
    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # List to store matching features
    matching_features = []
    
    # Iterate through features
    for feature in data['features']:
        # Get properties dictionary
        props = feature['properties']
        
        # Check all property values for any of the search terms
        for value in props.values():
            if isinstance(value, str) and any(term in value for term in search_terms):
                # Keep the entire feature structure
                matching_features.append(feature)
                break  # Once we find a match in this feature, move to next feature
    
    # Create the same structure as input JSON but with filtered features
    output_json = {
        "type": "FeatureCollection",
        "features": matching_features
    }
    
    return output_json

def main():
    # Define search terms
    search_terms = ["Reykjavík", "Mosfellsbær", "Kopavógur"]
    
    # File paths
    input_json_path = "data/smasvaedi_2021.json"  # Replace with your input JSON file path
    output_json_path = "data/processed/geo/capital.json"
    
    try:
        # Extract matching entries
        filtered_data = extract_locations(input_json_path, search_terms)
        
        # Write to new JSON file
        with open(output_json_path, 'w', encoding='utf-8') as outfile:
            json.dump(filtered_data, outfile, ensure_ascii=False, indent=2)
            
        print(f"\nSuccessfully created {output_json_path}")
        print(f"Found {len(filtered_data['features'])} matching entries")
            
    except FileNotFoundError:
        print("Error: Input JSON file not found.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()