import numpy as np
from skimage.restoration import denoise_nl_means, estimate_sigma
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float
import pydicom as dcm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
#from findpeaks import findpeaks

ds = dcm.dcmread(r'D:\Documents\2_Coding\Python\AAOCASeg\rest.dcm')
images = np.array(ds.pixel_array)
img = images[780]
img2 = images[100]

sigma_est = np.mean(estimate_sigma(img, channel_axis=None))

denoise_img = denoise_nl_means(img2, patch_size=7, 
                               patch_distance=11, 
                               h=0.1,  
                               sigma=.01, 
                               #multichannel=False, 
                               fast_mode=True,
                               channel_axis=None)

#function to 3d plot comparison of original and filter
def plot3DFilterComparison(img, ax):
    if np.amax(img) < 1.01:
        img = img * 250
    else:
        img
    xx, yy = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    ax.plot_surface(xx, yy, img, rstride=1, cstride=1, cmap=plt.cm.magma, linewidth=0)
    ax.set_zlim(0,150)

# Create the figure and subplots
fig, axs = plt.subplots(1, 2, subplot_kw={'projection': '3d'})
# Plot the images
plot3DFilterComparison(img2, axs[0])
plot3DFilterComparison(denoise_img, axs[1])
fig.subplots_adjust(wspace=0.4) # Adjust the spacing between subplots
plt.show()

#NLM filter 


#Curvlet thresholding


#Guided image filter





# #comparison of different filters with findpeaks
# filters = [None, 'lee','lee_enhanced','kuan', 'fastnl','bilateral','frost','median','mean']

# for getfilter in filters:
#     fp = findpeaks(method='topology', scale=False, denoise=getfilter, togray=True, imsize=False, window=15)
#     fp.fit(img2)
#     fp.plot_mesh(wireframe=False, title=str(getfilter), view=(30,30))

# # filters parameters
# winsize = 15
# k_value1 = 2.0
# k_value2 = 1.0
# cu_value = 0.25
# cu_lee_enhanced = 0.523
# cmax_value = 1.73

# # Some pre-processing
# img = findpeaks.stats.togray(img2)
# img = findpeaks.stats.scale(img2)

# # Denoising
# # fastnl
# img_fastnl = findpeaks.stats.denoise(img2, method='fastnl', window=winsize)
# # bilateral
# img_bilateral = findpeaks.stats.denoise(img2, method='bilateral', window=winsize)
# # frost filter
# image_frost = findpeaks.frost_filter(img2, damping_factor=k_value1, win_size=winsize)
# # kuan filter
# image_kuan = findpeaks.kuan_filter(img2, win_size=winsize, cu=cu_value)
# # lee filter
# image_lee = findpeaks.lee_filter(img2, win_size=winsize, cu=cu_value)
# # lee enhanced filter
# image_lee_enhanced = findpeaks.lee_enhanced_filter(img2, win_size=winsize, k=k_value2, cu=cu_lee_enhanced, cmax=cmax_value)
# # mean filter
# image_mean = findpeaks.mean_filter(img2, win_size=winsize)
# # median filter
# image_median = findpeaks.median_filter(img2, win_size=winsize)


# plt.figure(); plt.imshow(img_fastnl, cmap='gray'); plt.title('Fastnl')
# plt.figure(); plt.imshow(img_bilateral, cmap='gray'); plt.title('Bilateral')
# plt.figure(); plt.imshow(image_frost, cmap='gray'); plt.title('Frost')
# plt.figure(); plt.imshow(image_kuan, cmap='gray'); plt.title('Kuan')
# plt.figure(); plt.imshow(image_lee, cmap='gray'); plt.title('Lee')
# plt.figure(); plt.imshow(image_lee_enhanced, cmap='gray'); plt.title('Lee Enhanced')
# plt.figure(); plt.imshow(image_mean, cmap='gray'); plt.title('Mean')
# plt.figure(); plt.imshow(image_median, cmap='gray'); plt.title('Median')
# plt.show()



# #superpixel
# segments = slic(denoise_img, n_segments=250, compactness=0.08, sigma=1.4)
# segments[segments<20] = 0

# fig=plt.figure("superpixels-- %d segments"%(250))
# ax = fig.add_subplot(1,1,1)
# ax.imshow(mark_boundaries(denoise_img, segments, color=(1,1,1), outline_color=(1,1,1)))
# plt.axis("off")
# plt.show()

# plt.imshow(denoise_img, interpolation='nearest')
# plt.show()