from AD_Assessment_QC import cno_detection
import glob
import csv
import os
from pathlib import Path
from config.global_settings import import_config_dict
from ultralytics import YOLO
import time
from datetime import datetime

# Import config files

config_dict = import_config_dict()

# Import source folder path and detection model
DATA_PATH = config_dict['PATH']['source']
MODEL = config_dict['MODEL']['model']
MODEL_PATH = config_dict['MODEL']['folder_path']
CONF = config_dict['MODEL']['conf_threshold']
QC_MODEL = config_dict['QC']['model']
QC_MODEL_PATH = config_dict['QC']['folder_path']
DIR_NAME = Path(os.path.dirname(__file__))

log_file = "qc_error_log.txt"  # You can also use an absolute path if you prefer
folder_dir = "C:/Users/MIDAS/Desktop/QC_Experiments/25_Baby_B9"
cutoff_date = datetime(2025, 8, 27)
model = "YOLOv10-L"
conf = 0.2
DETECTION_MODEL = os.path.join(MODEL_PATH, MODEL)
QC_PREDICTOR = os.path.join(QC_MODEL_PATH, QC_MODEL)
cno_model = YOLO(str(DETECTION_MODEL))


def RewriteCSV(folder):
    # Extract folder information
    folder_info = folder.split('_')
    if folder_info[2][0:2] == "TL":
        country = folder_info[0]
        ad_severity = folder_info[1]
        tlss = int(folder_info[2].strip("TL"))
        if tlss == 0:
            lesional = False
        else:
            lesional = True
        number = int(folder_info[-1].strip("No."))
        ad_group = ad_severity.strip("G")
    else:
        country = None
        tlss = None
        lesional = None
        number = None
        ad_group = None


    original_png_path = os.path.join(folder_dir, folder, "CNO_Detection", "Image", "Original")
    enhanced_png_path = os.path.join(folder_dir, folder, "CNO_Detection", "Image", "Enhanced")
    kde_png_path = os.path.join(folder_dir, folder, "CNO_Detection", "Image", "KDE")
    save_dir = os.path.join(folder_dir, folder, "CNO_Detection", "Result")

    file_list = [f.stem for f in Path(enhanced_png_path).glob("*.png")]
    print("Images we redo CSV for are: ", file_list)

    print("Performing QC")
    #Redo QC model predictions
    cno_col, avg_area_col, total_area_col, layer_area, layer_cno, layer_density, qc_prediction, qc_conf = cno_detection(
    enhanced_png_path, kde_png_path, conf, cno_model,
    file_list, model)



    timestr = time.strftime("%Y%m%d-%H%M%S")
    # Write CSV
    # open the file in the write mode
    print("Now writing CSV result for ", folder)
    f = open(save_dir + os.sep + '{}_{}.csv'.format(folder, timestr), 'w')
    header = ['File', 'Country', 'Group', 'No.', 'TLSS', 'Lesional', 'CNO', 'QC', 'QC_Conf',

              'Layer_Area_0', 'Layer_Area_1', 'Layer_Area_2', 'Layer_Area_3', 'Layer_Area_4',
              'Layer_Area_5', 'Layer_Area_6', 'Layer_Area_7', 'Layer_Area_8', 'Layer_Area_9',
              'Layer_Area_10', 'Layer_Area_11', 'Layer_Area_12', 'Layer_Area_13', 'Layer_Area_14',
              'Layer_Area_15', 'Layer_Area_16', 'Layer_Area_17', 'Layer_Area_18', 'Layer_Area_19',
              'Layer_Area_20', 'Layer_Area_21', 'Layer_Area_22', 'Layer_Area_23', 'Layer_Area_24',

              'Layer_CNO_0', 'Layer_CNO_1', 'Layer_CNO_2', 'Layer_CNO_3', 'Layer_CNO_4',
              'Layer_CNO_5', 'Layer_CNO_6', 'Layer_CNO_7', 'Layer_CNO_8', 'Layer_CNO_9',
              'Layer_CNO_10', 'Layer_CNO_11', 'Layer_CNO_12', 'Layer_CNO_13', 'Layer_CNO_14',
              'Layer_CNO_15', 'Layer_CNO_16', 'Layer_CNO_17', 'Layer_CNO_18', 'Layer_CNO_19',
              'Layer_CNO_20', 'Layer_CNO_21', 'Layer_CNO_22', 'Layer_CNO_23', 'Layer_CNO_24',

              'Layer_Density_0', 'Layer_Density_1', 'Layer_Density_2', 'Layer_Density_3',
              'Layer_Density_4', 'Layer_Density_5', 'Layer_Density_6', 'Layer_Density_7',
              'Layer_Density_8', 'Layer_Density_9', 'Layer_Density_10', 'Layer_Density_11',
              'Layer_Density_12', 'Layer_Density_13', 'Layer_Density_14', 'Layer_Density_15',
              'Layer_Density_16', 'Layer_Density_17', 'Layer_Density_18', 'Layer_Density_19',
              'Layer_Density_20', 'Layer_Density_21', 'Layer_Density_22', 'Layer_Density_23',
              'Layer_Density_24',

              'AVG_Area', 'AVG_Size']

    writer = csv.writer(f)
    writer.writerow(header)
    for i in range(len(file_list)):
        data = [file_list[i], country, ad_group, number, tlss, lesional, cno_col[i], qc_prediction[i], qc_conf[i],

            layer_area[i][0], layer_area[i][1], layer_area[i][2], layer_area[i][3], layer_area[i][4],
            layer_area[i][5], layer_area[i][6], layer_area[i][7], layer_area[i][8], layer_area[i][9],
            layer_area[i][10], layer_area[i][11], layer_area[i][12], layer_area[i][13],
            layer_area[i][14], layer_area[i][15], layer_area[i][16], layer_area[i][17],
            layer_area[i][18], layer_area[i][19], layer_area[i][20], layer_area[i][21],
            layer_area[i][22], layer_area[i][23], layer_area[i][24],

            layer_cno[i][0], layer_cno[i][1], layer_cno[i][2], layer_cno[i][3], layer_cno[i][4],
            layer_cno[i][5], layer_cno[i][6], layer_cno[i][7], layer_cno[i][8], layer_cno[i][9],
            layer_cno[i][10], layer_cno[i][11], layer_cno[i][12], layer_cno[i][13], layer_cno[i][14],
            layer_cno[i][15], layer_cno[i][16], layer_cno[i][17], layer_cno[i][18], layer_cno[i][19],
            layer_cno[i][20], layer_cno[i][21], layer_cno[i][22], layer_cno[i][23], layer_cno[i][24],

            layer_density[i][0], layer_density[i][1], layer_density[i][2], layer_density[i][3],
            layer_density[i][4], layer_density[i][5], layer_density[i][6], layer_density[i][7],
            layer_density[i][8], layer_density[i][9], layer_density[i][10], layer_density[i][11],
            layer_density[i][12], layer_density[i][13], layer_density[i][14], layer_density[i][15],
            layer_density[i][16], layer_density[i][17], layer_density[i][18], layer_density[i][19],
            layer_density[i][20], layer_density[i][21], layer_density[i][22], layer_density[i][23],
            layer_density[i][24],

            total_area_col[i], avg_area_col[i]]

        writer.writerow(data)
    f.close()



