import math

import numpy as np
from loguru import logger
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from gui.geometry import Point, Spline


class Display(QGraphicsView):
    """Displays images and contours.

    Displays images and contours as well as allowing user to
    interact and manipulate contours.

    Attributes:
        scene: QGraphicsScene, all items
        frame: int, current frame
        lumen: tuple, lumen contours
        plaque: tuple: plaque contours
        hide: bool, indicates whether contours should be displayed or hidden
        activePoint: Point, active point in spline
        innerPoint: list, spline points for inner (lumen) contours
        outerPoint: list, spline points for outer (plaque) contours
    """

    def __init__(self):
        super(Display, self).__init__()
        print("View Height: {}, View Width: {}".format(self.width(), self.height()))

        scene = QGraphicsScene(self)

        self.scene = scene
        self.pointIdx = None
        self.frame = 0
        self.lumen = ([], [])
        self.plaque = ([], [])
        self.stent = ([], [])
        self.hide = True
        self.draw = False
        self.drawPoints = []
        self.edit_selection = None
        self.splineDrawn = False
        self.newSpline = None
        self.enable_drag = True
        self.activePoint = None
        self.innerPoint = []
        self.outerPoint = []
        self.display_size = 800

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.image = QGraphicsPixmapItem(QPixmap(self.display_size, self.display_size))
        self.scene.addItem(self.image)
        self.setScene(self.scene)

    def findItem(self, item, eventPos):
        """Sets the active point for interaction"""

        min_dist = 10

        pos = item.mapFromScene(self.mapToScene(eventPos))

        dist = item.select_point(pos)

        if dist < min_dist:
            item.updateColor()
            self.enable_drag = True
            self.activePoint = item
        else:
            self.activePoint = None
            print("No active point")

    def mousePressEvent(self, event):
        super(Display, self).mousePressEvent(event)

        # if event.button() == Qt.RightButton and self.drawPoints:
        #     self.drawPoints.pop()
        
        if self.draw: 
            pos = self.mapToScene(event.pos())
            self.addManualSpline(pos)
        else:
            # identify which point has been clicked
            items = self.items(event.pos())
            for item in items:
                if item in self.innerPoint:
                    # Convert mouse position to item position https://stackoverflow.com/questions/53627056/how-to-get-cursor-click-position-in-qgraphicsitem-coordinate-system
                    self.pointIdx = [i for i, checkItem in enumerate(self.innerPoint) if item == checkItem][0]
                    # print(self.pointIdx, 'Item found')
                    self.activeContour = 1
                    self.findItem(item, event.pos())
                elif item in self.outerPoint:
                    self.pointIdx = [i for i, checkItem in enumerate(self.outerPoint) if item == checkItem][0]
                    self.activeContour = 2
                    self.findItem(item, event.pos())

    def mouseReleaseEvent(self, event):
        if self.pointIdx is not None:
            contour_scaling_factor = self.display_size / self.imsize[1]
            item = self.activePoint
            item.resetColor()

            if self.activeContour == 1:
                self.lumen[0][self.frame] = [val / contour_scaling_factor for val in self.innerSpline.knotPoints[0]]
                self.lumen[1][self.frame] = [val / contour_scaling_factor for val in self.innerSpline.knotPoints[1]]
            elif self.activeContour == 2:
                self.plaque[0][self.frame] = [val / contour_scaling_factor for val in self.outerSpline.knotPoints[0]]
                self.plaque[1][self.frame] = [val / contour_scaling_factor for val in self.outerSpline.knotPoints[1]]

    def mouseMoveEvent(self, event):
        # self.setMouseTracking(True) # if this is disabled mouse tracking only occurs when a button is pressed
        if self.pointIdx is not None:
            item = self.activePoint
            pos = item.mapFromScene(self.mapToScene(event.pos()))
            newPos = item.update(pos)
            # update the spline
            if self.activeContour == 1:
                self.innerSpline.update(newPos, self.pointIdx)
            elif self.activeContour == 2:
                self.outerSpline.update(newPos, self.pointIdx)
            # self.disable_drag = False

    def setData(self, lumen, plaque, stent, images):
        self.numberOfFrames = images.shape[0]
        # lumen, plaque = self.resizeContours(lumen, plaque, scale)
        self.lumen = self.downsample(lumen)
        self.plaque = self.downsample(plaque)
        self.stent = self.downsample(stent)
        self.images = images
        self.imsize = self.images.shape
        self.displayImage()

    def resizeContours(self, lumen, plaque, scale):
        """If image is not 500x500 resize the contours for appropriate display"""
        print('Scaling images by {} for display'.format(scale))
        lumen = self.resize(lumen, scale)
        plaque = self.resize(plaque, scale)
        return lumen, plaque

    def resize(self, contours, scale):
        for idx in range(len(contours[0])):
            if contours[0][idx]:
                contours[0][idx] = [int(val * scale) for val in contours[0][idx]]
        for idx in range(len(contours[1])):
            if contours[0][idx]:
                contours[1][idx] = [int(val * scale) for val in contours[1][idx]]
        return (contours[0], contours[1])

    def getData(self):
        """Gets the interpolated image contours

        Returns:
            lumenContour: list, first and second lists are lists of x and y points
            plaqueContour: list, first and second lists are lists of x and y points
        """

        lumenContour = [[], []]
        plaqueContour = [[], []]

        for frame in range(self.numberOfFrames):
            if self.lumen[0][frame]:
                lumen = Spline([self.lumen[0][frame], self.lumen[1][frame]], 'r')
                lumenContour[0].append(list(lumen.points[0]))
                lumenContour[1].append(list(lumen.points[1]))
            else:
                lumenContour[0].append([])
                lumenContour[1].append([])
            if self.plaque[0][frame]:
                plaque = Spline([self.plaque[0][frame], self.plaque[1][frame]], 'y')
                plaqueContour[0].append(list(plaque.points[0]))
                plaqueContour[1].append(list(plaque.points[1]))
            else:
                plaqueContour[0].append([])
                plaqueContour[1].append([])

        return lumenContour, plaqueContour

    def downsample(self, contours, num_points=20):
        """Downsamples input contour data by selecting n points from original contour"""

        numberOfFrames = len(contours[0])

        downsampled = [[] for idx in range(numberOfFrames)], [[] for idx in range(numberOfFrames)]

        for i in range(numberOfFrames):
            if contours[0][i]:
                idx = len(contours[0][i]) // num_points
                downsampled[0][i] = [pnt for j, pnt in enumerate(contours[0][i]) if j % idx == 0]
                downsampled[1][i] = [pnt for j, pnt in enumerate(contours[1][i]) if j % idx == 0]

        return downsampled

    def displayImage(self):
        """Clears scene and displays current image and splines"""

        self.scene.clear()
        self.viewport().update()

        [self.removeItem(item) for item in self.scene.items()]

        self.activePoint = None
        self.pointIdx = None

        if len(self.images.shape) == 3:
            self.image = QImage(
                self.images[self.frame, :, :], self.imsize[1], self.imsize[2], QImage.Format_Grayscale8
            ).scaled(self.display_size, self.display_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        else:
            bytesPerLine = 3 * self.imsize[2]
            current_image = self.images[self.frame, :, :, :].astype(np.uint8, order='C', casting='unsafe')
            self.image = QImage(
                current_image.data, self.imsize[1], self.imsize[2], bytesPerLine, QImage.Format_RGB888
            ).scaled(self.display_size, self.display_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        image = QPixmap.fromImage(self.image)

        self.image = QGraphicsPixmapItem(image)
        self.scene.addItem(self.image)

        if not self.hide:
            if self.lumen[0] or self.plaque[0] or self.stent[0]:
                self.addInteractiveSplines(self.lumen, self.plaque, self.stent)

        self.setScene(self.scene)

    def addInteractiveSplines(self, lumen, plaque, stent):
        """Adds inner and outer splines to scene"""

        contour_scaling_factor = self.display_size / self.imsize[1]
        if lumen[0][self.frame]:
            lumen_x = [val * contour_scaling_factor for val in lumen[0][self.frame]]
            lumen_y = [val * contour_scaling_factor for val in lumen[1][self.frame]]
            self.innerSpline = Spline([lumen_x, lumen_y], 'r')
            self.innerPoint = [
                Point((self.innerSpline.knotPoints[0][idx], self.innerSpline.knotPoints[1][idx]), 'r')
                for idx in range(len(self.innerSpline.knotPoints[0]) - 1)
            ]
            [self.scene.addItem(point) for point in self.innerPoint]
            self.scene.addItem(self.innerSpline)

        if plaque[0][self.frame]:
            plaque_x = [val * contour_scaling_factor for val in plaque[0][self.frame]]
            plaque_y = [val * contour_scaling_factor for val in plaque[1][self.frame]]
            self.outerSpline = Spline([plaque_x, plaque_y], 'y')
            self.outerPoint = [
                Point((self.outerSpline.knotPoints[0][idx], self.outerSpline.knotPoints[1][idx]), 'y')
                for idx in range(len(self.outerSpline.knotPoints[0]) - 1)
            ]  # IMPORTANT TO NOT INCLUDE LAST COPIED KNOT POINT DUE TO PERIODICITY
            [self.scene.addItem(point) for point in self.outerPoint]
            self.scene.addItem(self.outerSpline)

    def addManualSpline(self, point):
        """Creates an interactive spline manually point by point"""

        if not self.drawPoints:
            self.splineDrawn = False

        self.drawPoints.append(Point((point.x(), point.y()), 'b'))
        self.scene.addItem(self.drawPoints[-1])

        if len(self.drawPoints) > 3:
            if not self.splineDrawn:
                self.newSpline = Spline(
                    [
                        [point.getPoint()[0] for point in self.drawPoints],
                        [point.getPoint()[1] for point in self.drawPoints],
                    ],
                    'c',
                )
                self.scene.addItem(self.newSpline)
                self.splineDrawn = True
            else:
                self.newSpline.update(point, len(self.drawPoints))

        if len(self.drawPoints) > 1:
            dist = math.sqrt(
                (point.x() - self.drawPoints[0].getPoint()[0]) ** 2
                + (point.y() - self.drawPoints[0].getPoint()[1]) ** 2
            )

            if dist < 10:
                self.draw = False
                self.drawPoints = []
                if self.newSpline is not None:
                    downsampled = self.downsample(
                        ([self.newSpline.points[0].tolist()], [self.newSpline.points[1].tolist()])
                    )
                    scaling_factor = self.display_size / self.imsize[1]
                    if self.edit_selection == 0:
                        self.stent[0][self.frame] = [val / scaling_factor for val in downsampled[0][0]]
                        self.stent[1][self.frame] = [val / scaling_factor for val in downsampled[1][0]]
                    elif self.edit_selection == 1:
                        self.plaque[0][self.frame] = [val / scaling_factor for val in downsampled[0][0]]
                        self.plaque[1][self.frame] = [val / scaling_factor for val in downsampled[1][0]]
                    elif self.edit_selection == 2:
                        self.lumen[0][self.frame] = [val / scaling_factor for val in downsampled[0][0]]
                        self.lumen[1][self.frame] = [val / scaling_factor for val in downsampled[1][0]]

                self.win.setCursor(Qt.ArrowCursor)
                self.displayImage()

    def run(self):
        self.displayImage()

    def new(self, window, edit_selection):
        self.win = window
        self.win.setCursor(Qt.CrossCursor)

        self.draw = True
        self.edit_selection = edit_selection

        if self.edit_selection == 0:
            self.stent[0][self.frame] = []
            self.stent[1][self.frame] = []
        elif self.edit_selection == 1:
            self.plaque[0][self.frame] = []
            self.plaque[1][self.frame] = []
        elif self.edit_selection == 2:
            self.lumen[0][self.frame] = []
            self.lumen[1][self.frame] = []
        else:
            return

        self.displayImage()

    def setFrame(self, value):
        self.frame = value

    def setDisplay(self, hide):
        self.hide = hide
