import time

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
        if key == Qt.Key_Right:
            self.setValue(self.value() + 1)
        elif key == Qt.Key_Left:
            self.setValue(self.value() - 1)
        elif key == Qt.Key_Up:
            if self.gatedFrames:
                currentGatedFrame = self.findFrame(self.value())
                currentGatedFrame = currentGatedFrame + 1
                if currentGatedFrame > self.maxFrame:
                    currentGatedFrame = self.maxFrame
                self.setValue(self.gatedFrames[currentGatedFrame])
            else:
                self.setValue(self.value() + 1)
        elif key == Qt.Key_Down:
            if self.gatedFrames:
                currentGatedFrame = self.findFrame(self.value())
                currentGatedFrame = currentGatedFrame - 1
                if currentGatedFrame < 0:
                    currentGatedFrame = 0
                self.setValue(self.gatedFrames[currentGatedFrame])
            else:
                self.setValue(self.value() - 1)
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

    def findFrame(self, currentFrame):
        """Find the closest gated frame.

        Args:
            currentFrame: int, current displayed frame
        Returns:
            currentGatedFrame: int, gated frame closeset to current displayed frame
        """

        frameDiff = [abs(val - currentFrame) for val in self.gatedFrames]
        currentGatedFrame = [idx for idx in range(len(frameDiff)) if frameDiff[idx] == min(frameDiff)][0]

        return currentGatedFrame

    def addGatedFrames(self, gatedFrames):
        """Stores the gated frames."""

        self.gatedFrames = gatedFrames
        self.maxFrame = len(self.gatedFrames) - 1
