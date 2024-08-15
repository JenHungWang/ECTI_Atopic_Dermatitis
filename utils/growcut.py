import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from scipy import ndimage
from matplotlib import cm
from PIL import Image, ImageDraw, ImageFont
from skimage import morphology
from skimage.measure import regionprops


def comp(*ims, figsize=(20, 10)):
    N = len(ims)
    ncols = {1: 1, 2: 2, 3: 3, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 3}
    nrows = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 3}
    fig, axes = plt.subplots(ncols=ncols[N], nrows=nrows[N], sharex=True, sharey=True, figsize=figsize)
    fig.subplots_adjust(wspace=0.01, hspace=0.01)
    axes = axes.ravel()
    cursor = MultiCursor(fig.canvas, axes,
                         horizOn=True, vertOn=True, color='red', linewidth=1)
    for i in range(N):
        axes[i].imshow(ims[i])
    return fig, axes, cursor


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


def G(x):
    return 1 - np.abs(x) ** .5


def growcut(land, labels, strength, maxiter=5):
    Ni, Nj = land.shape
    sidei, sidej = np.arange(Ni), np.arange(Nj)
    ij = np.dstack(np.meshgrid(sidei, sidej))[:, :, ::-1]
    iijj = np.tile(ij, (9, 1, 1, 1))
    for i, k in enumerate(((0, 0), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))):
        iijj[i, :, :, :] += np.array(k)
        iijj[i, :, :, 0] = iijj[i, :, :, 0].clip(0, land.shape[0] - 1)
        iijj[i, :, :, 1] = iijj[i, :, :, 1].clip(0, land.shape[1] - 1)
    neigh_slice = np.s_[iijj[:, :, :, 0], iijj[:, :, :, 1]]

    this_labels = labels * 1
    this_strength = strength * 1

    neigh_val = land[neigh_slice]
    jump_diff = land - neigh_val
    g = G(jump_diff)

    for i in range(maxiter):
        # print(np.sum(this_labels), end=' ')
        neigh_lab = this_labels[neigh_slice] * 1
        neigh_str = this_strength[neigh_slice] * 1

        attack_force = g * neigh_str

        new_layer = np.argmax(attack_force, axis=0)
        new_lab = neigh_lab[new_layer, iijj[0, :, :, 0], iijj[0, :, :, 1]] * 1
        new_strength = attack_force[new_layer, iijj[0, :, :, 0], iijj[0, :, :, 1]] * 1

        this_labels = new_lab
        this_strength = new_strength

    return this_labels, this_strength


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
    # ms = np.array(ms)
    land = np.mean(oom, axis=0)
    return land


def segmentate(land, alpha=0.7, beta=0.6):
    if alpha < beta:
        print("alpha must be greater than beta")
        assert False
    foreground = ndimage.binary_erosion(land > alpha, iterations=1)
    background = land < beta

    lab = ndimage.label(foreground)[0]
    lab[lab > 0] += 1
    lab[background] = 1

    strength = (lab > 1) * 1. + (lab == 1) * 1.
    this_labels, this_strength = growcut(land,
                                         lab, strength, maxiter=25)
    w = (this_labels != np.roll(this_labels, 1, axis=0)) + (this_labels != np.roll(this_labels, 1, axis=1))

    b = w * 0
    lab2 = ndimage.label(~w)[0]
    for l in np.unique(lab2)[1:]:
        if np.sum(foreground[l == lab2]) > 0:
            b[l == lab2] = 1

    lab2 = ndimage.label(ndimage.binary_dilation(this_labels > 1))[0]
    return lab2


def filter_objects(lab2, max_eccentricity=0.93, min_size=10, max_size=200, min_convex_coverage=0.8):
    props = regionprops(lab2)  # object metrics
    b = lab2 * 0.
    for i in np.unique(lab2)[1:]:
        ind = i - 1
        e = props[ind].eccentricity
        s = props[ind].area
        c = s * 1 / props[ind].convex_area
        # filter objects by eccentricity, size, ans convex hull coverage
        if e < max_eccentricity and (min_size < s < max_size) and c > min_convex_coverage:
            lev = 1
        else:
            lev = 2
        b[lab2 == i] = lev
    return b


def present(im, land, b):
    original_im = cm.afmhot(im)[:, :, :3]
    # Contrast Level 0.5
    resim = 0.5 * land + (1 - 0.5) * im
    enhanced_im = cm.afmhot(resim)[:, :, :3]
    monochrome_land = np.tile(land, (3, 1, 1)).transpose((1, 2, 0))
    detected = b == 1
    detected = ndimage.binary_dilation(detected)  # * (~ndimage.binary_erosion(detected))
    filtered = b == 2
    filtered = ndimage.binary_dilation(filtered)  # * (~ndimage.binary_erosion(filtered))

    monochrome_land[detected] *= np.array([.3, 1, .3])
    monochrome_land[filtered] *= np.array([1, .6, .6])

    newim = np.hstack((enhanced_im, monochrome_land))
    newim = np.dstack((newim, newim[:, :, 0] * 0 + 1))

    base = Image.fromarray((newim * 255).astype(np.uint8))
    original_im = Image.fromarray((original_im * 255).astype(np.uint8))
    enhanced_im = Image.fromarray((enhanced_im * 255).astype(np.uint8))

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new("RGBA", base.size, (255, 255, 255, 0))

    # get a font
    # fnt = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 30, encoding="unic")
    fnt = ImageFont.load_default()
    # get a drawing context
    d = ImageDraw.Draw(txt)
    ct = np.max(ndimage.label(b == 1)[0]) - 1
    d.text((600, 10), "CNOs: {:d}".format(ct), font=fnt, fill=(255, 50, 50, 255))
    out = Image.alpha_composite(base, txt)

    return out, original_im, enhanced_im, ct


def treat_one_image(fn, growcut_path, original_png_path, enhanced_png_path):

    file_list = []
    growcut_list = []

    # load data
    im = load_im(fn)

    # pyramid contrast
    land = pyramid_contrast(im)

    # detect objects
    lab2 = segmentate(land, alpha=.75, beta=0.7)

    # visualize
    b = filter_objects(lab2, max_eccentricity=0.967, min_size=30, max_size=200, min_convex_coverage=0.5)
    growcut_im, original_im, enhanced_im, ct = present(im, land, b)

    file_name = os.path.split(fn)[1][0:-10]

    original_im.save(os.path.join(original_png_path, file_name) + '.png')
    enhanced_im.save(os.path.join(enhanced_png_path, file_name) + '.png')
    growcut_im.save(os.path.join(growcut_path, file_name) + '.png')

    return file_name, ct