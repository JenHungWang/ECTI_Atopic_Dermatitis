# **Stratum corneum nanotexture feature detection using deep learning and spatial analysis: a non-invasive tool for skin barrier assessment**

<img src="./source/Overview.png" alt="Data Processing" width="95%" />

This repository presents an automated approach for the data processing of Atomic Force Microscopy (AFM), enabling the construction of an extensive database for further academic investigation and visualization. The program seamlessly integrates critical steps, including the conversion of raw AFM data into PNG files, the utilization of computer vision techniques, and the implementation of state-of-the-art deep learning algorithms for accurate detection of circular nano objects (CNOs) and classification of various skin diseases. In addition, the algorithm incorporates the grid search method to determine the optimal hyperparameter settings, ensuring optimal performance and enhancing the reliability of the results.

## **Dependencies**
- Python 3.9+
- matplotlib
- numpy
- opencv-python
- scipy
- scikit-image
- ultralytics
- customtkinter
- scikit-learn
- customtkinter

## **Directories**
- `AD_Assessment_GUI.zip` contains a cross-platform executable GUI, sample data, and a tutorial video.
- Folder `corneocyte dataset` contains original corneocyte nanotexture images and annotated images for training AI models.
- Folder `models` contains our fine-tuned YOLOv8-{N,S,M,L,X} and YOLOv9-{C,E} models.

## **Usage**
1. Execution via cross-platform executable GUI
    - Unzip `AD_Assessment_GUI.zip`
    - Run `AD_Assessment_GUI.exe`
    - Analysis results will be saved within the selected path in a folder titled `CNO_Detection`

2. Execution via python script
    - Install packages in terminal:
        ```    
        pip install -r requirements.txt
        ```
    - Run `AD_Assessment_GUI.py`
    - Analysis results will be saved within the selected path in a folder titled `CNO_Detection`

## **Executable**

1. Install PyInstaller in terminal:
                
    ```    
    pip install pyinstaller
    ```
   
2. Run command in terminal:

    ```    
    pyinstaller --onedir .\AD_Assessment_GUI.py
    ```

## **Contributions**

[1] Liao, H-S., Wang, J-H., Raun, E., Nørgaard, L. O., Dons, F. E., & Hwu, E. E-T. (2022). Atopic Dermatitis Severity Assessment using High-Speed Dermal Atomic Force Microscope. Abstract from AFM BioMed Conference 2022, Nagoya-Okazaki, Japan.

[2] Pereda, J., Liao, H-S., Werner, C., Wang, J-H., Huang, K-Y., Raun, E., Nørgaard, L. O., Dons, F. E., & Hwu, E. E. T. (2022). Hacking Consumer Electronics for Biomedical Imaging. Abstract from 5th Global Conference on Biomedical Engineering & Annual Meeting of TSBME, Taipei, Taiwan, Province of China.

[3] Liao, H. S., Akhtar, I., Werner, C., Slipets, R., Pereda, J., Wang, J. H., Raun, E., Nørgaard, L. O., Dons, F. E., & Hwu, E. E. T. (2022). Open-source controller for low-cost and high-speed atomic force microscopy imaging of skin corneocyte nanotextures. HardwareX, 12, [e00341]. https://doi.org/10.1016/j.ohx.2022.e00341

----

### Contact: [Jen-Hung Wang](mailto:jenhw@dtu.dk) / [Professor En-Te Hwu](mailto:etehw@dtu.dk)
