# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 16:19:15 2023

@author: ansel
"""
import numpy as np
from skimage.restoration import denoise_nl_means, estimate_sigma
from skimage.segmentation import slic, felzenszwalb
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float
import pydicom as dcm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import cv2
import polarTransform

#denoising parameters
patch_size = 7
patch_distance = 11
h = 0.1
sigma = 0.01
# superpixel parameters
n_segments = 250
compactness = 0.08
sigma_super = 1.4
threshold = 0.05

#import the dicom, and change it to a pixel array with values between 0 and 1
ds = dcm.dcmread(r'D:\Documents\2_Coding\Python\AAOCASeg\rest.dcm')
images = np.array(ds.pixel_array)
img = images[780]
img2 = images[100]
img3 = images[900]

img3_gray = (img3 - np.min(img3)) / (np.max(img3) - np.min(img3))


#simple denoising with the non-local means function
def denoising(img, patch_size, patch_distance, h, sigma):
    img_gray = (img - np.min(img)) / (np.max(img) - np.min(img))
    denoised_img = denoise_nl_means(img_gray, patch_size = patch_size, 
                                   patch_distance = patch_distance, 
                                   h = h,  
                                   sigma = sigma,  
                                   fast_mode=True,
                                   channel_axis=None)
    return denoised_img

def superpixel(denoised_img, img, n_segments, compactness, sigma_super, threshold):
    img_gray = (img - np.min(img)) / (np.max(img) - np.min(img))
    segments = slic(denoised_img, n_segments = n_segments, compactness = compactness, sigma = sigma_super)
    segments = segments.astype('float64')
    #for every index of the superpixel get the value of every pixel in original image and take the average
    for i in np.unique(segments):
        xy_number = np.where(segments == i)
        average_pixel_value = np.mean(img_gray[xy_number[0], xy_number[1]])
        segments[segments == i] = float(average_pixel_value)
    segments = np.where(segments <threshold, 0, segments)
    return segments
    
def cartesian_to_polar(img):
    value = np.sqrt(((img.shape[0]/2.0)**2.0)+((img.shape[1]/2.0)**2.0))
    polar_image = cv2.linearPolar(img,(img.shape[0]/2, img.shape[1]/2), value, cv2.WARP_FILL_OUTLIERS)
    return polar_image

def mask_superpixel(polar_image, thresh):
    diff_image = np.abs(np.diff(polar_image, axis=1, prepend=0)) > thresh
    first_trues = np.argmax(diff_image, axis=1)
    diff_image[:, first_trues] = False
    first_trues = np.argmax(diff_image, axis=1)
    # diff_image[:, first_trues:] = True
    for row in range(diff_image.shape[0]):
        diff_image[row, first_trues[row]:] = True
    return diff_image.astype(int)

def mask_superpixel(polar_image, thresh):
    diff_image = np.abs(np.diff(polar_image, axis=1, prepend=0)) > thresh
    first_trues = np.argmax(diff_image, axis=1)
    diff_image[:, first_trues] = False
    rows = np.arange(diff_image.shape[0])
    columns = first_trues[:, np.newaxis]
    diff_image[rows, columns:] = np.tile(True, (diff_image.shape[0], diff_image.shape[1] - first_trues[:, np.newaxis]))
    return diff_image.astype(int)



#change to grayscale with min max scaling
img2_gray = (img2 - np.min(img2)) / (np.max(img2) - np.min(img2))

denoise_img = denoise_nl_means(img2_gray, patch_size=7, 
                               patch_distance=11, 
                               h=0.1,  
                               sigma=.01,  
                               fast_mode=True,
                               channel_axis=None)

#get superpixels for the image
segments = slic(denoise_img, n_segments=250, compactness=0.08, sigma=1.4)
segments = segments.astype('float64')

#for every index of the superpixel get the value of every pixel and take the average
for i in np.unique(segments):
    xy_number = np.where(segments == i)
    average_pixel_value = np.mean(img2_gray[xy_number[0], xy_number[1]])
    segments[segments == i] = float(average_pixel_value)
segments = np.where(segments <0.07, 0, segments)

plt.hist(segments, bins = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])

plt.imshow(segments)
plt.pcolormesh(np.flipud(segments), cmap = 'gray')

denoised_img = denoising(img2, patch_size, patch_distance, h, sigma)
segments = superpixel(denoised_img, img2, n_segments, compactness, sigma_super, threshold)
polar = cartesian_to_polar(segments)
polar_mask = mask_superpixel(polar, thresh=0.10)
plt.imshow(polar_mask)
mask = polarTransform.convertToCartesianImage(polar_mask)
plt.imshow(mask[0])

plt.imshow(denoised_img)
plt.imshow(segments)
plt.imshow(img2)

denoised_img = denoising(img2, patch_size, patch_distance, h, sigma)
segments_fz = felzenszwalb(img2, scale =  250, sigma = 0.01, min_size= 50)
plt.imshow(segments_fz)

polar = cartesian_to_polar(segments)
mask = mask_superpixel(polar, thresh=0.1)
plt.imshow(polar)
plt.imshow(denoised_img)

segments = superpixel(polar, polar, n_segments, compactness, sigma_super, threshold)
plt.imshow(segments)

#felzenswalb
segments_fz = felzenszwalb(denoised_img, scale =  250, sigma = 0.01, min_size= 50)
plt.imshow(segments_fz)