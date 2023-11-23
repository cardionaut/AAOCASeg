import os

import numpy as np
import tensorflow as tf
from loguru import logger
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt


class Predict:
    def __init__(self, config) -> None:
        self.model_file = config.segmentation.model_file
        self.batch_size = config.segmentation.batch_size

    def __call__(self, images) -> None:
        self.images = images
        self.normalisation()
        mask = self.inference()

        return mask

    def normalisation(self):
        """Min-max normalisation of the images"""
        self.images = (self.images - self.images.max(axis=(1, 2), keepdims=True)) / (
            self.images.max(axis=(1, 2), keepdims=True) - self.images.min(axis=(1, 2), keepdims=True)
        )

    def inference(self):
        custom_objects = {'BinaryCrossentropy': tf.keras.losses.BinaryCrossentropy}
        model = tf.keras.models.load_model(self.model_file, custom_objects=custom_objects, compile=False)
        mask = np.zeros_like(self.images)
        number_of_frames = self.images.shape[0]

        progress = QProgressDialog()
        progress.setWindowFlags(Qt.Dialog)
        progress.setModal(True)
        progress.setMinimum(0)
        progress.setMaximum(number_of_frames)
        progress.resize(500, 100)
        progress.setValue(0)
        progress.setValue(1)
        progress.setValue(0)  # trick to make progress bar appear
        progress.setWindowTitle("Segmenting frames...")
        progress.show()

        for frame in range(0, number_of_frames, self.batch_size):
            progress.setValue(frame)
            # calling model() instead of model.predict() leads to smaller memory leak
            pred = model(self.images[frame : frame + self.batch_size, :, :], training=False)
            mask[frame : frame + self.batch_size, :, :] = np.array(pred)[0, :, :, :, 0]

        progress.close()

        return mask