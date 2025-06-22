import os
import csv
from pathlib import Path


def count_png_images_in_folder(folder_path):
    # Initialize result list for multiple folders
    results = []

    # Walk through all subdirectories in the parent folder
    for root, dirs, files in os.walk(folder_path):
        if os.path.basename(root) == 'Enhanced':
            # Get the parent folder name (one level up from Enhanced)
            parent_folder = os.path.basename(os.path.dirname(root))

            # Initialize counters for this folder
            trace_count = 0
            retrace_count = 0
            ns_trace_count = 0
            ns_retrace_count = 0

            # Check subfolders of Enhanced
            for subfolder in os.listdir(root):
                subfolder_path = os.path.join(root, subfolder)
                if os.path.isdir(subfolder_path):
                    # Count PNG files in each relevant subfolder
                    subfolder_lower = subfolder.lower()
                    png_files = [f for f in os.listdir(subfolder_path)
                                 if f.lower().endswith('.png')]

                    if subfolder_lower == 'dafm_trace':
                        trace_count = len(png_files)
                    elif subfolder_lower == 'dafm_retrace':
                        retrace_count = len(png_files)
                    elif subfolder_lower == 'ns_trace':
                        ns_trace_count = len(png_files)
                    elif subfolder_lower == 'ns_retrace':
                        ns_retrace_count = len(png_files)

            # Only add to results if there are any counts
            if trace_count > 0 or retrace_count > 0 or ns_trace_count > 0 or ns_retrace_count:
                results.append({
                    'Folder': parent_folder,
                    'DAFM_Trace': trace_count,
                    'DAFM_Retrace': retrace_count,
                    'NS_Trace': ns_trace_count,
                    'NS_Retrace': ns_retrace_count
                })

    return results


def main():
    # Parent folder path (modify this to your actual path)
    parent_folder = r'C:\Users\bobwa\OneDrive\Desktop\Test_extract'

    # Get counts for all subfolders
    results = count_png_images_in_folder(parent_folder)

    if not results:
        print("No Enhanced folders with images found!")
        return

    # Prepare CSV output path in the parent folder
    csv_filename = os.path.join(parent_folder, f'{os.path.basename(parent_folder)}_Count.csv')

    # Write to CSV
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Folder', 'DAFM_Trace', 'DAFM_Retrace', 'NS_Trace', 'NS_Retrace']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    # Print results to console
    print(f"Image counts for subfolders in {os.path.basename(parent_folder)}:")
    for result in results:
        print(f"\nFolder: {result['Folder']}")
        print(f"DAFM_Trace: {result['DAFM_Trace']}")
        print(f"DAFM_Retrace: {result['DAFM_Retrace']}")
        print(f"NS_Trace: {result['NS_Trace']}")
        print(f"NS_Retrace: {result['NS_Retrace']}")
    print(f"\nResults saved to {csv_filename}")


if __name__ == "__main__":
    main()