# Copyright 2024 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)

import time
import sys
import math
import glob
import cv2
import csv
import matplotlib.pyplot as plt
from pathlib import Path
from utils.Img_Preprocessing import *
from ultralytics import YOLO
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
from config.global_settings import import_config_dict

# Import config files
config_dict = import_config_dict()

# Import source folder path and detection model
DATA_PATH = config_dict['PATH']['source']
MODEL = config_dict['MODEL']['model']
MODEL_PATH = config_dict['MODEL']['folder_path']
CONF = config_dict['MODEL']['conf_threshold']
DIR_NAME = Path(os.path.dirname(__file__))
warnings.filterwarnings('ignore')  # Suppress warnings
np.set_printoptions(threshold=sys.maxsize)  # Print full numpy arrays
# Use GPU
# torch.cuda.set_device(0) # Set to your desired GPU number

# Model path
DETECTION_MODEL = os.path.join(MODEL_PATH, MODEL)


# The numcat function concatenates two integers in each row of the input 2D array
def numcat(arr):
    arr_size = arr.shape[0]
    arr_cat = np.empty([arr_size, 1], dtype=np.int32)
    for i in range(arr.shape[0]):
        arr_cat[i] = arr[i][0] * 1000 + arr[i][1]
    return arr_cat


# Perform CNO (Circular Nano-size Object) detection and density analysis using KDE
def cno_detection(source, kde_dir, conf, cno_model, file_list, model_type):
    # Declare parameters
    cno_col = []
    total_layer_area = []
    total_layer_cno = []
    total_layer_density = []
    avg_area_col = []
    total_area_col = []

    detection_results = cno_model.predict(source, save=False, save_txt=False, iou=0.5, conf=conf, max_det=1200)

    # CNO detection
    for idx, result in enumerate(detection_results):
        cno = len(result.boxes)
        single_layer_area = []
        single_layer_cno = []
        single_layer_density = []
        total_area = 0
        if cno < 5:
            avg_area_col.append(np.nan)
            total_area_col.append(np.nan)
            nan_arr = np.empty([25])
            nan_arr[:] = np.nan
            total_layer_area.append(nan_arr)
            total_layer_cno.append(nan_arr)
            total_layer_density.append(nan_arr)
        else:
            cno_coor = np.empty([cno, 2], dtype=int)
            for j in range(cno):
                w = result.boxes.xywh[j][2]  # Width of bounding box
                h = result.boxes.xywh[j][3]  # Height of bounding box
                area = (math.pi * w * h / 4) * 20 * 20 / (512 * 512)  # Area calculation
                total_area += area
                bbox_img = result.orig_img
                x = round(result.boxes.xywh[j][0].item())
                y = round(result.boxes.xywh[j][1].item())

                x1 = round(result.boxes.xyxy[j][0].item())
                y1 = round(result.boxes.xyxy[j][1].item())
                x2 = round(result.boxes.xyxy[j][2].item())
                y2 = round(result.boxes.xyxy[j][3].item())

                cno_coor[j] = [x, y]
                bbox_img = cv2.rectangle(bbox_img,
                                         (x1, y1),
                                         (x2, y2),
                                         (0, 255, 0), 1)

            avg_area = total_area / cno  # Calculate average area
            avg_area_col.append(round(avg_area.item(), 4))
            total_area_col.append(round(total_area.item(), 4))

            # Save bounding box image
            cv2.imwrite(os.path.join(kde_dir, '{}_{}_{}_bbox.png'.format(file_list[idx], model_type, conf)),
                        bbox_img)

            kde = KernelDensity(metric='euclidean', kernel='gaussian', algorithm='ball_tree')

            # Finding optimal bandwidth
            ti = time.time()
            if cno < 7:
                fold = cno
            else:
                fold = 7
            gs = GridSearchCV(kde, {'bandwidth': np.linspace(20, 60, 41)}, cv=fold)
            cv = gs.fit(cno_coor)
            bw = cv.best_params_['bandwidth']
            tf = time.time()
            print("Finding optimal bandwidth={:.2f} ({:n}-fold cross-validation): {:.2f} secs".format(bw, cv.cv,
                                                                                                      (tf - ti)))
            kde.bandwidth = bw
            _ = kde.fit(cno_coor)

            xgrid = np.arange(0, bbox_img.shape[0], 1)
            ygrid = np.arange(0, bbox_img.shape[1], 1)
            xv, yv = np.meshgrid(xgrid, ygrid)
            xys = np.vstack([xv.ravel(), yv.ravel()]).T
            gdim = xv.shape
            zi = np.arange(xys.shape[0])
            zXY = xys
            z = np.exp(kde.score_samples(zXY))  # KDE score samples
            zg = -9999 + np.zeros(xys.shape[0])
            zg[zi] = z

            xyz = np.hstack((xys[:, :2], zg[:, None]))
            x = xyz[:, 0].reshape(gdim)
            y = xyz[:, 1].reshape(gdim)
            z = xyz[:, 2].reshape(gdim)
            levels = np.linspace(0, z.max(), 26)
            print("levels", levels)

            for j in range(len(levels) - 1):

                # Identify the grid points in this layer
                layer_mask = (z >= levels[j])
                layer_area = np.sum(layer_mask)  # Number of grid points in this layer

                # Sum the KDE values in this layer
                layer_kde_sum = np.sum(z[layer_mask])

                # Calculate the real density in this layer
                if layer_area > 0:
                    density = np.round(
                        ((layer_kde_sum / np.sum(z)) * cno_coor.shape[0] / layer_area) * 512 * 512 / 400, 4)
                    layer_cno = np.round(layer_kde_sum / np.sum(z) * cno_coor.shape[0], 2)
                else:
                    density = 0.0
                    layer_cno = 0.0

                print("Level {}: Area={}, CNO={}, density={}".format(j, layer_area, layer_cno, density))
                single_layer_area.append(layer_area)
                single_layer_cno.append(layer_cno)
                single_layer_density.append(density)

            total_layer_area.append(single_layer_area)
            total_layer_cno.append(single_layer_cno)
            total_layer_density.append(single_layer_density)

            # Plot CNO distribution
            plt.contourf(x, y, z, levels=levels, cmap=plt.cm.bone)
            plt.axis('off')
            plt.gcf().set_size_inches(8, 8)
            plt.gca().invert_yaxis()
            plt.savefig(os.path.join(kde_dir, '{}_{}_{}_KDE.png'.format(file_list[idx], model_type, conf)),
                        bbox_inches='tight', pad_inches=0)
            plt.clf()

            plt.scatter(cno_coor[:, 0], cno_coor[:, 1], s=10)
            plt.axis('off')
            plt.gcf().set_size_inches(8, 8)
            plt.gca().invert_yaxis()
            plt.savefig(os.path.join(kde_dir, '{}_{}_{}_Spatial.png'.format(file_list[idx], model_type, conf)),
                        bbox_inches='tight', pad_inches=0)
            plt.clf()
        cno_col.append(cno)

    return cno_col, avg_area_col, total_area_col, total_layer_area, total_layer_cno, total_layer_density


