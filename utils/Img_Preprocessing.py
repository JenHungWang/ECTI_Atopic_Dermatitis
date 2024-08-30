# Copyright 2024 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)

import os
import re
import numpy as np
import warnings
from scipy import ndimage
from matplotlib import cm
from PIL import Image
from skimage import morphology

warnings.filterwarnings('ignore')


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
          np.mean(ndimage.gaussian_filter(im, 10), axis=1)).T  # palliate horizontal artifact
    im = im - np.min(im)
    im = im / np.max(im)  # normalize to 0.0-1.0
    return im


def pyramid_contrast(im):
    oom = []
    ms = []
    for d in (9, 15):  # (9, 11, 13, 15, 17,25):#(3, 6, 9, 12, 15, 18, 21):
        disk = morphology.disk(d)
        m = ndimage.percentile_filter(im, 10, footprint=disk)
        M = ndimage.percentile_filter(im, 90, footprint=disk)
        om = (im - m) / (M - m)
        om = np.nan_to_num(om).clip(0, 1)
        oom.append(om)
        ms.append(M - m)
    oom = np.array(oom)
    land = np.mean(oom, axis=0)
    return land


def present(im, land):
    original_im = cm.afmhot(im)[:, :, :3]
    resim = 0.5 * land + (1 - 0.5) * im
    enhanced_im = cm.afmhot(resim)[:, :, :3]
    original_im = Image.fromarray((original_im * 255).astype(np.uint8))
    enhanced_im = Image.fromarray((enhanced_im * 255).astype(np.uint8))

    return original_im, enhanced_im


def treat_one_image(fn, original_png_path, enhanced_png_path):
    # load data
    im = load_im(fn)
    # plt.imshow(im)
    # plt.show()

    # pyramid contrast
    land = pyramid_contrast(im)
    # plt.imshow(land)
    # plt.show()

    # visualize
    original_im, enhanced_im = present(im, land)

    # Save images
    file_name = os.path.split(fn)[1][0:-4]
    original_im.save(os.path.join(original_png_path, file_name) + '.png')
    enhanced_im.save(os.path.join(enhanced_png_path, file_name) + '.png')

    return file_name