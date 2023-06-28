import os

import numpy as np
from loguru import logger
from skimage.draw import polygon2mask
from PyQt5.QtWidgets import (
    QErrorMessage,
    QFileDialog,
    QMessageBox,
    QPushButton,
)
from PyQt5.QtCore import Qt

from input_output.read_xml import read
from input_output.write_xml import write_xml, mask_image, get_contours
from segmentation.tf_predict import predict


def readContours(window, fileName=None):
    """Reads contours.

    Reads contours  saved in xml format (Echoplaque compatible) and
    displays the contours in the graphics scene
    """

    if not window.image:
        warning = QErrorMessage(window)
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
        window.lumen, window.plaque, window.stent, window.resolution, _, window.phases = read(fileName)

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
        warning = QErrorMessage(window)
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Cannot write contours before reading DICOM file')
        warning.exec_()
        return

    window.lumen, window.plaque = window.wid.getData()

    # reformat data for compatibility with write_xml function
    x, y = [], []
    for i in range(window.numberOfFrames):
        if i < len(window.lumen[0]):
            new_x_lumen = window.lumen[0][i]
            new_y_lumen = window.lumen[1][i]
        else:
            new_x_lumen = []
            new_y_lumen = []

        if i < len(window.plaque[0]):
            new_x_plaque = window.plaque[0][i]
            new_y_plaque = window.plaque[1][i]
        else:
            new_x_plaque = []
            new_y_plaque = []

        x.append(new_x_lumen)
        x.append(new_x_plaque)
        y.append(new_y_lumen)
        y.append(new_y_plaque)

    write_xml(
        x,
        y,
        window.images.shape,
        window.resolution,
        window.ivusPullbackRate,
        window.phases,
        window.file_name,
    )


def reset_contours(window):
    window.contours = False
    window.lumen = None
    window.plaque = None
    window.stent = None


def segment(window):
    """Segmentation and phenotyping of IVUS images"""
    window.status_bar.showMessage('Segmenting all gated frames...')
    if not window.image:
        warning = QErrorMessage(window)
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Cannot perform automatic segmentation before reading DICOM file')
        warning.exec_()
        window.status_bar.showMessage('Waiting for user input...')
        return

    save_path = os.path.join(os.getcwd(), "model", "saved_model.pb")
    if not os.path.isfile(save_path):
        message = "No saved weights have been found, check that weights are saved in {}".format(
            os.path.join(os.getcwd(), "model")
        )
        error = QMessageBox()
        error.setIcon(QMessageBox.Critical)
        error.setWindowTitle("Error")
        error.setModal(True)
        error.setWindowModality(Qt.WindowModal)
        error.setText(message)
        error.exec_()
        window.status_bar.showMessage('Waiting for user input...')
        return -1

    # warning = QErrorMessage()
    # warning.setWindowModality(Qt.WindowModal)
    # warning.showMessage(
    #     "Warning: IVUS Phenotyping is currently only supported for 20MHz images. Interpret other images with extreme caution"
    # )
    # warning.exec_()

    image_dim = window.images.shape

    if hasattr(window, 'masks'):  # keep previous segmentation
        masks = window.masks
    else:  # perform first segmentation
        masks = np.zeros((window.numberOfFrames, image_dim[1], image_dim[2]), dtype=np.uint8)

    masks[window.gated_frames, :, :] = predict(window.images[window.gated_frames, :, :])
    window.masks = masks

    # compute metrics such as plaque burden
    window.metrics = computeMetrics(window, masks)

    # convert masks to contours
    window.lumen, window.plaque = maskToContours(masks)
    window.contours = True

    # stent contours currently unsupported so create empty list
    window.stent = [
        [[] for _ in range(image_dim[0])],
        [[] for _ in range(image_dim[0])],
    ]

    window.wid.setData(window.lumen, window.plaque, window.stent, window.images)
    window.hideBox.setChecked(False)
    window.status_bar.showMessage('Waiting for user input...')


def newSpline(window):
    """Create a message box to choose what spline to create"""

    if not window.image:
        warning = QErrorMessage(window)
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


def contoursToMask(images, lumen, plaque):
    """Convert IVUS contours to numpy mask"""
    image_shape = images.shape[1:3]
    mask = np.zeros_like(images)
    for frame in range(images.shape[0]):
        try:
            lumen_polygon = [[x, y] for x, y in zip(lumen[1][frame], lumen[0][frame])]
            mask[frame, :, :] += polygon2mask(image_shape, lumen_polygon).astype(np.uint8)
        except ValueError:
            pass
        try:
            vessel_polygon = [[x, y] for x, y in zip(plaque[1][frame], plaque[0][frame])]
            mask[frame, :, :] += polygon2mask(image_shape, vessel_polygon).astype(np.uint8) * 2
        except ValueError:
            pass
    mask = np.clip(mask, a_min=0, a_max=2)  # enforce correct value range

    return mask


def computeMetrics(window, masks):
    """Measures lumen area, plaque area and plaque burden"""

    lumen, plaque = 1, 2
    lumen_area = np.sum(masks == lumen, axis=(1, 2)) * window.resolution**2
    plaque_area = np.sum(masks == plaque, axis=(1, 2)) * window.resolution**2
    plaque_burden = (plaque_area / (lumen_area + plaque_area)) * 100

    return (lumen_area, plaque_area, plaque_burden)


def mapToList(contours):
    """Converts map to list"""

    x, y = contours
    x = [list(x[i]) for i in range(0, len(x))]
    y = [list(y[i]) for i in range(0, len(y))]

    return (x, y)
