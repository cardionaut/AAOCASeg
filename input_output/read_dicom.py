import os

import pydicom as dcm
import numpy as np
from loguru import logger
from PyQt5.QtWidgets import (
    QInputDialog,
    QMessageBox,
    QLineEdit,
    QFileDialog,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt

from input_output.contours import readContours


def readDICOM(window):
    """Reads DICOM images.

    Reads the dicom images and metadata. Places metatdata in a table.
    Images are displayed in the graphics scene.
    """
    if window.image:
        window.save_before_close()

    window.status_bar.showMessage('Reading DICOM file...')

    options = QFileDialog.Options()
    options = QFileDialog.DontUseNativeDialog
    # fileName, _ = QFileDialog.getOpenFileName(
    #     self, "QFileDialog.getOpenFileName()", "", "DICOM files (*.dcm);;All files (*)", options=options
    # )
    fileName, _ = QFileDialog.getOpenFileName(
        window, "QFileDialog.getOpenFileName()", "", "All files (*)", options=options
    )

    if fileName:
        try:
            window.dicom = dcm.read_file(fileName, force=True)
            window.images = window.dicom.pixel_array
            window.file_name = fileName
        except:
            error = QMessageBox()
            error.setIcon(QMessageBox.Critical)
            error.setWindowTitle("Error")
            error.setModal(True)
            error.setWindowModality(Qt.WindowModal)
            error.setText("File is not a valid IVUS file and could not be loaded")
            error.exec_()
            return None

        window.slider.setMaximum(window.dicom.NumberOfFrames - 1)
        window.image = True
        parseDICOM(window)
        window.numberOfFrames = int(window.dicom.NumberOfFrames)
        window.infoTable.setItem(0, 1, QTableWidgetItem(window.patientName))
        window.infoTable.setItem(1, 1, QTableWidgetItem(window.patientBirthDate))
        window.infoTable.setItem(2, 1, QTableWidgetItem(window.patientSex))
        window.infoTable.setItem(3, 1, QTableWidgetItem(str(window.ivusPullbackRate)))
        window.infoTable.setItem(4, 1, QTableWidgetItem(str(window.resolution)))
        window.infoTable.setItem(5, 1, QTableWidgetItem(str(window.rows)))
        window.infoTable.setItem(6, 1, QTableWidgetItem(window.manufacturer))
        window.infoTable.setItem(7, 1, QTableWidgetItem((window.model)))

        if len(window.lumen) != 0:
            reinitializeContours = len(window.lumen) != window.numberOfFrames
        else:
            reinitializeContours = False

        if not window.lumen or reinitializeContours:
            window.lumen = ([[] for _ in range(window.numberOfFrames)], [[] for _ in range(window.numberOfFrames)])
            window.plaque = ([[] for _ in range(window.numberOfFrames)], [[] for _ in range(window.numberOfFrames)])
            window.stent = ([[] for _ in range(window.numberOfFrames)], [[] for _ in range(window.numberOfFrames)])

        window.wid.setData(window.lumen, window.plaque, window.stent, window.images)
        window.slider.setValue(window.numberOfFrames - 1)

        # read contours if available
        try:
            readContours(window, os.path.splitext(window.file_name)[0] + '_contours.xml')
            window.segmentation = True
            try:
                window.gated_frames_dia = [frame for frame in range(window.numberOfFrames) if window.phases[frame] == 'D']
                window.gated_frames_sys = [frame for frame in range(window.numberOfFrames) if window.phases[frame] == 'S']
            except IndexError:  # old contour files may not have phases attr
                pass
            window.gated_frames = window.gated_frames_dia
            window.slider.addGatedFrames(window.gated_frames)
        except FileNotFoundError:
            window.phases = ['-'] * window.numberOfFrames
            pass

    window.status_bar.showMessage('Waiting for user input')


def parseDICOM(window):
    """Parses DICOM metadata"""

    if len(window.dicom.PatientName.encode('ascii')) > 0:
        window.patientName = window.dicom.PatientName.original_string.decode('utf-8')
    else:
        window.patientName = 'Unknown'

    if len(window.dicom.PatientBirthDate) > 0:
        window.patientBirthDate = window.dicom.PatientBirthDate
    else:
        window.patientBirthDate = 'Unknown'

    if len(window.dicom.PatientSex) > 0:
        window.patientSex = window.dicom.PatientSex
    else:
        window.patientSex = 'Unknown'

    if window.dicom.get('IVUSPullbackRate'):
        window.ivusPullbackRate = float(window.dicom.IVUSPullbackRate)
    # check Boston private tag
    elif window.dicom.get(0x000B1001):
        window.ivusPullbackRate = float(window.dicom[0x000B1001].value)
    else:
        window.ivusPullbackRate, _ = QInputDialog.getText(
            window,
            "Pullback Speed",
            "No pullback speed found, please enter pullback speeed (mm/s)",
            QLineEdit.Normal,
            "0.5",
        )
        window.ivusPullbackRate = float(window.ivusPullbackRate)

    if window.dicom.get('FrameTimeVector'):
        frameTimeVector = window.dicom.get('FrameTimeVector')
        frameTimeVector = [float(frame) for frame in frameTimeVector]
        pullbackTime = np.cumsum(frameTimeVector) / 1000  # assume in ms
        window.pullbackLength = pullbackTime * float(window.ivusPullbackRate)
    else:
        window.pullbackLength = np.zeros((window.images.shape[0],))

    if window.dicom.get('SequenceOfUltrasoundRegions'):
        if window.dicom.SequenceOfUltrasoundRegions[0].PhysicalUnitsXDirection == 3:
            # pixels are in cm, convert to mm
            window.resolution = window.dicom.SequenceOfUltrasoundRegions[0].PhysicalDeltaX * 10
        else:
            # assume mm
            window.resolution = window.dicom.SequenceOfUltrasoundRegions[0].PhysicalDeltaX
    elif window.dicom.get('PixelSpacing'):
        window.resolution = float(window.dicom.PixelSpacing[0])
    else:
        resolution, done = QInputDialog.getText(
            window, "Pixel Spacing", "No pixel spacing info found, please enter pixel spacing (mm)", QLineEdit.Normal, ""
        )
        window.resolution = float(resolution)

    if window.dicom.get('Rows'):
        window.rows = window.dicom.Rows
    else:
        window.rows = window.images.shape[1]

    if window.dicom.get('Manufacturer'):
        window.manufacturer = window.dicom.Manufacturer
    else:
        window.manufacturer = 'Unknown'

    if window.dicom.get('ManufacturerModelName'):
        window.model = window.dicom.ManufacturerModelName
    else:
        window.model = 'Unknown'

    # if pixel data is described by luminance (Y) and chominance (B & R)
    # only occurs when SamplesPerPixel==3
    # if self.dicom.get('PhotometricInterpretation') == 'YBR_FULL_422':
    #    #self.images = np.mean(self.images, 3, dtype=np.uint8)
    #    self.images = np.ascontiguousarray(self.images)[:, :, :, 0]
