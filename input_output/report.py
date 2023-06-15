import os

import numpy as np


def report(window):
    """Writes a report file containing lumen area, plaque, area, vessel area, plaque burden, phenotype"""

    if window.segmentation and not window.contours:
        window.errorMessage()
        return

    window.lumen, window.plaque = window.wid.getData()
    lumen_area, plaque_area, plaque_burden = computeContourMetrics(window, window.lumen, window.plaque)
    phenotype = [0] * window.numberOfFrames
    vessel_area = lumen_area + plaque_area

    frames = [frame for frame in range(window.numberOfFrames) if window.lumen[0][frame] and window.plaque[0][frame]]

    f = open(os.path.splitext(window.file_name)[0] + "_report.txt", "w")
    f.write(
        "Frame\tPosition (mm)\tLumen area (mm\N{SUPERSCRIPT TWO})\tPlaque area (mm\N{SUPERSCRIPT TWO})\t"
        "Vessel area (mm\N{SUPERSCRIPT TWO})\tPlaque burden (%)\tPhenotype\tPhase\n"
    )

    for _, frame in enumerate(frames):
        f.write(
            "{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\t{}\n".format(
                frame,
                window.pullbackLength[frame],
                lumen_area[frame],
                plaque_area[frame],
                vessel_area[frame],
                plaque_burden[frame],
                phenotype[frame],
                window.phases[frame]
            )
        )
    f.close()

    window.successMessage("Write report")


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


def contourArea(x, y):
    """Calculate contour/polygon area using Shoelace formula"""

    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    return area
