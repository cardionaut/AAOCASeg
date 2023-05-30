import numpy as np


def report(self):
    """Writes a report file containing lumen area, plaque, area, vessel area, plaque burden, phenotype"""

    if self.segmentation and not self.contours:
        self.errorMessage()
    else:
        self.lumen, self.plaque = self.wid.getData()
        lumen_area, plaque_area, plaque_burden = self.computeContourMetrics(self.lumen, self.plaque)
        phenotype = [0] * self.numberOfFrames
        patientName = self.infoTable.item(0, 1).text()
        vessel_area = lumen_area + plaque_area

        if self.useGatedBox.isChecked():
            frames = self.gatedFrames
        else:
            frames = list(range(self.numberOfFrames))

        f = open(patientName + "_report.txt", "w")
        f.write(
            "Frame\tPosition (mm)\tLumen area (mm\N{SUPERSCRIPT TWO})\tPlaque area (mm\N{SUPERSCRIPT TWO})\tVessel area (mm\N{SUPERSCRIPT TWO})\tPlaque burden (%)\tphenotype\n"
        )

        for _, frame in enumerate(frames):
            f.write(
                "{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\n".format(
                    frame,
                    self.pullbackLength[frame],
                    lumen_area[frame],
                    plaque_area[frame],
                    vessel_area[frame],
                    plaque_burden[frame],
                    phenotype[frame],
                )
            )
        f.close()

        self.successMessage("Write report")


def computeMetrics(self, masks):
    """Measures lumen area, plaque area and plaque burden"""

    lumen, plaque = 1, 2
    lumen_area = np.sum(masks == lumen, axis=(1, 2)) * self.resolution**2
    plaque_area = np.sum(masks == plaque, axis=(1, 2)) * self.resolution**2
    plaque_burden = (plaque_area / (lumen_area + plaque_area)) * 100

    return (lumen_area, plaque_area, plaque_burden)
