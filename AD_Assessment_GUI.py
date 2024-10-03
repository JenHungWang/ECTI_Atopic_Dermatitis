# Copyright 2024 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)

import tkinter
import tkinter.messagebox
import customtkinter
import pandas
import threading
import glob
from customtkinter import filedialog
from utils.CNO_KDE_Integration import *

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"
IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("AFM Skin Diagnosis.py")
        self.geometry(f"{1440}x{755}")

        # configure grid layout (4x4)
        self.grid_columnconfigure((1, 2), weight=1)
        # self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1), weight=0)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, padx=(0, 20), rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Topography Files",
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.data_path_field = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Directory")
        self.data_path_field.grid(row=1, column=0, padx=20, pady=10)
        self.path_btn = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event, text="Import")
        self.path_btn.grid(row=2, column=0, padx=20, pady=10)
        self.start_btn = customtkinter.CTkButton(self.sidebar_frame, command=self.analyze_event, text="Analyze")
        self.start_btn.grid(row=3, column=0, padx=20, pady=10)
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create textbox
        self.information_frame = customtkinter.CTkFrame(self, width=460)
        self.information_frame.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.information_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        self.information_frame_title = customtkinter.CTkLabel(self.information_frame, text="Personal Information",
                                                              fg_color=("gray80", "gray30"),
                                                              font=customtkinter.CTkFont(size=16, weight="bold"),
                                                              corner_radius=6)
        self.information_frame_title.grid(row=0, column=0, padx=20, pady=10, sticky="ew", columnspan=7)

        # Name field
        self.name_var = tkinter.StringVar()
        self.name_label = customtkinter.CTkLabel(master=self.information_frame, text="Name")
        self.name_label.grid(row=1, column=0, padx=20, pady=(25, 15), sticky="new")
        self.name_field = customtkinter.CTkEntry(self.information_frame, placeholder_text="Name")
        self.name_field.grid(row=1, column=1, padx=(10, 100), pady=(25, 15), sticky="we", columnspan=3)

        # Gender field
        self.gender_var = tkinter.IntVar(value=0)
        self.gender_label = customtkinter.CTkLabel(master=self.information_frame, text="Gender")
        self.gender_label.grid(row=2, column=0, padx=20, pady=15, sticky="new")
        self.gender_rbtn_m = customtkinter.CTkRadioButton(master=self.information_frame, variable=self.gender_var,
                                                          value=0, text="Male")
        self.gender_rbtn_m.grid(row=2, column=1, pady=15, padx=10, sticky="w")
        self.gender_rbtn_f = customtkinter.CTkRadioButton(master=self.information_frame, variable=self.gender_var,
                                                          value=1, text="Female")
        self.gender_rbtn_f.grid(row=2, column=2, pady=15, padx=10, sticky="w")

        # Age field
        self.age_var = tkinter.IntVar(value=0)
        self.age_label = customtkinter.CTkLabel(master=self.information_frame, text="Age")
        self.age_label.grid(row=3, column=0, padx=20, pady=15, sticky="new")
        self.age_slider = customtkinter.CTkSlider(self.information_frame, from_=0, to=100, command=self.age_sliding)
        self.age_slider.set(50)
        self.age_slider.grid(row=3, column=1, pady=15, padx=10, sticky="ew", columnspan=2)
        self.age_val_label = customtkinter.CTkLabel(master=self.information_frame, text=str(int(self.age_slider.get())))
        self.age_val_label.grid(row=3, column=3, pady=15, padx=(0,10), sticky="w")

        # Fitzpatrick
        self.pigmentation_var = tkinter.IntVar(value=0)
        self.pigmentation_label = customtkinter.CTkLabel(master=self.information_frame, text="Fitzpatrick")
        self.pigmentation_label.grid(row=4, column=0, padx=20, pady=15, sticky="new")
        self.pigmentation_slider = customtkinter.CTkSlider(self.information_frame, from_=1, to=6, number_of_steps=5,
                                                           command=self.pigmentation_sliding)
        self.pigmentation_slider.set(1)
        self.pigmentation_slider.grid(row=4, column=1, pady=15, padx=10, sticky="ew", columnspan=2)
        self.pigmentation_val_label = customtkinter.CTkLabel(master=self.information_frame, text=str(int(self.pigmentation_slider.get())))
        self.pigmentation_val_label.grid(row=4, column=3, pady=15, padx=(0, 10), sticky="w")

        # Familial disease checkboxes
        self.history_label = customtkinter.CTkLabel(master=self.information_frame, text="Medical History")
        self.history_label.grid(row=5, column=0, padx=10, pady=(15, 0), sticky="new")
        self.history_checkbox_1 = customtkinter.CTkCheckBox(master=self.information_frame, text="Familial Disease")
        self.history_checkbox_1.grid(row=5, column=1, pady=(15, 0), padx=(10, 20), sticky="w")
        self.history_checkbox_2 = customtkinter.CTkCheckBox(master=self.information_frame, text="Allergic Rhinitis")
        self.history_checkbox_2.grid(row=5, column=2, pady=(15, 0), padx=(10, 20), sticky="w")
        self.history_checkbox_3 = customtkinter.CTkCheckBox(master=self.information_frame, text="Asthma")
        self.history_checkbox_3.grid(row=5, column=3, pady=(15, 0), padx=(10, 20), sticky="w")

        # create tabview
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=2, padx=(20, 30), pady=(0, 20), sticky="nsew", rowspan=2)
        self.tabview.add("AFM")
        self.tabview.add("CNO")
        self.tabview.add("KDE")
        self.tabview.tab("AFM").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("AFM").grid_rowconfigure((0, 1, 2), weight=1)  # configure grid of individual tabs
        self.tabview.tab("CNO").grid_columnconfigure(0, weight=1)
        self.tabview.tab("CNO").grid_rowconfigure((0, 1, 2), weight=1)  # configure grid of individual tabs
        self.tabview.tab("KDE").grid_columnconfigure(0, weight=1)
        self.tabview.tab("KDE").grid_rowconfigure((0, 1, 2), weight=1)  # configure grid of individual tabs

        # tabview - AFM original images
        self.model_frame_afm = customtkinter.CTkFrame(self.tabview.tab("AFM"))
        self.model_frame_afm.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="new")
        self.model_frame_afm.grid_columnconfigure((0, 1, 2, 3), weight=1)  # configure grid of individual tabs

        model_var = customtkinter.StringVar(value="YOLOv10-L")  # set initial value
        conf_var = customtkinter.StringVar(value="0.2")  # set initial value
        self.model = "YOLOv10-L"
        self.conf = 0.2

        self.model_label = customtkinter.CTkLabel(master=self.model_frame_afm, text="Model:")
        self.model_label.grid(row=0, column=0, padx=0, pady=0, sticky="new")
        self.model_optionmenu = customtkinter.CTkOptionMenu(self.model_frame_afm, button_color="orange3",
                                                            fg_color="orange", button_hover_color="DarkOrange3",
                                                            values=["YOLOv10-N", "YOLOv10-S", "YOLOv10-M", "YOLOv10-B",
                                                                    "YOLOv10-L", "YOLOv10-X"],
                                                            variable=model_var, command=self.model_optionmenu_callback)
        self.model_optionmenu.grid(row=0, column=1, padx=0, pady=0, sticky="nw")

        self.conf_label = customtkinter.CTkLabel(master=self.model_frame_afm, text="Conf:")
        self.conf_label.grid(row=0, column=2, padx=0, pady=0, sticky="new")
        self.conf_optionmenu = customtkinter.CTkOptionMenu(self.model_frame_afm, button_color="orange3",
                                                           fg_color="orange", button_hover_color="DarkOrange3",
                                                           values=["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7",
                                                                   "0.8", "0.9"],
                                                           variable=conf_var, command=self.conf_optionmenu_callback)
        self.conf_optionmenu.grid(row=0, column=3, padx=0, pady=0, sticky="nw")

        self.afm_img_result = customtkinter.CTkLabel(master=self.tabview.tab("AFM"), width=IMAGE_WIDTH,
                                                     height=IMAGE_HEIGHT, text="Please select folder directory",
                                                     font=customtkinter.CTkFont(size=16, weight="bold"))
        self.afm_img_result.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.button_frame_afm = customtkinter.CTkFrame(self.tabview.tab("AFM"))
        self.button_frame_afm.grid(row=2, column=0, padx=80, pady=(0, 20), sticky="new")
        self.button_frame_afm.grid_columnconfigure((0, 1), weight=1)  # configure grid of individual tabs
        self.result_label = customtkinter.CTkLabel(self.button_frame_afm,
                                                   text=" ",
                                                   font=customtkinter.CTkFont(size=16, weight="bold"))
        self.result_label.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)

        self.analyze_btn = customtkinter.CTkButton(self.button_frame_afm, command=self.analyze_event, text="Analyze")
        self.analyze_btn.grid(row=2, column=0, padx=20, sticky="new")
        self.stop_btn = customtkinter.CTkButton(self.button_frame_afm, command=self.stop_event, text="Stop")
        self.stop_btn.grid(row=2, column=1, padx=20, sticky="new")

        # tabview - CNO detection images
        self.model_frame_cno = customtkinter.CTkFrame(self.tabview.tab("CNO"))
        self.model_frame_cno.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="new")
        self.model_frame_cno.grid_columnconfigure((0, 1, 2, 3), weight=1)  # configure grid of individual tabs

        self.model_label = customtkinter.CTkLabel(master=self.model_frame_cno, text="Model:")
        self.model_label.grid(row=0, column=0, padx=0, pady=0, sticky="new")
        self.model_optionmenu = customtkinter.CTkOptionMenu(self.model_frame_cno, button_color="orange3",
                                                            fg_color="orange", button_hover_color="DarkOrange3",
                                                            values=["YOLOv10-N", "YOLOv10-S", "YOLOv10-M", "YOLOv10-B",
                                                                    "YOLOv10-L", "YOLOv10-X"],
                                                            variable=model_var, command=self.model_optionmenu_callback)
        self.model_optionmenu.grid(row=0, column=1, padx=0, pady=0, sticky="nw")

        self.conf_label = customtkinter.CTkLabel(master=self.model_frame_cno, text="Conf:")
        self.conf_label.grid(row=0, column=2, padx=0, pady=0, sticky="new")
        self.conf_optionmenu = customtkinter.CTkOptionMenu(self.model_frame_cno, button_color="orange3",
                                                           fg_color="orange", button_hover_color="DarkOrange3",
                                                           values=["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7",
                                                                   "0.8", "0.9"],
                                                           variable=conf_var, command=self.conf_optionmenu_callback)
        self.conf_optionmenu.grid(row=0, column=3, padx=0, pady=0, sticky="nw")

        self.cno_img_result = customtkinter.CTkLabel(master=self.tabview.tab("CNO"), width=IMAGE_WIDTH,
                                                     height=IMAGE_HEIGHT, text="Please select folder directory",
                                                     font=customtkinter.CTkFont(size=16, weight="bold"))
        self.cno_img_result.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.button_frame_cno = customtkinter.CTkFrame(self.tabview.tab("CNO"))
        self.button_frame_cno.grid(row=2, column=0, padx=80, pady=(0, 20), sticky="new")
        self.button_frame_cno.grid_columnconfigure((0, 1), weight=1)  # configure grid of individual tabs

        self.result_label = customtkinter.CTkLabel(self.button_frame_cno,
                                                   text=" ",
                                                   font=customtkinter.CTkFont(size=16, weight="bold"))
        self.result_label.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)

        self.analyze_btn = customtkinter.CTkButton(self.button_frame_cno, command=self.analyze_event, text="Analyze")
        self.analyze_btn.grid(row=2, column=0, padx=20, sticky="new")
        self.stop_btn = customtkinter.CTkButton(self.button_frame_cno, command=self.stop_event, text="Stop")
        self.stop_btn.grid(row=2, column=1, padx=20, sticky="new")

        # tabview - KDE analysis results
        self.model_frame_kde = customtkinter.CTkFrame(self.tabview.tab("KDE"))
        self.model_frame_kde.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="new")
        self.model_frame_kde.grid_columnconfigure((0, 1, 2, 3), weight=1)  # configure grid of individual tabs

        self.model_label = customtkinter.CTkLabel(master=self.model_frame_kde, text="Model:")
        self.model_label.grid(row=0, column=0, padx=0, pady=0, sticky="new")
        self.model_optionmenu = customtkinter.CTkOptionMenu(self.model_frame_kde, button_color="orange3",
                                                            fg_color="orange", button_hover_color="DarkOrange3",
                                                            values=["YOLOv10-N", "YOLOv10-S", "YOLOv10-M", "YOLOv10-B",
                                                                    "YOLOv10-L", "YOLOv10-X"],
                                                            variable=model_var, command=self.model_optionmenu_callback)
        self.model_optionmenu.grid(row=0, column=1, padx=0, pady=0, sticky="nw")

        self.conf_label = customtkinter.CTkLabel(master=self.model_frame_kde, text="Conf:")
        self.conf_label.grid(row=0, column=2, padx=0, pady=0, sticky="new")
        self.conf_optionmenu = customtkinter.CTkOptionMenu(self.model_frame_kde, button_color="orange3",
                                                           fg_color="orange", button_hover_color="DarkOrange3",
                                                           values=["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7",
                                                                   "0.8", "0.9"],
                                                           variable=conf_var, command=self.conf_optionmenu_callback)
        self.conf_optionmenu.grid(row=0, column=3, padx=0, pady=0, sticky="nw")

        self.kde_img_result = customtkinter.CTkLabel(master=self.tabview.tab("KDE"), width=IMAGE_WIDTH,
                                                     height=IMAGE_HEIGHT, text="Please select folder directory",
                                                     font=customtkinter.CTkFont(size=16, weight="bold"))
        self.kde_img_result.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.button_frame_kde = customtkinter.CTkFrame(self.tabview.tab("KDE"))
        self.button_frame_kde.grid(row=2, column=0, padx=80, pady=(0, 20), sticky="new")
        self.button_frame_kde.grid_columnconfigure((0, 1), weight=1)  # configure grid of individual tabs

        self.result_label = customtkinter.CTkLabel(self.button_frame_kde,
                                                   text=" ",
                                                   font=customtkinter.CTkFont(size=16, weight="bold"))
        self.result_label.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)

        self.analyze_btn = customtkinter.CTkButton(self.button_frame_kde, command=self.analyze_event, text="Analyze")
        self.analyze_btn.grid(row=2, column=0, padx=20, sticky="new")
        self.stop_btn = customtkinter.CTkButton(self.button_frame_kde, command=self.stop_event, text="Stop")
        self.stop_btn.grid(row=2, column=1, padx=20, sticky="new")

        # TLSS Frame
        self.tlss_frame = customtkinter.CTkFrame(self, width=460)
        self.tlss_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        self.tlss_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        self.tlss_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        self.tlss_frame_title = customtkinter.CTkLabel(self.tlss_frame, text="TLSS",
                                                       fg_color=("gray80", "gray30"),
                                                       font=customtkinter.CTkFont(size=16, weight="bold"),
                                                       corner_radius=6)
        self.tlss_frame_title.grid(row=0, column=0, padx=20, pady=10, sticky="ew", columnspan=7)

        # Lichenification slider
        self.lichenification_var = tkinter.IntVar(value=0)
        self.lichenification_label = customtkinter.CTkLabel(master=self.tlss_frame, text="Lichenification")
        self.lichenification_label.grid(row=1, column=0, padx=20, pady=10, sticky="new")
        self.lichenification_slider = customtkinter.CTkSlider(self.tlss_frame, from_=0, to=3, number_of_steps=3,
                                                              command=self.lichenification_sliding)
        self.lichenification_slider.set(0)
        self.lichenification_slider.grid(row=1, column=1, pady=10, padx=10, sticky="ew", columnspan=2)
        self.lichenification_val_label = customtkinter.CTkLabel(master=self.tlss_frame, text=str(int(self.lichenification_slider.get())))
        self.lichenification_val_label.grid(row=1, column=3, pady=10, padx=(0, 10), sticky="w")

        # Erythema slider
        self.erythema_var = tkinter.IntVar(value=0)
        self.erythema_label = customtkinter.CTkLabel(master=self.tlss_frame, text="Erythema")
        self.erythema_label.grid(row=2, column=0, padx=20, pady=10, sticky="new")
        self.erythema_slider = customtkinter.CTkSlider(self.tlss_frame, from_=0, to=3, number_of_steps=3,
                                                       command=self.erythema_sliding)
        self.erythema_slider.set(0)
        self.erythema_slider.grid(row=2, column=1, pady=10, padx=10, sticky="ew", columnspan=2)
        self.erythema_val_label = customtkinter.CTkLabel(master=self.tlss_frame,
                                                         text=str(int(self.erythema_slider.get())))
        self.erythema_val_label.grid(row=2, column=3, pady=10, padx=(0, 10), sticky="w")

        # Induration/Papulation/Edema slider
        self.induration_var = tkinter.IntVar(value=0)
        self.induration_label = customtkinter.CTkLabel(master=self.tlss_frame, text="Induration/Papulation/Edema")
        self.induration_label.grid(row=3, column=0, padx=20, pady=10, sticky="new")
        self.induration_slider = customtkinter.CTkSlider(self.tlss_frame, from_=0, to=3, number_of_steps=3,
                                                         command=self.induration_sliding)
        self.induration_slider.set(0)
        self.induration_slider.grid(row=3, column=1, pady=10, padx=10, sticky="ew", columnspan=2)
        self.induration_val_label = customtkinter.CTkLabel(master=self.tlss_frame,
                                                           text=str(int(self.induration_slider.get())))
        self.induration_val_label.grid(row=3, column=3, pady=10, padx=(0, 10), sticky="w")

        # Oozing/Crusting slider
        self.oozing_var = tkinter.IntVar(value=0)
        self.oozing_label = customtkinter.CTkLabel(master=self.tlss_frame, text="Oozing/Crusting")
        self.oozing_label.grid(row=4, column=0, padx=20, pady=10, sticky="new")
        self.oozing_slider = customtkinter.CTkSlider(self.tlss_frame, from_=0, to=3, number_of_steps=3,
                                                     command=self.oozing_sliding)
        self.oozing_slider.set(0)
        self.oozing_slider.grid(row=4, column=1, pady=10, padx=10, sticky="ew", columnspan=2)
        self.oozing_val_label = customtkinter.CTkLabel(master=self.tlss_frame,
                                                         text=str(int(self.oozing_slider.get())))
        self.oozing_val_label.grid(row=4, column=3, pady=10, padx=(0, 10), sticky="w")

        # Scaling slider
        self.scaling_var = tkinter.IntVar(value=0)
        self.scaling_label = customtkinter.CTkLabel(master=self.tlss_frame, text="Scaling")
        self.scaling_label.grid(row=5, column=0, padx=20, pady=(10,20), sticky="new")
        self.scaling_slider = customtkinter.CTkSlider(self.tlss_frame, from_=0, to=3, number_of_steps=3,
                                                      command=self.scaling_sliding)
        self.scaling_slider.set(0)
        self.scaling_slider.grid(row=5, column=1, pady=(10,20), padx=10, sticky="ew", columnspan=2)
        self.scaling_val_label = customtkinter.CTkLabel(master=self.tlss_frame,
                                                        text=str(int(self.scaling_slider.get())))
        self.scaling_val_label.grid(row=5, column=3, pady=(10,20), padx=(0, 10), sticky="w")

        # Initialize
        self.appearance_mode_optionemenu.set("System")
        self.scaling_optionemenu.set("100%")

    def model_optionmenu_callback(self, choice: str):
        print("Model selected:", choice)
        self.model = choice

    def conf_optionmenu_callback(self, choice: str):
        print("Conf selected:", choice)
        self.conf = float(choice)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        folder_path = os.path.normpath(filedialog.askdirectory(initialdir=Path(os.path.dirname(__file__))))
        if len(folder_path) != 0:
            self.data_path_field.delete(0, 300)
            self.data_path_field.insert(0, folder_path)
        print(folder_path)

    def age_sliding(self, value:int):
        self.age_val_label.configure(text=int(value))

    def pigmentation_sliding(self, value:int):
        self.pigmentation_val_label.configure(text=int(value))

    def lichenification_sliding(self, value:int):
        self.lichenification_val_label.configure(text=int(value))

    def erythema_sliding(self, value:int):
        self.erythema_val_label.configure(text=int(value))

    def induration_sliding(self, value:int):
        self.induration_val_label.configure(text=int(value))

    def oozing_sliding(self, value:int):
        self.oozing_val_label.configure(text=int(value))

    def scaling_sliding(self, value:int):
        self.scaling_val_label.configure(text=int(value))

    def analyze_event(self):

        # Retrieve User Input
        self.folder_dir = self.data_path_field.get()
        print("Folder Directory: ", self.folder_dir)

        if len(self.folder_dir) == 0:
            self.afm_img_result.configure(text="Please select folder directory", text_color="red", image="",
                                          width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            self.cno_img_result.configure(text="Please select folder directory", text_color="red", image="",
                                          width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            self.kde_img_result.configure(text="Please select folder directory", text_color="red", image="",
                                          width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            return

        elif not os.path.exists(self.folder_dir):
            self.afm_img_result.configure(text="Folder directory is empty", text_color="red", image="",
                                          width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            self.cno_img_result.configure(text="Folder directory is empty", text_color="red", image="",
                                          width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            self.kde_img_result.configure(text="Folder directory is empty", text_color="red", image="",
                                          width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            return

        else:
            # Checking if the list is empty or not
            if len(os.listdir(self.folder_dir)) == 0:
                print("Empty directory")
            else:
                print("Not empty directory")

        self.name = self.name_field.get()
        print("User Name: ", self.name)

        if self.gender_var.get() == 0:
            self.gender = 'M'
        else:
            self.gender = 'F'
        print("Gender: ", self.gender)

        self.age = self.age_val_label.cget("text")
        print("Age: ", self.age)

        self.pigmentation = self.pigmentation_val_label.cget("text")
        print("Pigmentation: ", self.pigmentation)

        self.familial_disease = self.history_checkbox_1.get()
        print("Familial Disease: ", self.familial_disease)

        self.allergic_rhinitis = self.history_checkbox_2.get()
        print("Allergic Rhinitis: ", self.allergic_rhinitis)

        self.asthma = self.history_checkbox_3.get()
        print("Asthma: ", self.asthma)

        self.lichenification = self.lichenification_val_label.cget("text")
        print("TLSS - Lichenification: ", self.lichenification)

        self.erythema = self.erythema_val_label.cget("text")
        print("TLSS - Erythema: ", self.erythema)

        self.induration = self.induration_val_label.cget("text")
        print("TLSS - Induration: ", self.induration)

        self.oozing = self.oozing_val_label.cget("text")
        print("TLSS - Oozing: ", self.oozing)

        self.scaling = self.scaling_val_label.cget("text")
        print("TLSS - Scaling: ", self.scaling)

        # self.model = self.model_optionmenu.cget("variable")
        print("Detection Model: ", self.model)

        # self.conf = float(self.conf_optionmenu.get())
        print("Confidence Threshold: ", self.conf)

        self.analyze_btn.grid_forget()
        self.stop_btn.grid_forget()

        self.afm_path = os.path.join(self.folder_dir, "CNO_Detection", "Image", "Enhanced")
        self.cno_path = os.path.join(self.folder_dir, "CNO_Detection", "Image", "KDE")
        self.csv_path = os.path.join(self.folder_dir, "CNO_Detection", "Result")

        self.run_analyze = True

        if os.path.exists(self.csv_path):
            self.csv_files = os.listdir(self.csv_path)

            for i in range(len(self.csv_files)):
                # print("files", self.csv_files)
                csv_info = self.csv_files[i].split('_')
                # print("csv info", csv_info)

                if self.model in csv_info and str(self.conf) in csv_info:
                    self.run_analyze = False
                    print("Read csv", os.path.join(self.csv_path, self.csv_files[i]))
                    self.df = pandas.read_csv(os.path.join(self.csv_path, self.csv_files[i]))

        print("Analyzing", self.run_analyze)

        if self.run_analyze:
            self.afm_img_result.configure(text="Analyzing...Please wait.",
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            self.cno_img_result.configure(text="Analyzing...Please wait.",
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            self.kde_img_result.configure(text="Analyzing...Please wait.",
                                          font=customtkinter.CTkFont(size=16, weight="bold"))
            print("Analyzing...")

            t1 = threading.Thread(target=cno_detect(self.folder_dir, self.model, self.conf))

            list_of_files = glob.glob(os.path.join(self.csv_path, '*.csv'))
            latest_file = max(list_of_files, key=os.path.getmtime)
            print("Read csv", latest_file)
            self.df = pandas.read_csv(latest_file)

        self.button_frame_afm.grid_forget()
        self.button_frame_cno.grid_forget()
        self.button_frame_kde.grid_forget()

        self.button_frame_afm = customtkinter.CTkFrame(self.tabview.tab("AFM"))
        self.button_frame_afm.grid(row=2, column=0, padx=80, pady=(0, 20), sticky="new")
        self.button_frame_afm.grid_columnconfigure((0, 1, 2), weight=1)

        self.button_frame_cno = customtkinter.CTkFrame(self.tabview.tab("CNO"))
        self.button_frame_cno.grid(row=2, column=0, padx=80, pady=(0, 20), sticky="new")
        self.button_frame_cno.grid_columnconfigure((0, 1, 2), weight=1)

        self.button_frame_kde = customtkinter.CTkFrame(self.tabview.tab("KDE"))
        self.button_frame_kde.grid(row=2, column=0, padx=80, pady=(0, 20), sticky="new")
        self.button_frame_kde.grid_columnconfigure((0, 1, 2), weight=1)

        self.afm_files = [f for f in os.listdir(self.afm_path) if os.path.isfile(os.path.join(self.afm_path, f))]
        self.cno_files = [f for f in os.listdir(self.cno_path) if
                          os.path.isfile(os.path.join(self.cno_path, f)) and f.endswith("{}_{}_bbox.png".format(self.model, self.conf))]
        self.kde_files = [f for f in os.listdir(self.cno_path) if
                          os.path.isfile(os.path.join(self.cno_path, f)) and f.endswith("{}_{}_KDE.png".format(self.model, self.conf))]
        self.image_num = len(self.afm_files)
        self.image_view = 0

        # AFM Results
        self.result_label_afm = customtkinter.CTkLabel(self.button_frame_afm,
                                                       text=" ", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.result_label_afm.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)
        self.previous_btn_afm = customtkinter.CTkButton(self.button_frame_afm, command=self.previous_event,
                                                        text="Previous")
        self.previous_btn_afm.grid(row=2, column=0, padx=10, sticky="new")
        self.image_label_afm = customtkinter.CTkLabel(self.button_frame_afm, text="{} / {}".format(self.image_view + 1,
                                                                                                   self.image_num))
        self.image_label_afm.grid(row=2, column=1, padx=10, sticky="new")
        self.next_btn_afm = customtkinter.CTkButton(self.button_frame_afm, command=self.next_event, text="Next")
        self.next_btn_afm.grid(row=2, column=2, padx=10, sticky="new")

        # CNO Results
        self.result_label_cno = customtkinter.CTkLabel(self.button_frame_cno,
                                                       text=" ",
                                                       font=customtkinter.CTkFont(size=16, weight="bold"))
        self.result_label_cno.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)
        self.previous_btn_cno = customtkinter.CTkButton(self.button_frame_cno, command=self.previous_event,
                                                        text="Previous")
        self.previous_btn_cno.grid(row=2, column=0, padx=10, sticky="new")
        self.image_label_cno = customtkinter.CTkLabel(self.button_frame_cno,
                                                      text="{} / {}".format(self.image_view + 1, self.image_num))
        self.image_label_cno.grid(row=2, column=1, padx=10, sticky="new")
        self.next_btn_cno = customtkinter.CTkButton(self.button_frame_cno, command=self.next_event, text="Next")
        self.next_btn_cno.grid(row=2, column=2, padx=10, sticky="new")

        # KDE Results
        self.result_label_kde = customtkinter.CTkLabel(self.button_frame_kde,
                                                       text=" ",
                                                       font=customtkinter.CTkFont(size=16, weight="bold"))
        self.result_label_kde.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)
        self.previous_btn_kde = customtkinter.CTkButton(self.button_frame_kde, command=self.previous_event,
                                                        text="Previous")
        self.previous_btn_kde.grid(row=2, column=0, padx=10, sticky="new")
        self.image_label_kde = customtkinter.CTkLabel(self.button_frame_kde,
                                                      text="{} / {}".format(self.image_view + 1, self.image_num))
        self.image_label_kde.grid(row=2, column=1, padx=10, sticky="new")
        self.next_btn_kde = customtkinter.CTkButton(self.button_frame_kde, command=self.next_event, text="Next")
        self.next_btn_kde.grid(row=2, column=2, padx=10, sticky="new")

        self.show_image(self.image_view)

    def next_event(self):
        self.image_view += 1
        if self.image_view > self.image_num - 1:
            self.image_view = self.image_num - 1
        print(self.image_view)
        self.show_image(self.image_view)

    def previous_event(self):
        self.image_view -= 1
        if self.image_view < 0:
            self.image_view = 0
        print(self.image_view)
        self.show_image(self.image_view)

    def stop_event(self):
        self.destroy()

    def show_image(self, image_view):

        self.con_count = self.df['Layer_CNO_0'][image_view]
        self.kde_density = round((self.df['Layer_Density_16'][image_view] +
                                  self.df['Layer_Density_17'][image_view] +
                                  self.df['Layer_Density_18'][image_view]) / 3.0, 4)

        if self.con_count <= 59:
            color = "red"
        else:
            color = "green"

        self.afm_img_result.grid_forget()
        self.afm_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join(self.afm_path, self.afm_files[image_view])),
            size=(IMAGE_WIDTH, IMAGE_HEIGHT))
        self.afm_img_result = customtkinter.CTkLabel(master=self.tabview.tab("AFM"), image=self.afm_image, text='')
        self.afm_img_result.grid(column=0, row=1, padx=20, pady=20, sticky="nsew")
        self.result_label_afm = customtkinter.CTkLabel(self.button_frame_afm,
                                                       text="CNO Count: {} | KDE Density: {}".format(
                                                            self.con_count + 1, self.kde_density),
                                                       font=customtkinter.CTkFont(size=16, weight="bold"),
                                                       text_color=color)
        self.result_label_afm.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)
        self.image_label_afm = customtkinter.CTkLabel(self.button_frame_afm,
                                                      text="{} / {}".format(image_view + 1, self.image_num))
        self.image_label_afm.grid(row=2, column=1, padx=10, sticky="new")

        self.cno_img_result.grid_forget()
        self.cno_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join(self.cno_path, self.cno_files[image_view])),
            size=(IMAGE_WIDTH, IMAGE_HEIGHT))
        self.cno_img_result = customtkinter.CTkLabel(master=self.tabview.tab("CNO"), image=self.cno_image, text='')
        self.cno_img_result.grid(column=0, row=1, padx=20, pady=20, sticky="nsew")
        self.result_label_cno = customtkinter.CTkLabel(self.button_frame_cno,
                                                       text="CNO Count: {} | KDE Density: {}".format(
                                                           self.con_count + 1, self.kde_density),
                                                       font=customtkinter.CTkFont(size=16, weight="bold"),
                                                       text_color=color)
        self.result_label_cno.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)
        self.image_label_cno = customtkinter.CTkLabel(self.button_frame_cno,
                                                      text="{} / {}".format(image_view + 1, self.image_num))
        self.image_label_cno.grid(row=2, column=1, padx=10, sticky="new")

        self.kde_img_result.grid_forget()
        self.kde_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join(self.cno_path, self.kde_files[image_view])),
            size=(IMAGE_WIDTH, IMAGE_HEIGHT))
        self.kde_img_result = customtkinter.CTkLabel(master=self.tabview.tab("KDE"), image=self.kde_image, text='')
        self.kde_img_result.grid(column=0, row=1, padx=20, pady=20, sticky="nsew")
        self.result_label_kde = customtkinter.CTkLabel(self.button_frame_kde,
                                                       text="CNO Count: {} | KDE Density: {}".format(
                                                           self.con_count + 1, self.kde_density),
                                                       font=customtkinter.CTkFont(size=16, weight="bold"),
                                                       text_color=color)
        self.result_label_kde.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="new", columnspan=3)
        self.image_label_kde = customtkinter.CTkLabel(self.button_frame_kde,
                                                      text="{} / {}".format(image_view + 1, self.image_num))
        self.image_label_kde.grid(row=2, column=1, padx=10, sticky="new")


        print(self.afm_files[image_view])
        print(self.cno_files[image_view])
        print(self.kde_files[image_view])
        print('CNO Count: ', self.con_count)
        print('KDE Density: ', self.kde_density)


if __name__ == "__main__":
    app = App()
    app.mainloop()
