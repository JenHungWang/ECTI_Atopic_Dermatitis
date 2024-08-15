import os
import cv2
import pandas as pd
import PIL.Image as Image
import gradio as gr
import numpy as np
import math
from pathlib import Path
from ultralytics import ASSETS, YOLO

DIR_NAME = Path(os.path.dirname(__file__))
DETECTION_MODEL_n = os.path.join(DIR_NAME, 'models', 'YOLOv8-N_CNO_Detection.pt')
DETECTION_MODEL_s = os.path.join(DIR_NAME, 'models', 'YOLOv8-S_CNO_Detection.pt')
DETECTION_MODEL_m = os.path.join(DIR_NAME, 'models', 'YOLOv8-M_CNO_Detection.pt')
DETECTION_MODEL_l = os.path.join(DIR_NAME, 'models', 'YOLOv8-L_CNO_Detection.pt')
DETECTION_MODEL_x = os.path.join(DIR_NAME, 'models', 'YOLOv8-X_CNO_Detection.pt')

# MODEL = os.path.join(DIR_NAME, 'models', 'YOLOv8-M_CNO_Detection.pt')
# model = YOLO(MODEL)
# cno_df = pd.DataFrame()

def predict_image(name, model, img, conf_threshold, iou_threshold):
    """Predicts and plots labeled objects in an image using YOLOv8 model with adjustable confidence and IOU thresholds."""
    gr.Info("Starting process")
    # gr.Warning("Name is empty")
    if name == "":
        gr.Warning("Name is empty")

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

    results = CNO_model.predict(
        source=img,
        conf=conf_threshold,
        iou=iou_threshold,
        show_labels=False,
        show_conf=False,
        imgsz=512,
        max_det=1200
    )

    cno_count = []
    cno_image = []
    file_name = []

    # print("deb", img)

    for idx, result in enumerate(results):
        cno = len(result.boxes)
        cno_coor = np.empty([cno, 2], dtype=int)
        file_label = img[idx].split(os.sep)[-1]
        for j in range(cno):
            # w = r.boxes.xywh[j][2]
            # h = r.boxes.xywh[j][3]
            # area = (math.pi * w * h / 4) * 20 * 20 / (512 * 512)
            # total_area += area
            # bbox_img = r.orig_img
            x = round(result.boxes.xywh[j][0].item())
            y = round(result.boxes.xywh[j][1].item())

            x1 = round(result.boxes.xyxy[j][0].item())
            y1 = round(result.boxes.xyxy[j][1].item())
            x2 = round(result.boxes.xyxy[j][2].item())
            y2 = round(result.boxes.xyxy[j][3].item())

            cno_coor[j] = [x, y]
            cv2.rectangle(result.orig_img, (x1, y1), (x2, y2), (0, 255, 0), 1)
        im_array = result.orig_img
        cno_image.append([Image.fromarray(im_array[..., ::-1]), file_label])
        cno_count.append(cno)
        file_name.append(file_label)

    """
    for r in results:
        CNO = len(r.boxes)
        CNO_coor = np.empty([CNO, 2], dtype=int)
        for j in range(CNO):
            # w = r.boxes.xywh[j][2]
            # h = r.boxes.xywh[j][3]
            # area = (math.pi * w * h / 4) * 20 * 20 / (512 * 512)
            # total_area += area
            # bbox_img = r.orig_img
            x = round(r.boxes.xywh[j][0].item())
            y = round(r.boxes.xywh[j][1].item())

            x1 = round(r.boxes.xyxy[j][0].item())
            y1 = round(r.boxes.xyxy[j][1].item())
            x2 = round(r.boxes.xyxy[j][2].item())
            y2 = round(r.boxes.xyxy[j][3].item())

            CNO_coor[j] = [x, y]
            cv2.rectangle(r.orig_img, (x1, y1), (x2, y2), (0, 255, 0), 1)
        im_array = r.orig_img
        im = Image.fromarray(im_array[..., ::-1])

    CNO_count = "CNO Count: " + str(CNO)
    
    test = []
    for i in range(len(cno_image)):
        test.append([cno_image[0], f"label {i}"])
    """
    data = {
        "Files": file_name,
        "CNO Count": cno_count,
    }

    # load data into a DataFrame object:
    cno_df = pd.DataFrame(data)

    return cno_df, cno_image

