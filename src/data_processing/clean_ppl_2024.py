import pandas as pd
import os

def clean_habitants_data():
   # Create paths
   input_path = os.path.join('data', 'raw', 'habitants', 'ibuafjoldi.csv') 
   output_dir = os.path.join('data', 'processed', 'habitants')
   output_file = os.path.join(output_dir, 'habitant_2023.csv')

   # Read CSV
   df = pd.read_csv(input_path)
   
   # Filter for year 2024
   df_2023 = df[df['ar'] == 2023]
   
   # Save cleaned data
   df_2023.to_csv(output_file, index=False)

if __name__ == "__main__":
   clean_habitants_data()