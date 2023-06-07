import os
import sys
import hydra

import numpy as np
from omegaconf import DictConfig
from loguru import logger

from preprocessing.preprocessing import PreProcessing
from filters.nonlocal_means import NonLocalMeansFilter
from gui.compare_stacks import CompareStacks
from gui.gui import QApplication, Master


@hydra.main(version_base=None, config_path='.', config_name='config')
def main(config: DictConfig) -> None:
    app = QApplication(sys.argv)
    ex = Master()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
