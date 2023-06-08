import os

import numpy as np
from loguru import logger
from PyQt5.QtWidgets import (
    QErrorMessage,
    QFileDialog,
    QMessageBox,
    QPushButton,
)
from PyQt5.QtCore import Qt

from input_output.read_xml import read
from input_output.write_xml import write_xml, mask_image, get_contours


def readContours(window, fileName=None):
    """Reads contours.

    Reads contours  saved in xml format (Echoplaque compatible) and
    displays the contours in the graphics scene
    """

    if not window.image:
        warning = QErrorMessage()
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Reading of contours failed. Images must be loaded prior to loading contours')
        warning.exec_()
        return

    if fileName is None:
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            window, "QFileDialog.getOpenFileName()", "", "XML file (*.xml)", options=options
        )

    if fileName:
        window.lumen, window.plaque, window.stent, window.resolution, _ = read(fileName)

        window.resolution = float(window.resolution[0])
        window.lumen = mapToList(window.lumen)
        window.plaque = mapToList(window.plaque)
        window.stent = mapToList(window.stent)
        window.contours = True
        window.wid.setData(window.lumen, window.plaque, window.stent, window.images)
        window.hideBox.setChecked(False)


def writeContours(window):
    """Writes contours to an xml file compatible with Echoplaque"""

    if not window.image:
        warning = QErrorMessage()
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Cannot write contours before reading DICOM file')
        warning.exec_()
        return

    window.lumen, window.plaque = window.wid.getData()

    # reformat data for compatibility with write_xml function
    x, y = [], []
    for i in range(len(window.lumen[0])):
        if i < len(window.plaque[0]):
            new_x_plaque = window.plaque[0][i]
            new_y_plaque = window.plaque[1][i]
        else:
            new_x_plaque = []
            new_y_plaque = []

        x.append(window.lumen[0][i])
        x.append(new_x_plaque)
        y.append(window.lumen[1][i])
        y.append(new_y_plaque)

    if not window.segmentation and not window.contours:
        window.errorMessage()

    frames = list(range(window.numberOfFrames))
    write_xml(
        x,
        y,
        window.images.shape,
        window.resolution,
        window.ivusPullbackRate,
        frames,
        window.file_name,
    )


def reset_contours(window):
    window.contours = False
    window.lumen = None
    window.plaque = None
    window.stent = None


def segment(window):
    """Segmentation and phenotyping of IVUS images"""
    pass


def newSpline(window):
    """Create a message box to choose what spline to create"""

    if not window.image:
        warning = QErrorMessage()
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Cannot create manual contour before reading DICOM file')
        warning.exec_()
        return

    b1 = QPushButton("Stent")
    b2 = QPushButton("Vessel")
    b3 = QPushButton("Lumen")

    d = QMessageBox()
    d.setText("Select which contour to draw")
    d.setInformativeText("Contour must be closed before proceeding by clicking on initial point")
    d.setWindowModality(Qt.WindowModal)
    d.addButton(b1, 0)
    d.addButton(b2, 1)
    d.addButton(b3, 2)

    result = d.exec_()

    window.wid.new(window, result)
    window.hideBox.setChecked(False)
    window.contours = True


def maskToContours(masks):
    """Convert numpy mask to IVUS contours"""

    levels = [1.5, 2.5]
    image_shape = masks.shape[1:3]
    masks = mask_image(masks, catheter=0)
    _, _, lumen_pred, plaque_pred = get_contours(masks, levels, image_shape)

    return lumen_pred, plaque_pred


def contourArea(x, y):
    """Calculate contour/polygon area using Shoelace formula"""

    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    return area


def computeContourMetrics(window, lumen, plaque):
    """Computes lumen area, plaque area and plaque burden from contours"""

    numberOfFrames = len(lumen[0])
    lumen_area = np.zeros((numberOfFrames))
    plaque_area = np.zeros_like(lumen_area)
    plaque_burden = np.zeros_like(lumen_area)
    for i in range(numberOfFrames):
        if lumen[0][i]:
            lumen_area[i] = contourArea(lumen[0][i], lumen[1][i]) * window.resolution**2
            plaque_area[i] = contourArea(plaque[0][i], plaque[1][i]) * window.resolution**2 - lumen_area[i]
            plaque_burden[i] = (plaque_area[i] / (lumen_area[i] + plaque_area[i])) * 100

    return (lumen_area, plaque_area, plaque_burden)


def mapToList(contours):
    """Converts map to list"""

    x, y = contours
    x = [list(x[i]) for i in range(0, len(x))]
    y = [list(y[i]) for i in range(0, len(y))]

    return (x, y)
