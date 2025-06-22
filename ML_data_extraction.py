import pandas as pd
import os
import shutil

data_path = "C:\\Users\\bobwa\\OneDrive\\Desktop\\Test_extract"
extract_col = 'Age_Cls'

# Path to the Excel file
csv_file = os.path.join(data_path, 'Test_extract_Count.csv')
# excel_file = "C:\\Users\\bobwa\\OneDrive\\Desktop\\Test_extract\\Test_extract_Count.csv"  # Replace with your Excel file path

# Base destination path
dest_base_path = os.path.join(data_path, 'cls_results')
# dest_base_path = './cls_results'

# Read the Excel file
df = pd.read_csv(csv_file)

# Ensure destination base path exists
os.makedirs(dest_base_path, exist_ok=True)

# Iterate through each row in the DataFrame
for index, row in df.iterrows():
    folder_name = row['Folder']
    col_class = row[extract_col]

    # Define source and destination paths
    source_path = os.path.join(data_path, folder_name)  # Use data_path for source folders
    dest_path = os.path.join(dest_base_path, col_class, folder_name)

    # Create age class directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Check if source folder exists
    if os.path.exists(source_path) and os.path.isdir(source_path):
        try:
            # Copy the folder to the destination
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            print(f"Copied {folder_name} to {dest_path}")
        except Exception as e:
            print(f"Error moving {folder_name}: {e}")
    else:
        print(f"Source folder {folder_name} does not exist")