folder_list = []
for folderName in glob.glob(folder_dir + os.sep + '*'):
    if os.path.isdir(folderName):  # now only searches in dir
        folder = folderName.split(os.sep)[-1]
        folder_list.append(folder)
folder_list.sort()
print("Detected Folders", folder_list)

for folder in folder_list:
    resultFolder = folder + "/CNO_Detection/Result"
    csv_files = sorted(glob.glob(os.path.join(folder_dir,resultFolder, "*.csv")))

    if not csv_files:
        print("No CSV files found in folder to append to.")
        print("Running QC code")
        try:
            RewriteCSV(folder)
        except Exception as e:
            print("Could not do QC for this folder ", folder)
            print("Error was ", e)
            print("Will write this to log")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append error info to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Folder: {folder}\n")
                f.write(f"Error: {e}\n")
                f.write("-" * 60 + "\n")
    else:
        csv_path = csv_files[0]
        mod_time = datetime.fromtimestamp(os.path.getmtime(csv_path))
        if mod_time > cutoff_date:
            #if file(csv_path) is newer than August 27, 2025:
            print("Now deleting CSV file at " ,csv_path)
            os.remove(csv_path)
            print("Writing new CSV file based on new QC calculations for ", folder)
            try:
                RewriteCSV(folder)
            except Exception as e:
                print("Could not do QC for this folder ", folder)
                print("Error was ", e)
                print("Will write this to log")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Append error info to log file
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] Folder: {folder}\n")
                    f.write(f"Error: {e}\n")
                    f.write("-" * 60 + "\n")

        else:
            print("CSV file too old to be affected by bug in ", folder)

