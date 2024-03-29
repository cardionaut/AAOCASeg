## Table of contents <!-- omit in toc -->

- [Installation](#installation)
- [Functionalities](#functionalities)
- [Configuration](#configuration)
- [Usage](#usage)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Acknowledgements](#acknowledgements)


## Installation
```
    python3 -m venv env
    source env/bin/activate
    pip install poetry
    poetry install
```

If you plan on using GPU acceleration for model training and inference, make sure to install the required tools (NVIDIA toolkit, etc.) and the corresponding version of Tensorflow.

## Functionalities
This application is designed for IVUS images in DICOM format and offers the following functionalities:
- Inspect IVUS images frame-by-frame and display DICOM metadata
- Manually **draw lumen contours** with automatic calculation of lumen area, circumference and elliptic ratio
- **Automatic segmentation** of lumen for all frames (work in progress)
- Manually tag diastolic/systolic frames and frames with plaque
- **Auto-save** of contours and tags enabled by default with user-definable interval
- Generation of report file containing detailed metrics for each frame
- Ability to save images and segmentations as **NIfTi files**, e.g. to train a machine learning model
- (unfinished) Automatically extract diastolic/systolic frames

## Configuration
Make sure to quickly check the **config.yaml** file and configure everything to your needs.

## Usage
After the config file is set up properly, you can run the application using:
```
python3 main.py
```
This will open a graphical user interface (GUI) in which you have access to the above-mentioned functionalities.
## Keyboard shortcuts
For ease-of-use, this application contains several keyboard shortcuts.\
In the current state, these cannot be changed by the user (at least not without changing the source code).
- Use the <kbd>A</kbd> and <kbd>D</kbd> keys to move through the IVUS images frame-by-frame
- If gated (diastolic/systolic) frames are available, you can move through those using <kbd>S</kbd> and <kbd>W</kbd>\
  Make sure to select which gated frames you want to traverse using the corresponding button (blue for diastolic, red for systolic)
- Press <kbd>E</kbd> to manually draw a new lumen contour
- Hold the right mouse button <kbd>RMB</kbd> for windowing (can be reset by pressing <kbd>R</kbd>)
- Press <kbd>C</kbd> to toggle color mode
- Press <kbd>H</kbd> to hide all contours
- Press <kbd>J</kbd> to jiggle around the current frame
- Press <kbd>Q</kbd> to close the program

## Acknowledgements
The starting point of this project was the [DeepIVUS](https://github.com/dmolony3/DeepIVUS) public repository by [David](https://github.com/dmolony3) (cloned on May 22, 2023).
