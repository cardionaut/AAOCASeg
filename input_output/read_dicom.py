import pydicom as dcm
import numpy as np
from PyQt5.QtWidgets import (
    QInputDialog,
    QMessageBox,
    QLineEdit,
    QFileDialog,
    QTableWidgetItem,
)

from PyQt5.QtCore import Qt


def readDICOM(self):
    """Reads DICOM images.

    Reads the dicom images and metadata. Places metatdata in a table.
    Images are displayed in the graphics scene.
    """

    options = QFileDialog.Options()
    options = QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(
        self, "QFileDialog.getOpenFileName()", "", "DICOM files (*.dcm);;All files (*)", options=options
    )

    if fileName:
        try:
            self.dicom = dcm.read_file(fileName, force=True)
            self.images = self.dicom.pixel_array
        except:
            error = QMessageBox()
            error.setIcon(QMessageBox.Critical)
            error.setWindowTitle("Error")
            error.setModal(True)
            error.setWindowModality(Qt.WindowModal)
            error.setText("File is not a valid IVUS file and could not be loaded")
            error.exec_()
            return None

        self.slider.setMaximum(self.dicom.NumberOfFrames - 1)
        self.image = True
        self.parseDICOM()
        self.numberOfFrames = int(self.dicom.NumberOfFrames)
        self.infoTable.setItem(0, 1, QTableWidgetItem(self.patientName))
        self.infoTable.setItem(1, 1, QTableWidgetItem(self.patientBirthDate))
        self.infoTable.setItem(2, 1, QTableWidgetItem(self.patientSex))
        self.infoTable.setItem(3, 1, QTableWidgetItem(str(self.ivusPullbackRate)))
        self.infoTable.setItem(4, 1, QTableWidgetItem(str(self.resolution)))
        self.infoTable.setItem(5, 1, QTableWidgetItem(str(self.rows)))
        self.infoTable.setItem(6, 1, QTableWidgetItem(self.manufacturer))
        self.infoTable.setItem(7, 1, QTableWidgetItem((self.model)))

        if len(self.lumen) != 0:
            reinitializeContours = len(self.lumen) != self.numberOfFrames
        else:
            reinitializeContours = False

        if not self.lumen or reinitializeContours:
            self.lumen = ([[] for _ in range(self.numberOfFrames)], [[] for _ in range(self.numberOfFrames)])
            self.plaque = ([[] for _ in range(self.numberOfFrames)], [[] for _ in range(self.numberOfFrames)])
            self.stent = ([[] for _ in range(self.numberOfFrames)], [[] for _ in range(self.numberOfFrames)])

        self.wid.setData(self.lumen, self.plaque, self.stent, self.images)
        self.slider.setValue(self.numberOfFrames - 1)


def parseDICOM(self):
    """Parses DICOM metadata"""

    if len(self.dicom.PatientName.encode('ascii')) > 0:
        self.patientName = self.dicom.PatientName.original_string.decode('utf-8')
    else:
        self.patientName = 'Unknown'

    if len(self.dicom.PatientBirthDate) > 0:
        self.patientBirthDate = self.dicom.PatientBirthDate
    else:
        self.patientBirthDate = 'Unknown'

    if len(self.dicom.PatientSex) > 0:
        self.patientSex = self.dicom.PatientSex
    else:
        self.patientSex = 'Unknown'

    if self.dicom.get('IVUSPullbackRate'):
        self.ivusPullbackRate = float(self.dicom.IVUSPullbackRate)
    # check Boston private tag
    elif self.dicom.get(0x000B1001):
        self.ivusPullbackRate = float(self.dicom[0x000B1001].value)
    else:
        self.ivusPullbackRate, _ = QInputDialog.getText(
            self,
            "Pullback Speed",
            "No pullback speed found, please enter pullback speeed (mm/s)",
            QLineEdit.Normal,
            "0.5",
        )
        self.ivusPullbackRate = float(self.ivusPullbackRate)

    if self.dicom.get('FrameTimeVector'):
        frameTimeVector = self.dicom.get('FrameTimeVector')
        frameTimeVector = [float(frame) for frame in frameTimeVector]
        pullbackTime = np.cumsum(frameTimeVector) / 1000  # assume in ms
        self.pullbackLength = pullbackTime * float(self.ivusPullbackRate)
    else:
        self.pullbackLength = np.zeros((self.images.shape[0],))

    if self.dicom.get('SequenceOfUltrasoundRegions'):
        if self.dicom.SequenceOfUltrasoundRegions[0].PhysicalUnitsXDirection == 3:
            # pixels are in cm, convert to mm
            self.resolution = self.dicom.SequenceOfUltrasoundRegions[0].PhysicalDeltaX * 10
        else:
            # assume mm
            self.resolution = self.dicom.SequenceOfUltrasoundRegions[0].PhysicalDeltaX
    elif self.dicom.get('PixelSpacing'):
        self.resolution = float(self.dicom.PixelSpacing[0])
    else:
        resolution, done = QInputDialog.getText(
            self, "Pixel Spacing", "No pixel spacing info found, please enter pixel spacing (mm)", QLineEdit.Normal, ""
        )
        self.resolution = float(resolution)

    if self.dicom.get('Rows'):
        self.rows = self.dicom.Rows
    else:
        self.rows = self.images.shape[1]

    if self.dicom.get('Manufacturer'):
        self.manufacturer = self.dicom.Manufacturer
    else:
        self.manufacturer = 'Unknown'

    if self.dicom.get('ManufacturerModelName'):
        self.model = self.dicom.ManufacturerModelName
    else:
        self.model = 'Unknown'

    # if pixel data is described by luminance (Y) and chominance (B & R)
    # only occurs when SamplesPerPixel==3
    # if self.dicom.get('PhotometricInterpretation') == 'YBR_FULL_422':
    #    #self.images = np.mean(self.images, 3, dtype=np.uint8)
    #    self.images = np.ascontiguousarray(self.images)[:, :, :, 0]
