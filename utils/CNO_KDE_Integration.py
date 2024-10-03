# Copyright 2024 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)

import time
import sys
import csv
import cv2
import math
import matplotlib.pyplot as plt
from pathlib import Path
from utils.Img_Preprocessing import *
from ultralytics import YOLO
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV

warnings.filterwarnings('ignore')
DIR_NAME = Path(os.path.dirname(__file__)).parent
np.set_printoptions(threshold=sys.maxsize)
# Use GPU
# torch.cuda.set_device(0) # Set to your desired GPU number

# Model Path
DETECTION_MODEL_n = os.path.join(DIR_NAME, 'models', 'YOLOv8n.pt')
DETECTION_MODEL_s = os.path.join(DIR_NAME, 'models', 'YOLOv8s.pt')
DETECTION_MODEL_m = os.path.join(DIR_NAME, 'models', 'YOLOv8m.pt')
DETECTION_MODEL_l = os.path.join(DIR_NAME, 'models', 'YOLOv8l.pt')
DETECTION_MODEL_x = os.path.join(DIR_NAME, 'models', 'YOLOv8x.pt')
# DETECTION_MODEL_c = os.path.join(DIR_NAME, 'models', 'YOLOv9c.pt')
# DETECTION_MODEL_e = os.path.join(DIR_NAME, 'models', 'YOLOv9e.pt')

def numcat(arr):
    arr_size = arr.shape[0]
    arr_cat = np.empty([arr_size, 1], dtype=np.int32)
    for i in range(arr.shape[0]):
        arr_cat[i] = arr[i][0] * 1000 + arr[i][1]
    return arr_cat


def cno_detection(source, kde_dir, conf, cno_model, file_list, model_type):

    # Declare Parameters
    cno_col = []
    total_layer_area = []
    total_layer_cno = []
    total_layer_density = []
    avg_area_col = []
    total_area_col = []

    detection_results = cno_model.predict(source, save=False, save_txt=False, iou=0.5, conf=conf, max_det=1200)

    # CNO Analysis
    for idx, result in enumerate(detection_results):
        CNO = len(result.boxes)
        single_layer_area = []
        single_layer_cno = []
        single_layer_density = []
        total_area = 0
        if CNO < 5:
            avg_area_col.append(np.nan)
            total_area_col.append(np.nan)
            nan_arr = np.empty([25])
            nan_arr[:] = np.nan
            total_layer_area.append(nan_arr)
            total_layer_cno.append(nan_arr)
            total_layer_density.append(nan_arr)
        else:
            CNO_coor = np.empty([CNO, 2], dtype=int)
            for j in range(CNO):
                w = result.boxes.xywh[j][2]
                h = result.boxes.xywh[j][3]
                area = (math.pi * w * h / 4) * 20 * 20 / (512 * 512)
                total_area += area
                bbox_img = result.orig_img
                x = round(result.boxes.xywh[j][0].item())
                y = round(result.boxes.xywh[j][1].item())

                x1 = round(result.boxes.xyxy[j][0].item())
                y1 = round(result.boxes.xyxy[j][1].item())
                x2 = round(result.boxes.xyxy[j][2].item())
                y2 = round(result.boxes.xyxy[j][3].item())

                CNO_coor[j] = [x, y]
                bbox_img = cv2.rectangle(bbox_img,
                                         (x1, y1),
                                         (x2, y2),
                                         (0, 255, 0), 1)

            avg_area = total_area / CNO
            avg_area_col.append(round(avg_area.item(), 4))
            total_area_col.append(round(total_area.item(), 4))

            cv2.imwrite(os.path.join(kde_dir, '{}_{}_{}_bbox.png'.format(file_list[idx], model_type, conf)),
                        bbox_img)

            kde = KernelDensity(metric='euclidean', kernel='gaussian', algorithm='ball_tree')

            # Finding Optimal Bandwidth
            ti = time.time()
            if CNO < 7:
                fold = CNO
            else:
                fold = 7
            gs = GridSearchCV(kde, {'bandwidth': np.linspace(20, 60, 41)}, cv=fold)
            cv = gs.fit(CNO_coor)
            bw = cv.best_params_['bandwidth']
            tf = time.time()
            print("Finding optimal bandwidth={:.2f} ({:n}-fold cross-validation): {:.2f} secs".format(bw, cv.cv,
                                                                                                      (tf - ti)))
            kde.bandwidth = bw
            _ = kde.fit(CNO_coor)

            xgrid = np.arange(0, bbox_img.shape[0], 1)
            ygrid = np.arange(0, bbox_img.shape[1], 1)
            xv, yv = np.meshgrid(xgrid, ygrid)
            xys = np.vstack([xv.ravel(), yv.ravel()]).T
            gdim = xv.shape
            zi = np.arange(xys.shape[0])
            zXY = xys
            z = np.exp(kde.score_samples(zXY))
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
                        ((layer_kde_sum / np.sum(z)) * CNO_coor.shape[0] / layer_area) * 512 * 512 / 400, 4)
                    layer_cno = np.round(layer_kde_sum / np.sum(z) * CNO_coor.shape[0], 2)
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

            # Plot CNO Distribution
            plt.contourf(x, y, z, levels=levels, cmap=plt.cm.bone)
            plt.axis('off')
            plt.gcf().set_size_inches(8, 8)
            plt.gca().invert_yaxis()
            plt.savefig(os.path.join(kde_dir, '{}_{}_{}_KDE.png'.format(file_list[idx], model_type, conf)),
                        bbox_inches='tight', pad_inches=0)
            plt.clf()

            plt.scatter(CNO_coor[:, 0], CNO_coor[:, 1], s=10)
            plt.axis('off')
            plt.gcf().set_size_inches(8, 8)
            plt.gca().invert_yaxis()
            plt.savefig(os.path.join(kde_dir, '{}_{}_{}_Spatial.png'.format(file_list[idx], model_type, conf)),
                        bbox_inches='tight', pad_inches=0)
            plt.clf()
        cno_col.append(CNO)

    return cno_col, avg_area_col, total_area_col, total_layer_area, total_layer_cno, total_layer_density


