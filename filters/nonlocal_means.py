from loguru import logger
import numpy as np
import matplotlib.pyplot as plt
from skimage.restoration import denoise_nl_means, estimate_sigma


class NonLocalMeansFilter:
    def __init__(self, config) -> None:
        self.patch_size = config.filters.nonlocal_means.patch_size
        self.patch_distance = config.filters.nonlocal_means.patch_distance
        self.h = config.filters.nonlocal_means.h
        self.fast_mode = config.filters.nonlocal_means.fast_mode
        self.sigma = config.filters.nonlocal_means.sigma
        self.preserve_range = config.filters.nonlocal_means.preserve_range
        self.channel_axis = 0

    def __call__(self, array):
        sigma = estimate_sigma(array, average_sigmas=True, channel_axis=None)
        denoised_array = denoise_nl_means(
            array,
            patch_size=self.patch_size,
            patch_distance=self.patch_distance,
            h=self.h,
            fast_mode=self.fast_mode,
            sigma=sigma,
            channel_axis=self.channel_axis
        )
        denoised_array = (denoised_array * 255).astype(np.uint8)

        return denoised_array
