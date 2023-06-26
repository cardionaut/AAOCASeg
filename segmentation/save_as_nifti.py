import os

from loguru import logger
from monailabel.transform.writer import write_nifti
from PyQt5.QtWidgets import QErrorMessage
from PyQt5.QtCore import Qt

from input_output.contours import contoursToMask


def save_as_nifti(window):
    if not window.image:
        warning = QErrorMessage(window)
        warning.setWindowModality(Qt.WindowModal)
        warning.showMessage('Cannot save as NIfTI before reading DICOM file')
        warning.exec_()
        return

    contoured_frames = [
        frame for frame in range(window.numberOfFrames) if window.lumen[0][frame] or window.plaque[0][frame]
    ]  # find frames with contours (no need to save the others)

    if contoured_frames:
        out_path = os.path.splitext(window.file_name)[0]  # remove file extension
        mask = contoursToMask(window.images[contoured_frames], window.lumen, window.plaque)
        for i, frame in enumerate(contoured_frames):  # save individual frames as NIfTI
            write_nifti(mask[i, :, :], filename=f'{out_path}_frame_{i}_seg.nii.gz')
            write_nifti(window.images[frame, :, :], filename=f'{out_path}_frame_{i}_img.nii.gz')

        # save entire stack as NIfTI
        write_nifti(mask, filename=f'{out_path}_seg.nii.gz')
        write_nifti(window.images[contoured_frames, :, :], filename=f'{out_path}_img.nii.gz')
 