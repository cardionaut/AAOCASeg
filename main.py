import os
import sys
import hydra
import qdarktheme

import numpy as np
from omegaconf import DictConfig
from loguru import logger

from preprocessing.preprocessing import PreProcessing
from filters.nonlocal_means import NonLocalMeansFilter
from gui.compare_stacks import CompareStacks
from gui.gui import QApplication, Master


@hydra.main(version_base=None, config_path='.', config_name='config')
def main(config: DictConfig) -> None:
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    qdarktheme.setup_theme('auto')
    ex = Master()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
