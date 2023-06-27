import os
import glob
import torch

import matplotlib.pyplot as plt
import pytorch_lightning as pl
from tqdm import tqdm
from datetime import datetime
from loguru import logger
from torch.utils.data import random_split
from monai.losses import DiceCELoss
from monai.inferers import sliding_window_inference
from monai.transforms import (
    Compose,
    LoadImage,
    EnsureChannelFirst,
    RandSpatialCrop,
    ScaleIntensity,
    EnsureType,
    AsDiscrete,
)
from monai.metrics import DiceMetric
from monai.networks.nets import UNet
from monai.data import (
    DataLoader,
    CacheDataset,
    ArrayDataset,
)

from segmentation.model import Model


class UNetSegmentation:
    def __init__(self, config) -> None:
        torch.backends.cudnn.benchmark = True
        # self.cuda = torch.cuda.is_available()
        self.cuda = False
        self.device = torch.device("cuda" if self.cuda else "cpu")
        self.input_shape = (512, 512)
        self.num_classes = 1  # background, lumen, vessel

        self.root_dir = config.root_dir
        self.batch_size = config.segmentation.batch_size
        self.num_workers = config.segmentation.num_workers
        self.dropout_rate = config.segmentation.dropout_rate
        self.learning_rate = config.segmentation.learning_rate
        self.weight_decay = config.segmentation.weight_decay
        self.max_epochs = config.segmentation.max_epochs
        self.train_val_ratio = config.segmentation.train_val_ratio

        self.init_transforms()

    def __call__(self) -> None:
        imgs = sorted(glob.glob(os.path.join(self.root_dir, "*frame_*_img.nii.gz")))
        segs = sorted(glob.glob(os.path.join(self.root_dir, "*frame_*_seg.nii.gz")))
        dataset = ArrayDataset(imgs, self.img_trafos, segs, self.seg_trafos)
        n_train = int(round(self.train_val_ratio * len(imgs)))
        splits = n_train, len(imgs) - n_train
        train_dataset, val_dataset = random_split(dataset, splits)
        train_loader = DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=self.num_workers, pin_memory=self.cuda
        )
        val_loader = DataLoader(
            val_dataset, batch_size=64, shuffle=False, num_workers=self.num_workers, pin_memory=self.cuda
        )
        net = UNet(
            spatial_dims=2,
            in_channels=1,
            out_channels=self.num_classes,
            channels=(4, 8, 16),
            strides=(2, 2),
            dropout=self.dropout_rate,
        )
        loss_function = DiceCELoss(softmax=True)
        optimizer = torch.optim.AdamW
        model = Model(net, loss_function, self.learning_rate, optimizer)
        early_stopping = pl.callbacks.early_stopping.EarlyStopping(monitor='val_loss')
        accelerator = 'gpu' if self.cuda else 'cpu'
        trainer = pl.Trainer(
            callbacks=[early_stopping], accelerator=accelerator, max_epochs=self.max_epochs, log_every_n_steps=2
        )

        start = datetime.now()
        logger.info(f'Training started at {start}')
        trainer.fit(model=model, train_dataloaders=train_loader, val_dataloaders=val_loader)
        logger.info(f'Training duration: {datetime.now() - start}')

    def init_transforms(self) -> None:
        self.img_trafos = Compose(
            [
                LoadImage(image_only=True),
                EnsureChannelFirst(),
                ScaleIntensity(),
                # RandSpatialCrop(self.input_shape, random_size=False),
            ]
        )
        self.seg_trafos = Compose(
            [
                LoadImage(image_only=True),
                EnsureChannelFirst(),
                # AsDiscrete(to_onehot=self.num_classes)
                # RandSpatialCrop(self.input_shape, random_size=False),
            ]
        )
