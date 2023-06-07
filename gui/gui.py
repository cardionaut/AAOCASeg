import time

from loguru import logger
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QApplication,
    QHeaderView,
    QStyle,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QErrorMessage,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from gui.display import Display
from gui.slider import Slider, Communicate
from input_output.read_dicom import readDICOM
from input_output.contours import readContours, writeContours, segment, newSpline
from input_output.report import report
from preprocessing.preprocessing import PreProcessing


class Master(QMainWindow):
    """Main Window Class

    Attributes:
        image: bool, indicates whether images have been loaded (true) or not
        contours: bool, indicates whether contours have been loaded (true) or not
        segmentation: bool, indicates whether segmentation has been performed (true) or not
        lumen: tuple, contours for lumen border
        plaque: tuple, contours for plaque border
    """

    def __init__(self):
        super().__init__()
        self.image = False
        self.contours = False
        self.segmentation = True  # segmentation to do
        self.lumen = ()
        self.plaque = ()
        self.initGUI()

    def initGUI(self):
        self.setGeometry(100, 100, 1200, 1200)
        self.display_size = 800
        self.addToolBar("MY Window")
        self.showMaximized()

        layout = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox2 = QVBoxLayout()
        vbox1hbox1 = QHBoxLayout()

        vbox1.setContentsMargins(0, 0, 100, 100)
        vbox2.setContentsMargins(100, 0, 0, 100)
        vbox2hbox1 = QHBoxLayout()
        vbox2.addLayout(vbox2hbox1)
        layout.addLayout(vbox1)
        layout.addLayout(vbox2)

        dicomButton = QPushButton('Read DICOM')
        contoursButton = QPushButton('Read Contours')
        gatingButton = QPushButton('Extract Diastolic and Systolic Frames')
        segmentButton = QPushButton('Segment')
        splineButton = QPushButton('Manual Contour')
        writeButton = QPushButton('Write Contours')
        reportButton = QPushButton('Write Report')

        dicomButton.setToolTip("Load images in .dcm format")
        contoursButton.setToolTip("Load saved contours in .xml format")
        gatingButton.setToolTip("Extract diastolic and systolic images from pullback")
        segmentButton.setToolTip("Run deep learning based segmentation of lumen and plaque")
        splineButton.setToolTip("Manually draw new contour for lumen, plaque or stent")
        writeButton.setToolTip("Save contours in .xml file")
        reportButton.setToolTip("Write report containing, lumen, plaque and vessel areas and plaque burden")

        hideHeader1 = QHeaderView(Qt.Vertical)
        hideHeader1.hide()
        hideHeader2 = QHeaderView(Qt.Horizontal)
        hideHeader2.hide()
        self.infoTable = QTableWidget()
        self.infoTable.setRowCount(8)
        self.infoTable.setColumnCount(2)
        self.infoTable.setItem(0, 0, QTableWidgetItem('Patient Name'))
        self.infoTable.setItem(1, 0, QTableWidgetItem('Patient DOB'))
        self.infoTable.setItem(2, 0, QTableWidgetItem('Patient Sex'))
        self.infoTable.setItem(3, 0, QTableWidgetItem('Pullback Speed'))
        self.infoTable.setItem(4, 0, QTableWidgetItem('Resolution (mm)'))
        self.infoTable.setItem(5, 0, QTableWidgetItem('Dimensions'))
        self.infoTable.setItem(6, 0, QTableWidgetItem('Manufacturer'))
        self.infoTable.setItem(7, 0, QTableWidgetItem('Model'))
        self.infoTable.setVerticalHeader(hideHeader1)
        self.infoTable.setHorizontalHeader(hideHeader2)
        self.infoTable.horizontalHeader().setStretchLastSection(True)

        dicomButton.clicked.connect(lambda _: readDICOM(self))
        contoursButton.clicked.connect(lambda _: readContours(self))
        segmentButton.clicked.connect(lambda _: segment(self))
        splineButton.clicked.connect(lambda _: newSpline(self))
        gatingButton.clicked.connect(self.gate)
        writeButton.clicked.connect(lambda _: writeContours(self))
        reportButton.clicked.connect(lambda _: report(self))

        self.playButton = QPushButton()
        pixmapi1 = getattr(QStyle, 'SP_MediaPlay')
        pixmapi2 = getattr(QStyle, 'SP_MediaPause')
        self.playIcon = self.style().standardIcon(pixmapi1)
        self.pauseIcon = self.style().standardIcon(pixmapi2)
        self.playButton.setIcon(self.playIcon)
        self.playButton.clicked.connect(self.play)
        self.paused = True

        self.slider = Slider(Qt.Horizontal)
        self.slider.valueChanged[int].connect(self.changeValue)

        self.hideBox = QCheckBox('Hide Contours')
        self.hideBox.setChecked(True)
        self.hideBox.stateChanged[int].connect(self.changeState)
        self.useGatedBox = QCheckBox('Gated Frames')
        self.useGatedBox.stateChanged[int].connect(self.useGated)
        self.useGatedBox.setToolTip(
            "When this is checked only gated frames will be segmented and only gated frames statistics will be written to the report"
        )
        self.useDiastolicBox = QCheckBox('Diastolic Frames')
        self.useDiastolicBox.stateChanged[int].connect(self.useDiastolic)
        self.useDiastolicBox.setToolTip("Check for diastolic frames, uncheck for systolic frames")

        self.wid = Display()
        self.c = Communicate()
        self.c.updateBW[int].connect(self.wid.setFrame)
        self.c.updateBool[bool].connect(self.wid.setDisplay)

        self.text = QLabel()
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setText("Frame {}".format(self.slider.value() + 1))

        vbox1.addWidget(self.wid)
        vbox1hbox1.addWidget(self.playButton)
        vbox1hbox1.addWidget(self.slider)
        vbox1.addLayout(vbox1hbox1)
        vbox1.addWidget(self.text)

        vbox2.addWidget(self.hideBox)
        vbox2.addWidget(self.useGatedBox)
        vbox2.addWidget(self.useDiastolicBox)
        vbox2.addWidget(dicomButton)
        vbox2.addWidget(contoursButton)
        vbox2.addWidget(gatingButton)
        vbox2.addWidget(segmentButton)
        vbox2.addWidget(splineButton)
        vbox2.addWidget(writeButton)
        vbox2.addWidget(reportButton)
        vbox2hbox1.addWidget(self.infoTable)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setWindowIcon(QIcon('Media/thumbnail.png'))
        self.setWindowTitle('DeepIVUS')
        self.setCentralWidget(centralWidget)
        self.show()
        # disclaimer = QMessageBox.about(
        #     self, 'DeepIVUS', 'DeepIVUS is not FDA approved and should not be used for medical decisions.'
        # )

        # pipe = subprocess.Popen(["rm","-r","some.file"])
        # pipe.communicate() # block until process completes.
        timer = QTimer(self)
        timer.timeout.connect(self.autoSave)
        timer.start(1000000)  # autosave interval in milliseconds

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Q:
            self.close()
        elif key == Qt.Key_H:
            if not self.hideBox.isChecked():
                self.hideBox.setChecked(True)
            elif self.hideBox.isChecked():
                self.hideBox.setChecked(False)
            self.hideBox.setChecked(self.hideBox.isChecked())
        elif key == Qt.Key_J:
            currentFrame = self.slider.value()
            self.slider.setValue(currentFrame + 1)
            QApplication.processEvents()
            time.sleep(0.1)
            self.slider.setValue(currentFrame)
            QApplication.processEvents()
            time.sleep(0.1)
            self.slider.setValue(currentFrame - 1)
            QApplication.processEvents()
            time.sleep(0.1)
            self.slider.setValue(currentFrame)
            QApplication.processEvents()
        elif key == Qt.Key_W:
            self.slider.next_gated_frame()
        elif key == Qt.Key_S:
            self.slider.last_gated_frame()
        elif key == Qt.Key_D:
            self.slider.setValue(self.slider.value() + 1)
        elif key == Qt.Key_A:
            self.slider.setValue(self.slider.value() - 1)
        elif key == Qt.Key_E:
            if self.image:
                self.wid.new(self, 2)  # start new manual Lumen contour
                self.hideBox.setChecked(False)
                self.contours = True
        elif key == Qt.Key_R:
            if self.image:
                self.wid.new(self, 1)  # start new manual Vessel contour
                self.hideBox.setChecked(False)
                self.contours = True
        elif key == Qt.Key_T:
            if self.image:
                self.wid.new(self, 0)  # start new manual Stent contour
                self.hideBox.setChecked(False)
                self.contours = True

    def play(self):
        "Plays all frames until end of pullback starting from currently selected frame" ""
        start_frame = self.slider.value()

        if self.paused:
            self.paused = False
            self.playButton.setIcon(self.pauseIcon)
        else:
            self.paused = True
            self.playButton.setIcon(self.playIcon)

        for frame in range(start_frame, self.numberOfFrames):
            if not self.paused:
                self.slider.setValue(frame)
                QApplication.processEvents()
                time.sleep(0.05)
                self.text.setText("Frame {}".format(frame + 1))

        self.playButton.setIcon(self.playIcon)

    def gate(self):
        """Extract end diastolic frames and stores in new variable"""
        try:
            preprocessor = PreProcessing(self.images, self.dicom.CineRate, self.ivusPullbackRate)
            self.gated_frames_dia, self.gated_frames_sys, self.distance_frames = preprocessor()
            self.gated_frames = self.gated_frames_dia  # diastolic frames by default
        except AttributeError:  # self.images not defined because no file was read first
            warning = QErrorMessage()
            warning.setWindowModality(Qt.WindowModal)
            warning.showMessage("Please first select a DICOM file to be read")
            warning.exec_()
            return
        
        if self.gated_frames is not None:
            self.slider.addGatedFrames(self.gated_frames)
            self.useGatedBox.setChecked(True)
            self.useDiastolicBox.setChecked(True)
            self.successMessage("Diastolic/Systolic frame (change with up and down arrows) extraction")
        else:
            warning = QErrorMessage()
            warning.setWindowModality(Qt.WindowModal)
            warning.showMessage("Diastolic/Systolic frame extraction was unsuccessful")
            warning.exec_()

    def autoSave(self):
        """Automatically saves contours to a temporary file every 180 seconds"""

        if self.contours:
            logger.info("Automatically saving current contours")
            writeContours(self)

    def changeValue(self, value):
        self.c.updateBW.emit(value)
        self.wid.run()
        self.text.setText("Frame {}".format(value + 1))

    def changeState(self, value):
        self.c.updateBool.emit(value)
        self.wid.run()

    def useGated(self, value):
        self.gated = value

    def useDiastolic(self, value):
        if value:
            self.gated_frames = self.gated_frames_dia
        else:
            self.gated_frames = self.gated_frames_sys

        self.slider.addGatedFrames(self.gated_frames)
        self.useGatedBox.setChecked(True)

    def errorMessage(self):
        """Helper function for errors"""

        warning = QMessageBox()
        warning.setWindowModality(Qt.WindowModal)
        warning.setWindowTitle("Error")
        warning.setText("Segmentation must be performed first")
        warning.exec_()

    def successMessage(self, task):
        """Helper function for success messages"""

        success = QMessageBox()
        success.setWindowModality(Qt.WindowModal)
        success.setWindowTitle("Status")
        success.setText(task + " has been successfully completed")
        success.exec_()
