import os
import hydra

import numpy as np
from omegaconf import DictConfig
from loguru import logger

from preprocessing.preprocessing import PreProcessing
from filters.nonlocal_means import NonLocalMeansFilter
from gui.compare_stacks import CompareStacks


@hydra.main(version_base=None, config_path='.', config_name='config')
def main(config: DictConfig) -> None:
    preprocessor = PreProcessing(config)
    dia, sys, distance_frames = preprocessor()
    nonlocal_means = NonLocalMeansFilter(config)
    dia_nonlocal_means = nonlocal_means(dia)

    app = QApplication(sys.argv)
    ex = Master()
    
    CompareStacks()(dia, dia_nonlocal_means)

    if config.filters.plot:
        pass
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
