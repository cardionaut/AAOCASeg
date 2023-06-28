import os
import sys
import hydra
import qdarktheme

from omegaconf import DictConfig
from loguru import logger

from gui.gui import QApplication, Master
from segmentation.unet_segmentation import UNetSegmentation

@hydra.main(version_base=None, config_path='.', config_name='config')
def main(config: DictConfig) -> None:
    if config.train:
        unet = UNetSegmentation(config)
        unet()
    else:
        qdarktheme.enable_hi_dpi()
        app = QApplication(sys.argv)
        qdarktheme.setup_theme('auto')
        Master(config)
        
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
