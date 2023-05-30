import os

import numpy as np
from PyQt5.QtWidgets import (
    QErrorMessage,
    QFileDialog,
    QMessageBox,
    QPushButton,
)
from PyQt5.QtCore import Qt

from input_output.read_xml import read
from input_output.write_xml import write_xml, mask_image, get_contours


def readContours(self):
    """Reads contours.

    Reads contours  saved in xml format (Echoplaque compatible) and
    displays the contours in the graphics scene
    """

    if not self.image:
        warning = QErrorMessage()
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Reading of contours failed. Images must be loaded prior to loading contours')
        warning.exec_()
    else:
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "XML file (*.xml)", options=options
        )
        if fileName:
            self.lumen, self.plaque, self.stent, self.resolution, frames = read(fileName)

            if len(self.lumen[0]) != self.dicom.NumberOfFrames:
                warning = QErrorMessage()
                warning.setWindowModality(Qt.WindowModal)
                warning.showMessage(
                    'Reading of contours failed. File must contain the same number of frames as loaded dicom'
                )
                warning.exec_()
            else:
                self.resolution = float(self.resolution[0])
                self.lumen = self.mapToList(self.lumen)
                self.plaque = self.mapToList(self.plaque)
                self.stent = self.mapToList(self.stent)
                self.contours = True
                self.wid.setData(self.lumen, self.plaque, self.stent, self.images)
                self.hideBox.setChecked(False)

                gatedFrames = [
                    frame for frame in range(len(self.lumen[0])) if self.lumen[0][frame] or self.plaque[0][frame]
                ]
                self.gatedFrames = gatedFrames
                self.useGatedBox.setChecked(True)
                self.slider.addGatedFrames(self.gatedFrames)


def writeContours(self, fname=None):
    """Writes contours to an xml file compatible with Echoplaque"""

    patientName = self.infoTable.item(0, 1).text()
    saveName = patientName if fname is None else fname
    self.lumen, self.plaque = self.wid.getData()

    # reformat data for compatibility with write_xml function
    x, y = [], []
    for i in range(len(self.lumen[0])):
        x.append(self.lumen[0][i])
        x.append(self.plaque[0][i])
        y.append(self.lumen[1][i])
        y.append(self.plaque[1][i])

    if not self.segmentation and not self.contours:
        self.errorMessage()
    else:
        frames = list(range(self.numberOfFrames))

        write_xml(
            x,
            y,
            self.images.shape,
            self.resolution,
            self.ivusPullbackRate,
            frames,
            saveName,
        )
        if fname is None:
            self.successMessage("Writing contours")


def autoSave(self):
    """Automatically saves contours to a temporary file every 180 seconds"""

    if self.contours:
        print("Automatically saving current contours")
        self.writeContours("temp")


def segment(self):
    """Segmentation and phenotyping of IVUS images"""
    pass

def newSpline(self):
    """Create a message box to choose what spline to create"""

    b3 = QPushButton("lumen")
    b2 = QPushButton("Vessel")
    b1 = QPushButton("Stent")

    d = QMessageBox()
    d.setText("Select which contour to draw")
    d.setInformativeText(
        "Contour must be closed before proceeding by clicking on initial point"
    )
    d.setWindowModality(Qt.WindowModal)
    d.addButton(b1, 0)
    d.addButton(b2, 1)
    d.addButton(b3, 2)

    result = d.exec_()

    self.wid.new(result)
    self.hideBox.setChecked(False)

def maskToContours(self, masks):
    """Convert numpy mask to IVUS contours"""

    levels = [1.5, 2.5]
    image_shape = masks.shape[1:3]
    masks = mask_image(masks, catheter=0)
    _, _, lumen_pred, plaque_pred = get_contours(masks, levels, image_shape)

    return lumen_pred, plaque_pred

def contourArea(self, x, y):
    """Calculate contour/polygon area using Shoelace formula"""

    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    return area

def computeContourMetrics(self, lumen, plaque):
    """Computes lumen area, plaque area and plaque burden from contours"""

    numberOfFrames = len(lumen[0])
    lumen_area = np.zeros((numberOfFrames))
    plaque_area = np.zeros_like(lumen_area)
    plaque_burden = np.zeros_like(lumen_area)
    for i in range(numberOfFrames):
        if lumen[0][i]:
            lumen_area[i] = (
                self.contourArea(lumen[0][i], lumen[1][i]) * self.resolution**2
            )
            plaque_area[i] = (
                self.contourArea(plaque[0][i], plaque[1][i]) * self.resolution**2
                - lumen_area[i]
            )
            plaque_burden[i] = (
                plaque_area[i] / (lumen_area[i] + plaque_area[i])
            ) * 100

    return (lumen_area, plaque_area, plaque_burden)

def mapToList(self, contours):
    """Converts map to list"""

    x, y = contours
    x = [list(x[i]) for i in range(0, len(x))]
    y = [list(y[i]) for i in range(0, len(y))]

    return (x, y)
