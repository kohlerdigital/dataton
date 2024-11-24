import pandas as pd
import os
from pathlib import Path

def get_project_root():
    """Get the project root directory by looking for data/raw directory"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "data" / "raw").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (data/raw directory not found)")

# Define base paths
try:
    BASE_DIR = get_project_root()
    RAW_DATA_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
    
    print(f"Found project root at: {BASE_DIR}")
    print(f"Raw data directory: {RAW_DATA_DIR}")
    print(f"Processed data directory: {PROCESSED_DATA_DIR}")
except Exception as e:
    print(f"Error finding directories: {str(e)}")
    raise

def ensure_output_dirs():
    """Create output directories if they don't exist."""
    (PROCESSED_DATA_DIR / "work").mkdir(parents=True, exist_ok=True)
    (PROCESSED_DATA_DIR / "habitants").mkdir(parents=True, exist_ok=True)

def read_and_print_sample(file_path):
    """Read a CSV file and print first few rows to understand its structure."""
    print(f"\nReading file: {file_path}")
    df = pd.read_csv(file_path)
    print("\nColumns:", df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    return df

def clean_habitants_data():
    """Clean the employed people data from habitants directory."""
    input_path = RAW_DATA_DIR / "habitants" / "fjoldi_starfandi.csv"
    
    print(f"\nReading habitants data from: {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read and display sample of the data to understand structure
    df = read_and_print_sample(input_path)
    
    # Filter for 2023 data (we'll confirm the actual year column name from the output)
    year_col = [col for col in df.columns if 'year' in col.lower() or 'ar' in col.lower()]
    if year_col:
        print(f"\nFound year column: {year_col[0]}")
        df_2023 = df[df[year_col[0]] == 2023].copy()
    else:
        print("\nWarning: No year column found. Processing all data.")
        df_2023 = df.copy()
    
    # Clean column names (remove spaces, lowercase)
    df_2023.columns = df_2023.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Remove any duplicate entries
    df_2023 = df_2023.drop_duplicates()
    
    # Save the cleaned data
    output_path = PROCESSED_DATA_DIR / "habitants" / "employed_2023.csv"
    df_2023.to_csv(output_path, index=False)
    print(f"\nSaved cleaned habitants data to {output_path}")
    
    return df_2023

def clean_work_data():
    """Clean the data from work directory."""
    input_path = RAW_DATA_DIR / "work" / "fjoldi_starfandi.csv"
    
    print(f"\nReading work data from: {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read and display sample of the data to understand structure
    df = read_and_print_sample(input_path)
    
    # Filter for 2023 data (we'll confirm the actual year column name from the output)
    year_col = [col for col in df.columns if 'year' in col.lower() or 'ar' in col.lower()]
    if year_col:
        print(f"\nFound year column: {year_col[0]}")
        df_2023 = df[df[year_col[0]] == 2023].copy()
    else:
        print("\nWarning: No year column found. Processing all data.")
        df_2023 = df.copy()
    
    # Clean column names (remove spaces, lowercase)
    df_2023.columns = df_2023.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Remove any duplicate entries
    df_2023 = df_2023.drop_duplicates()
    
    # Save the cleaned data
    output_path = PROCESSED_DATA_DIR / "work" / "employed_2023.csv"
    df_2023.to_csv(output_path, index=False)
    print(f"\nSaved cleaned work data to {output_path}")
    
    return df_2023

def main():
    """Main function to execute the data cleaning pipeline."""
    print("\nStarting data cleaning process...")
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    try:
        # Clean data from habitants directory
        habitants_df = clean_habitants_data()
        print(f"\nSuccessfully cleaned habitants data. Shape: {habitants_df.shape}")
        
        # Clean data from work directory
        work_df = clean_work_data()
        print(f"\nSuccessfully cleaned work data. Shape: {work_df.shape}")
        
        print("\nData cleaning completed successfully!")
        
    except Exception as e:
        print(f"\nError during data cleaning: {str(e)}")
        raise

if __name__ == "__main__":
    main()
    