def main(folder_dir, model, conf):
    cno_model = YOLO(str(DETECTION_MODEL))

    # Search folder path
    folder_list = []
    for folderName in glob.glob(folder_dir + os.sep + '*'):
        folder = folderName.split(os.sep)[-1]
        folder_list.append(folder)
    folder_list.sort()
    print("Detected Folders", folder_list)

    for folder in folder_list:

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

        run_preprocessing = True
        timestr = time.strftime("%Y%m%d-%H%M%S")

        cno_list = []
        area_sum = []
        area_avg = []
        file_list = []
        file_type = "bcr"

        original_png_path = os.path.join(folder_dir, folder, "CNO_Detection", "Image", "Original")
        enhanced_png_path = os.path.join(folder_dir, folder, "CNO_Detection", "Image", "Enhanced")
        kde_png_path = os.path.join(folder_dir, folder, "CNO_Detection", "Image", "KDE")
        save_dir = os.path.join(folder_dir, folder, "CNO_Detection", "Result")
        print("Save Path:", save_dir)

        try:
            os.makedirs(original_png_path, exist_ok=True)
            os.makedirs(enhanced_png_path, exist_ok=True)
            os.makedirs(kde_png_path, exist_ok=True)
            if not os.listdir(enhanced_png_path):
                print("Directory is empty")
                run_preprocessing = True
            else:
                print("Directory is not empty")
                run_preprocessing = False
            os.makedirs(save_dir, exist_ok=True)
        except OSError as error:
            print("Directory can not be created")

        encyc = []
        walk = os.walk(folder_dir)
        for d, sd, files in walk:
            directory = d.split(os.sep)[-1]
            for fn in files:
                if (fn[0:2] != "._" and
                        (fn.lower().endswith('_trace.bcr') or fn.lower().endswith(
                            '_retrace.bcr')) and directory == folder):
                    encyc.append(d + os.sep + fn)
                    file_type = "bcr"
                elif fn[0:2] != "._" and fn[-3:].lower() == 'nid' and directory == folder:
                    encyc.append(d + os.sep + fn)
                    file_type = "nid"
        encyc.sort()
        print("Files: ", encyc)
        print("File type: ", file_type)

        # Image preprocessing
        if run_preprocessing:
            for i, fn in enumerate(encyc):
                file_type = "bcr" if fn.lower().endswith(('.bcr')) else "nid"
                file = treat_one_image(fn, original_png_path, enhanced_png_path, file_type)
                if file_type == 'nid':
                    file_list.extend(file)
                else:
                    file_list.append(file)
                print(i, end=' ')
        else:
            for i, fn in enumerate(encyc):
                file_type = "bcr" if fn.lower().endswith(('.bcr')) else "nid"
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

        print("Model", model)
        print("Conf", conf)

        # CNO detection & KDE calculation
        cno_col, avg_area_col, total_area_col, layer_area, layer_cno, layer_density = cno_detection(enhanced_png_path, kde_png_path, conf, cno_model,
                                                                                                    file_list, model)
        cno_list.append(cno_col)
        area_sum.append(total_area_col)
        area_avg.append(avg_area_col)

        # Write CSV
        # open the file in the write mode
        f = open(save_dir + os.sep + '{}_{}.csv'.format(folder, timestr), 'w')
        header = ['File', 'Country', 'Group', 'No.', 'TLSS', 'Lesional', 'CNO',

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
            data = [file_list[i], country, ad_group, number, tlss, lesional, cno_list[0][i],

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

                    area_sum[0][i], area_avg[0][i]]
            writer.writerow(data)
        f.close()


if __name__ == "__main__":
    main(DATA_PATH, MODEL, CONF)