def cno_detect(folder_dir, model, conf):

    if model == 'YOLOv8-N':
        CNO_model = YOLO(DETECTION_MODEL_n)
    elif model == 'YOLOv8-S':
        CNO_model = YOLO(DETECTION_MODEL_s)
    elif model == 'YOLOv8-M':
        CNO_model = YOLO(DETECTION_MODEL_m)
    elif model == 'YOLOv8-L':
        CNO_model = YOLO(DETECTION_MODEL_l)
    else:
        CNO_model = YOLO(DETECTION_MODEL_x)
    """  
    elif model == 'YOLOv9-C':
        CNO_model = YOLO(DETECTION_MODEL_c)
    else:
        CNO_model = YOLO(DETECTION_MODEL_e)
    """

    # Search folder path
    folder = folder_dir.split(os.sep)[-1]

    print("Analyzing Folder", folder)

    # Extract folder information
    folder_info = folder.split('_')
    if folder_info[2][0:2] == "TL":
        Country = folder_info[0]
        AD_severity = folder_info[1]
        TLSS = int(folder_info[2].strip("TL"))
        if TLSS == 0:
            lesional = False
        else:
            lesional = True
        Number = int(folder_info[-1].strip("No."))
        AD_group = AD_severity.strip("G")
    else:
        Country = None
        TLSS = None
        lesional = None
        Number = None
        AD_group = None

    run_growcut = True
    timestr = time.strftime("%Y%m%d-%H%M%S")

    CNO_list = []
    Area_sum = []
    Area_avg = []

    file_list = []
    growcut_list = []

    growcut_path = os.path.join(folder_dir, "CNO_Detection", "GrowCut")
    original_png_path = os.path.join(folder_dir, "CNO_Detection", "Image", "Original")
    enhanced_png_path = os.path.join(folder_dir, "CNO_Detection", "Image", "Enhanced")
    kde_png_path = os.path.join(folder_dir, "CNO_Detection", "Image", "KDE")
    save_dir = os.path.join(folder_dir, "CNO_Detection", "Result")
    print("Save Path:", save_dir)

    try:
        os.makedirs(growcut_path, exist_ok=True)
        os.makedirs(original_png_path, exist_ok=True)
        os.makedirs(enhanced_png_path, exist_ok=True)
        os.makedirs(kde_png_path, exist_ok=True)
        if not os.listdir(enhanced_png_path):
            print("Directory is empty")
            run_growcut = True
        else:
            print("Directory is not empty")
            run_growcut = False
        os.makedirs(save_dir, exist_ok=True)
    except OSError as error:
        print("Directory can not be created")

    encyc = []
    walk = os.walk(folder_dir)
    for d, sd, files in walk:
        directory = d.split(os.sep)[-1]
        for fn in files:
            if fn[0:2] != "._" and fn[-10:].lower() == '_trace.bcr' and directory == folder:
                encyc.append(d + os.sep + fn)
    encyc.sort()

    # GrowCut Detection
    if run_growcut:
        for i, fn in enumerate(encyc):
            file, gc_CNO = treat_one_image(fn, growcut_path, original_png_path, enhanced_png_path)
            file_list.append(file)
            growcut_list.append(gc_CNO)
            print(i, end=' ')
    else:
        for i, fn in enumerate(encyc):
            file_list.append(os.path.split(fn)[1][0:-10])

    # CNO Detection & AD Classification
    print("Model", model)
    print("Conf", conf)

    # Make Function
    cno_col, avg_area_col, total_area_col, layer_area, layer_cno, layer_density = cno_detection(enhanced_png_path,
                                                                                                kde_png_path,
                                                                                                conf, CNO_model,
                                                                                                file_list, model)
    CNO_list.append(cno_col)
    Area_sum.append(total_area_col)
    Area_avg.append(avg_area_col)

    Layer_area = layer_area
    Layer_cno = layer_cno
    Layer_density = layer_density

    # Write CSV
    # open the file in the write mode
    f = open(save_dir + os.sep + '{}_{}_{}_{}_.csv'.format(folder, timestr, model, conf), 'w')
    header = ['File', 'Country', 'Group', 'No.', 'TLSS', 'Lesional',

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
        data = [file_list[i], Country, AD_group, Number, TLSS, lesional,

                Layer_area[i][0], Layer_area[i][1], Layer_area[i][2], Layer_area[i][3], Layer_area[i][4],
                Layer_area[i][5], Layer_area[i][6], Layer_area[i][7], Layer_area[i][8], Layer_area[i][9],
                Layer_area[i][10], Layer_area[i][11], Layer_area[i][12], Layer_area[i][13],
                Layer_area[i][14], Layer_area[i][15], Layer_area[i][16], Layer_area[i][17],
                Layer_area[i][18], Layer_area[i][19], Layer_area[i][20], Layer_area[i][21],
                Layer_area[i][22], Layer_area[i][23], Layer_area[i][24],

                Layer_cno[i][0], Layer_cno[i][1], Layer_cno[i][2], Layer_cno[i][3], Layer_cno[i][4],
                Layer_cno[i][5], Layer_cno[i][6], Layer_cno[i][7], Layer_cno[i][8], Layer_cno[i][9],
                Layer_cno[i][10], Layer_cno[i][11], Layer_cno[i][12], Layer_cno[i][13], Layer_cno[i][14],
                Layer_cno[i][15], Layer_cno[i][16], Layer_cno[i][17], Layer_cno[i][18], Layer_cno[i][19],
                Layer_cno[i][20], Layer_cno[i][21], Layer_cno[i][22], Layer_cno[i][23], Layer_cno[i][24],

                Layer_density[i][0], Layer_density[i][1], Layer_density[i][2], Layer_density[i][3],
                Layer_density[i][4], Layer_density[i][5], Layer_density[i][6], Layer_density[i][7],
                Layer_density[i][8], Layer_density[i][9], Layer_density[i][10], Layer_density[i][11],
                Layer_density[i][12], Layer_density[i][13], Layer_density[i][14], Layer_density[i][15],
                Layer_density[i][16], Layer_density[i][17], Layer_density[i][18], Layer_density[i][19],
                Layer_density[i][20], Layer_density[i][21], Layer_density[i][22], Layer_density[i][23],
                Layer_density[i][24],

                Area_sum[0][i], Area_avg[0][i]]
        writer.writerow(data)
    f.close()

