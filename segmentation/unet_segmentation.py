import os
import glob
import torch

import matplotlib.pyplot as plt
from tqdm import tqdm
from loguru import logger
from monai.losses import DiceCELoss
from monai.inferers import sliding_window_inference
from monai.transforms import (
    Compose,
    LoadImage,
    RandSpatialCrop,
    ScaleIntensity,
    EnsureType,
    AsDiscrete,
)
from monai.metrics import DiceMetric
from monai.networks.nets import UNETR
from monai.data import (
    DataLoader,
    CacheDataset,
    ArrayDataset,
)


class UNetSegmentation:
    def __init__(self, config) -> None:
        torch.backends.cudnn.benchmark = True
        self.cuda = torch.cuda.is_available()
        self.device = torch.device("cuda" if self.cuda else "cpu")
        self.input_shape = (512, 512)
        self.num_classes = 3  # background, lumen, vessel
        self.root_dir = config.root_dir
        self.init_transforms()

    def __call__(self) -> None:
        imgs = sorted(glob.glob(os.path.join(self.root_dir, "*img.nii.gz")))
        segs = sorted(glob.glob(os.path.join(self.root_dir, "*seg.nii.gz")))
        dataset = ArrayDataset(imgs, self.img_trafos, segs, self.seg_trafos)
        train_loader = DataLoader(dataset, batch_size=1, shuffle=True, num_workers=8, pin_memory=self.cuda)

        self.model = UNETR(
            in_channels=1,
            out_channels=self.num_classes,
            img_size=self.input_shape,
            feature_size=16,
            hidden_size=768,
            mlp_dim=3072,
            num_heads=12,
            pos_embed="conv",
            norm_name="instance",
            res_block=True,
            dropout_rate=0.0,
            spatial_dims=2,
        ).to(self.device)

        self.loss_function = DiceCELoss(to_onehot_y=True, softmax=True)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=1e-5)


    def init_transforms(self) -> None:
        self.img_trafos = Compose(
            [
                LoadImage(image_only=True),
                ScaleIntensity(),
                RandSpatialCrop(self.input_shape, random_size=False),
            ]
        )
        self.seg_trafos = Compose(
            [
                LoadImage(image_only=True),
                RandSpatialCrop(self.input_shape, random_size=False),
            ]
        )

    def validation(self):
        pass

    def train(self):
        pass
