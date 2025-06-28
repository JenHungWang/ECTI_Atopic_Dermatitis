# Copyright 2024 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)

import sys
import glob
from pathlib import Path
from utils.Img_Preprocessing import *
import shutil
from config.global_settings import import_config_dict

# folder path
DATA_PATH = "/Users/jen-hung/Desktop/Test12/"
DIR_NAME = Path(os.path.dirname(__file__))
warnings.filterwarnings('ignore')  # Suppress warnings
np.set_printoptions(threshold=sys.maxsize)  # Print full numpy arrays


def main(folder_dir):
    # Search folder path
    folder_list = []
    for folderName in glob.glob(folder_dir + os.sep + '*'):
        folder = folderName.split(os.sep)[-1]
        folder_list.append(folder)
    folder_list.sort()
    print("Detected Folders", folder_list)

    for folder in folder_list:
        run_preprocessing = True
        file_list = []
        file_type = "bcr"

        # Paths with trace and retrace subfolders
        original_trace_path = os.path.join(folder_dir, "Result", folder, "Original", "DAFM_Trace")
        original_retrace_path = os.path.join(folder_dir, "Result", folder, "Original", "DAFM_Retrace")
        original_ns_trace_path = os.path.join(folder_dir, "Result", folder, "Original", "NS_Trace")
        original_ns_retrace_path = os.path.join(folder_dir, "Result", folder, "Original", "NS_Retrace")
        enhanced_trace_path = os.path.join(folder_dir, "Result", folder, "Enhanced", "DAFM_Trace")
        enhanced_retrace_path = os.path.join(folder_dir, "Result", folder, "Enhanced", "DAFM_Retrace")
        enhanced_ns_trace_path = os.path.join(folder_dir, "Result", folder, "Enhanced", "NS_Trace")
        enhanced_ns_retrace_path = os.path.join(folder_dir, "Result", folder, "Enhanced", "NS_Retrace")

        try:
            os.makedirs(original_trace_path, exist_ok=True)
            os.makedirs(original_retrace_path, exist_ok=True)
            os.makedirs(original_ns_trace_path, exist_ok=True)
            os.makedirs(original_ns_retrace_path, exist_ok=True)
            os.makedirs(enhanced_trace_path, exist_ok=True)
            os.makedirs(enhanced_retrace_path, exist_ok=True)
            os.makedirs(enhanced_ns_trace_path, exist_ok=True)
            os.makedirs(enhanced_ns_retrace_path, exist_ok=True)

            # Check all subdirectories for emptiness
            if not os.listdir(enhanced_trace_path) and not os.listdir(enhanced_retrace_path):
                print("Directory is empty")
                run_preprocessing = True
            else:
                print("Directory is not empty")
                run_preprocessing = False
        except OSError as error:
            print("Directory can not be created")

        encyc = []
        walk = os.walk(folder_dir)
        for d, sd, files in walk:
            directory = d.split(os.sep)[-1]
            for fn in files:
                # Check for both trace and retrace BCR files
                if (fn[0:2] != "._" and
                   (fn.lower().endswith('_trace.bcr') or fn.lower().endswith('_retrace.bcr')) and directory == folder):
                    encyc.append(d + os.sep + fn)
                    file_type = "bcr"
                elif (fn[0:2] != "._" and
                      fn.lower().endswith('.nid') and
                      directory == folder):
                    encyc.append(d + os.sep + fn)
                    file_type = "nid"
        encyc.sort()
        print("Files: ", encyc)
        print("File type: ", file_type)

        # Image preprocessing with trace/retrace separation
        if run_preprocessing:
            for i, fn in enumerate(encyc):
                if fn.lower().endswith('_trace.bcr'):
                    file = treat_one_image(fn, original_trace_path, enhanced_trace_path, file_type)
                    file_list.append(file)
                elif fn.lower().endswith('_retrace.bcr'):
                    file = treat_one_image(fn, original_retrace_path, enhanced_retrace_path, file_type)
                    file_list.append(file)
                elif file_type == "nid":
                    file = treat_one_image(fn, original_ns_trace_path, enhanced_ns_trace_path, file_type)
                    file_list.extend(file)
                print(i, end=' ')
        else:
            for i, fn in enumerate(encyc):
                base = os.path.split(fn)[1][0:-10]
                if file_type == 'nid':
                    # For .nid, add names based on direction
                    if "_OB" in fn:
                        file_list.append(f"{base}_backward")
                    elif "_OF" in fn:
                        file_list.append(f"{base}_forward")
                    else:
                        file_list.extend([f"{base}_backward", f"{base}_forward"])
                else:
                    file_list.append(base)

        if file_type == 'nid':
            # Loop through and move files
            for filename in os.listdir(original_ns_trace_path):
                if 'backward' in filename and filename.endswith('.png'):
                    src = os.path.join(original_ns_trace_path, filename)
                    dst = os.path.join(original_ns_retrace_path, filename)
                    shutil.move(src, dst)
            for filename in os.listdir(enhanced_ns_trace_path):
                if 'backward' in filename and filename.endswith('.png'):
                    src = os.path.join(enhanced_ns_trace_path, filename)
                    dst = os.path.join(enhanced_ns_retrace_path, filename)
                    shutil.move(src, dst)
                    # print(f"Moved: {filename}")


if __name__ == "__main__":
    main(DATA_PATH)

