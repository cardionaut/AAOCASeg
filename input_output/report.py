import os

import numpy as np
from loguru import logger
from PyQt5.QtWidgets import QErrorMessage
from PyQt5.QtCore import Qt


def report(window):
    """Writes a report file containing lumen area, plaque, area, vessel area, plaque burden, phenotype"""

    if not window.image:
        warning = QErrorMessage(window)
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Cannot write report before reading DICOM file')
        warning.exec_()
        return

    if window.segmentation and not window.contours:
        window.errorMessage()
        return

    window.lumen, window.plaque = window.wid.getData()
    contoured_frames = [
        frame for frame in range(window.numberOfFrames) if window.lumen[0][frame] or window.plaque[0][frame]
    ]
    lumen_area, plaque_area, plaque_burden = computeContourMetrics(window, contoured_frames)
    phenotype = [0] * len(contoured_frames)
    vessel_area = lumen_area + plaque_area

    f = open(os.path.splitext(window.file_name)[0] + "_report.txt", "w")
    f.write(
        "Frame\tPosition (mm)\tLumen area (mm\N{SUPERSCRIPT TWO})\tPlaque area (mm\N{SUPERSCRIPT TWO})\t"
        "Vessel area (mm\N{SUPERSCRIPT TWO})\tPlaque burden (%)\tPhenotype\tPhase\n"
    )

    for index, frame in enumerate(contoured_frames):
        f.write(
            "{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\t{}\n".format(
                frame,
                window.pullbackLength[frame],
                lumen_area[index],
                plaque_area[index],
                vessel_area[index],
                plaque_burden[index],
                phenotype[index],
                window.phases[frame],
            )
        )
    f.close()

    window.successMessage("Write report")


def computeContourMetrics(window, contoured_frames):
    """Computes lumen area, plaque area and plaque burden from contours"""

    lumen_area = np.zeros(len(contoured_frames))
    plaque_area = np.zeros_like(lumen_area)
    plaque_burden = np.zeros_like(lumen_area)
    for index, frame in enumerate(contoured_frames):
        if window.lumen[0][frame]:
            lumen_area[index] = contourArea(window.lumen[0][frame], window.lumen[1][frame]) * window.resolution**2
            if window.plaque[0][frame]:
                plaque_area[index] = (
                    contourArea(window.plaque[0][frame], window.plaque[1][frame]) * window.resolution**2
                    - lumen_area[index]
                )
                plaque_burden[index] = (plaque_area[index] / (lumen_area[index] + plaque_area[index])) * 100

    return (lumen_area, plaque_area, plaque_burden)


def contourArea(x, y):
    """Calculate contour/polygon area using Shoelace formula"""

    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    return area
