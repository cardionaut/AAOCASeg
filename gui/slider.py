import time

import numpy as np
from loguru import logger
from PyQt5.QtWidgets import (
    QSlider,
    QApplication,
    QSizePolicy,
)
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QSize


class Communicate(QObject):
    updateBW = pyqtSignal(int)
    updateBool = pyqtSignal(bool)


class Slider(QSlider):
    """Slider for changing the currently displayed image."""

    def __init__(self, orientation):
        super().__init__()
        self.setOrientation(orientation)
        self.setRange(0, 0)
        self.setValue(0)
        self.setFocusPolicy(Qt.StrongFocus)
        sizePolicy = QSizePolicy()
        sizePolicy.setHorizontalPolicy(QSizePolicy.Fixed)
        sizePolicy.setVerticalPolicy(QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(800, 25))
        self.setMaximumSize(QSize(800, 25))
        self.gatedFrames = []

    def keyPressEvent(self, event):
        """Key events."""

        key = event.key()
        if key == Qt.Key_Right or key == Qt.Key_D:
            self.setValue(self.value() + 1)
        elif key == Qt.Key_Left or key == Qt.Key_A:
            self.setValue(self.value() - 1)
        elif key == Qt.Key_Up or key == Qt.Key_W:
            self.next_gated_frame()
        elif key == Qt.Key_Down or key == Qt.Key_S:
            self.last_gated_frame()
        elif key == Qt.Key_J:
            self.setValue(self.value() - 1)
            QApplication.processEvents()
            time.sleep(0.1)
            self.setValue(self.value() + 1)
            QApplication.processEvents()
            time.sleep(0.1)
            self.setValue(self.value() + 1)
            QApplication.processEvents()
            time.sleep(0.1)
            self.setValue(self.value() - 1)
            QApplication.processEvents()

    def next_gated_frame(self):
        if self.gatedFrames:
            currentGatedFrame = self.findFrame(self.value())
            currentGatedFrame = currentGatedFrame + 1
            if currentGatedFrame > self.maxFrame:
                currentGatedFrame = self.maxFrame
            self.setValue(self.gatedFrames[currentGatedFrame])
        else:
            self.setValue(self.value() + 1)

    def last_gated_frame(self):
        if self.gatedFrames:
            currentGatedFrame = self.findFrame(self.value())
            currentGatedFrame = currentGatedFrame - 1
            if currentGatedFrame < 0:
                currentGatedFrame = 0
            self.setValue(self.gatedFrames[currentGatedFrame])
        else:
            self.setValue(self.value() - 1)

    def findFrame(self, currentFrame):
        """Find the closest gated frame"""
        gated_frames = np.asarray(self.gatedFrames)
        closest_gated_frame = np.argmin(np.abs(gated_frames - currentFrame))

        return closest_gated_frame

    def addGatedFrames(self, gatedFrames):
        """Stores the gated frames."""

        self.gatedFrames = gatedFrames
        self.maxFrame = len(self.gatedFrames) - 1
