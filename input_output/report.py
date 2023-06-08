import os

import numpy as np

from input_output.contours import computeContourMetrics


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
        "Frame\tPosition (mm)\tLumen area (mm\N{SUPERSCRIPT TWO})\tPlaque area (mm\N{SUPERSCRIPT TWO})\tVessel area (mm\N{SUPERSCRIPT TWO})\tPlaque burden (%)\tphenotype\n"
    )

    for _, frame in enumerate(frames):
        f.write(
            "{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\n".format(
                frame,
                window.pullbackLength[frame],
                lumen_area[frame],
                plaque_area[frame],
                vessel_area[frame],
                plaque_burden[frame],
                phenotype[frame],
            )
        )
    f.close()

    window.successMessage("Write report")


def computeMetrics(self, masks):
    """Measures lumen area, plaque area and plaque burden"""

    lumen, plaque = 1, 2
    lumen_area = np.sum(masks == lumen, axis=(1, 2)) * self.resolution**2
    plaque_area = np.sum(masks == plaque, axis=(1, 2)) * self.resolution**2
    plaque_burden = (plaque_area / (lumen_area + plaque_area)) * 100

    return (lumen_area, plaque_area, plaque_burden)
