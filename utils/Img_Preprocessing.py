# Copyright 2024 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)

import os
import re
import numpy as np
import warnings
import matplotlib.pyplot as plt
from scipy import ndimage
from matplotlib import cm
from PIL import Image
from skimage import io, morphology
from NSFopen import read


warnings.filterwarnings('ignore')  # Suppress warnings


# Load an image from a file and preprocess it to remove horizontal artifacts and normalize its intensity
def load_im(fn):
    f = open(fn, 'rb')
    a = f.read()
    f.close()
    aa = str(a[:2048])
    xpix = int(re.findall('xpixels\s?=\s?([0-9]*)', aa)[0])
    ypix = int(re.findall('ypixels\s?=\s?([0-9]*)', aa)[0])
    a = a[2048:]

    words = [a[k * 2:k * 2 + 2] for k in range(xpix * ypix)]
    arr = [int.from_bytes(words[k], byteorder='little', signed=True) for k in range(len(words))]
    im = np.array(arr).reshape((ypix, xpix))

    im = (im.T - np.mean(im, axis=1) +
          np.mean(ndimage.gaussian_filter(im, 10), axis=1)).T  # Reduce horizontal artifacts

    im = im - np.min(im)
    im = im / np.max(im)  # normalize to 0.0-1.0
    return im


# Helper function to normalize and convert array to uint8
def normalize_to_uint8(array):
    array = np.array(array, dtype=float)
    array = np.flipud(array)  # Flip vertically to fix orientation
    min_val = np.min(array)
    ptp_val = np.ptp(array)  # Peak-to-peak (max - min)
    if ptp_val == 0:
        return np.zeros_like(array, dtype=np.uint8)
    norm_array = 255 * (array - min_val) / ptp_val
    return norm_array.astype(np.uint8)


# Apply pyramid contrast enhancement to an image
def pyramid_contrast(im):
    oom = []
    # Different disk sizes for contrast enhancement
    for d in (9, 15): # (9, 11, 13, 15, 17,25): #(3, 6, 9, 12, 15, 18, 21):
        disk = morphology.disk(d)
        m = ndimage.percentile_filter(im, 10, footprint=disk)
        M = ndimage.percentile_filter(im, 90, footprint=disk)
        om = (im - m) / (M - m)
        om = np.nan_to_num(om).clip(0, 1)
        # plt.imshow(om)
        # plt.show()
        oom.append(om)

    oom = np.array(oom)
    land = np.mean(oom, axis=0)
    return land


# Visualize the original and enhanced images using a colormap
def present(im, land):
    original_im = cm.afmhot(im)[:, :, :3]
    resim = 0.5 * land + (1 - 0.5) * im
    enhanced_im = cm.afmhot(resim)[:, :, :3]
    original_im = Image.fromarray((original_im * 255).astype(np.uint8))
    enhanced_im = Image.fromarray((enhanced_im * 255).astype(np.uint8))

    return original_im, enhanced_im


# Process a single .nid file, extract Forward/Backward data, and apply contrast enhancement
def process_nid_file(fn, original_png_path, enhanced_png_path):
    try:
        data = read(fn)
        # Extract Z-Axis data
        forward_data = data.data["Image"]["Forward"]["Z-Axis"]
        backward_data = data.data["Image"]["Backward"]["Z-Axis"]

        # Base name without extension
        base = os.path.splitext(os.path.basename(fn))[0]

        # Process forward data
        im = np.array(forward_data, dtype=float)
        im = np.flipud(im)  # Flip vertically to match .bcr orientation
        # Reduce horizontal artifacts (as in load_im)
        im = (im.T - np.mean(im, axis=1) +
              np.mean(ndimage.gaussian_filter(im, 10), axis=1)).T
        # Normalize to 0.0–1.0 (as in load_im)
        im = im - np.min(im)
        im = im / np.max(im) if np.max(im) != 0 else im
        land = pyramid_contrast(im)
        original_im, enhanced_im = present(im, land)
        original_im.save(os.path.join(original_png_path, f"{base}_forward.png"))
        enhanced_im.save(os.path.join(enhanced_png_path, f"{base}_forward.png"))

        # Process backward data
        im = np.array(backward_data, dtype=float)
        im = np.flipud(im)  # Flip vertically to match .bcr orientation
        # Reduce horizontal artifacts (as in load_im)
        im = (im.T - np.mean(im, axis=1) +
              np.mean(ndimage.gaussian_filter(im, 10), axis=1)).T
        # Normalize to 0.0–1.0 (as in load_im)
        im = im - np.min(im)
        im = im / np.max(im) if np.max(im) != 0 else im
        land = pyramid_contrast(im)
        original_im, enhanced_im = present(im, land)
        original_im.save(os.path.join(original_png_path, f"{base}_backward.png"))
        enhanced_im.save(os.path.join(enhanced_png_path, f"{base}_backward.png"))

        return [f"{base}_backward", f"{base}_forward"]
    except Exception as e:
        print(f"Failed to process {fn}: {e}")
        return None


# Process a single image file, enhance its contrast, and save the original and enhanced images
def treat_one_image(fn, original_png_path, enhanced_png_path, file_type):
    # Load image
    if file_type == "nid":
        file_name = process_nid_file(fn, original_png_path, enhanced_png_path)
    elif file_type == "bcr":
        im = load_im(fn)
        # plt.imshow(im)
        # plt.show()

        # Enhance contrast using pyramid contrast
        land = pyramid_contrast(im)
        # plt.imshow(land)
        # plt.show()

        # Visualize and save the original and enhanced images
        original_im, enhanced_im = present(im, land)
        file_name = os.path.split(fn)[1][0:-4]
        original_im.save(os.path.join(original_png_path, file_name) + '.png')
        enhanced_im.save(os.path.join(enhanced_png_path, file_name) + '.png')

    return file_name