def highlight_max(s, props=''):
    return np.where(s == np.nanmax(s.values), props, '')

def highlight_df(df, data: gr.SelectData):

    styler = df.style.apply(lambda x: ['background: lightgreen'
                               if x.Files == data.value["caption"]
                               else None for i in x], axis=1)

    # print("selected", data.value["caption"])
    return data.value["caption"], styler

def reset():
    name_textbox = ""
    gender_radio = None
    age_slider = 0
    fitzpatrick = 1
    history = []
    model_radio = "YOLOv8-M"
    input_files = []
    conf_slider = 0.2
    iou_slider = 0.5
    analysis_results = []
    cno_gallery = []
    test_label = ""

    return name_textbox, gender_radio, age_slider, fitzpatrick, history, model_radio, input_files, conf_slider, iou_slider, analysis_results, cno_gallery, test_label


with gr.Blocks(title="AFM AI Analysis", theme="default") as app:
    with gr.Row():
        with gr.Column():
            # gr.Markdown("User Information")
            with gr.Accordion("User Information", open=True):
                name_textbox = gr.Textbox(label="Name")
                with gr.Row():
                    gender_radio = gr.Radio(["Male", "Female"], label="Gender", interactive=True, scale=1)
                    age_slider = gr.Slider(minimum=0, maximum=100, step=1, value=0, label="Age", interactive=True, scale=2)
                with gr.Group():
                    fitzpatrick = gr.Slider(minimum=1, maximum=6, step=1, value=1, label="Fitzpatrick", interactive=True)
                history = gr.Checkboxgroup(["Familial Disease", "Allergic Rhinitis", "Asthma"], label="Medical History", interactive=True)

            input_files = gr.File(file_types=["image"], file_count="multiple", label="Upload Image")
            # gr.Markdown("Model Configuration")
            with gr.Accordion("Model Configuration", open=False):
                model_radio = gr.Radio(["YOLOv8-N", "YOLOv8-S", "YOLOv8-M", "YOLOv8-L", "YOLOv8-X"], label="Model Selection", value="YOLOv8-M")
                conf_slider = gr.Slider(minimum=0, maximum=1, value=0.2, label="Confidence threshold")
                iou_slider = gr.Slider(minimum=0, maximum=1, value=0.5, label="IoU threshold")
            with gr.Row():
                analyze_btn = gr.Button("Analyze")
                clear_btn = gr.Button("Reset")
        with gr.Column():
            analysis_results = gr.Dataframe(headers=["Files", "CNO Count"], interactive=False)
            # cno_label = gr.Label(label="Analysis Results")
            cno_gallery = gr.Gallery(label="Result", show_label=True, columns=3, object_fit="contain")
            test_label = gr.Label(label="Analysis Results")
            # cno_img = gr.Image(type="pil", label="Result")

    analyze_btn.click(
        fn=predict_image,
        inputs=[name_textbox, model_radio, input_files, conf_slider, iou_slider],
        outputs=[analysis_results, cno_gallery]
    )

    clear_btn.click(reset, outputs=[name_textbox, gender_radio, age_slider, fitzpatrick, history, model_radio,
                                    input_files, conf_slider, iou_slider, analysis_results, cno_gallery, test_label])

    cno_gallery.select(highlight_df, inputs=analysis_results, outputs=[test_label, analysis_results])


"""
iface = gr.Interface(
    fn=predict_image,
    inputs=[
        gr.Textbox(label="User Name"),
        gr.Radio(["YOLOv8-N", "YOLOv8-S", "YOLOv8-M", "YOLOv8-L", "YOLOv8-X"], value="YOLOv8-M"),
        # gr.Image(type="filepath", label="Upload Image"),
        gr.File(file_types=["image"], file_count="multiple", label="Upload Image"),
        gr.Slider(minimum=0, maximum=1, value=0.2, label="Confidence threshold"),
        gr.Slider(minimum=0, maximum=1, value=0.5, label="IoU threshold")
    ],
    outputs=[gr.Label(label="Analysis Results"), gr.Image(type="pil", label="Result")],
    title="AFM AI Analysis",
    description="Upload images for inference. The YOLOv8-M model is used by default.",
    theme=gr.themes.Default()
)
"""

if __name__ == '__main__':
    # iface.launch()
    app.launch()
