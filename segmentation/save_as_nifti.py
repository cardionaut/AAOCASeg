import os

import numpy as np
import SimpleITK as sitk
from loguru import logger
from PyQt5.QtWidgets import QProgressDialog, QApplication
from PyQt5.QtCore import Qt
from skimage.draw import polygon2mask

from gui.error_message import ErrorMessage


def save_as_nifti(main_window):
    if not main_window.image_displayed:
        ErrorMessage(main_window, 'Cannot save as NIfTi before reading DICOM file')
        return

    out_path = f'{main_window.config.save.nifti_dir}_{main_window.config.save.save_niftis}_frames'
    if main_window.config.save.save_niftis == 'contoured':
        frames_to_save = [
            frame for frame in range(main_window.metadata['num_frames']) if main_window.data['lumen'][0][frame]
        ]  # find frames with contours (no need to save the others)
    elif main_window.config.save.save_niftis == 'all':
        frames_to_save = range(main_window.metadata['num_frames'])
    else:
        return  # nothing to save

    if frames_to_save:
        file_name = os.path.splitext(os.path.basename(main_window.file_name))[0]  # remove file extension
        os.makedirs(out_path, exist_ok=True)
        mask = contours_to_mask(main_window.images[frames_to_save], frames_to_save, main_window.data['lumen'])

        progress = QProgressDialog()
        progress.setWindowFlags(Qt.Dialog)
        progress.setModal(True)
        progress.setMinimum(0)
        progress_max = len(frames_to_save) * main_window.config.save.save_2d + main_window.config.save.save_3d
        progress.setMaximum(progress_max)
        progress.resize(500, 100)
        progress.setValue(0)
        progress.setValue(1)
        progress.setValue(0)  # trick to make progress bar appear
        progress.setWindowTitle('Saving frames as NIfTi files...')
        progress.show()

        if main_window.config.save.save_2d:
            for i, frame in enumerate(frames_to_save):  # save individual frames as NIfTi
                progress.setValue(i)
                QApplication.processEvents()
                if progress.wasCanceled():
                    break
                if main_window.data['lumen'][0][frame]:  # only save mask if contour exists
                    sitk.WriteImage(
                        sitk.GetImageFromArray(mask[i, :, :]),
                        os.path.join(out_path, f'{file_name}_frame_{i}_seg.nii.gz'),
                    )
                sitk.WriteImage(
                    sitk.GetImageFromArray(main_window.images[frame, :, :]),
                    os.path.join(out_path, f'{file_name}_frame_{i}_img.nii.gz'),
                )
        if main_window.config.save.save_3d:
            if any(main_window.data['lumen'][0]):  # only save mask if any contour exists
                sitk.WriteImage(sitk.GetImageFromArray(mask), os.path.join(out_path, f'{file_name}_seg.nii.gz'))
            sitk.WriteImage(
                sitk.GetImageFromArray(main_window.images), os.path.join(out_path, f'{file_name}_img.nii.gz')
            )
            progress.setValue(len(frames_to_save) * main_window.config.save.save_2d + 1)
            QApplication.processEvents()

        progress.close()


def contours_to_mask(images, contoured_frames, lumen):
    """Convert IVUS contours to numpy mask"""
    image_shape = images.shape[1:3]
    mask = np.zeros_like(images)
    for i, frame in enumerate(contoured_frames):
        try:
            lumen_polygon = [[x, y] for x, y in zip(lumen[1][frame], lumen[0][frame])]
            mask[i, :, :] += polygon2mask(image_shape, lumen_polygon).astype(np.uint8)
        except ValueError:  # frame has no lumen contours
            pass
    mask = np.clip(mask, a_min=0, a_max=1)  # enforce correct value range

    return mask
