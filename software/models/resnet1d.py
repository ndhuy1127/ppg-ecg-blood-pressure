"""1D ResNet-18 of the PulseDB paper (B5; docs/protocol/b5_pulsedb_definition.md).

Wang et al. 2023 (PulseDB, Front. Digit. Health, doi:10.3389/fdgth.2022.1090854)
built their example model from ResNet-18 (He et al. 2016) by replacing the 2D
convolution, batch normalization and pooling layers with 1D ones, taking ECG and
PPG as two input channels and giving one regression output. The paper gives no
layer table in its text, so the layout here is that of ResNet-18 as published
(torchvision ``resnet18``) with every 2D layer made 1D: stem 7-tap convolution
stride 2 with 64 filters, 3-tap max pool stride 2, four stages of two basic
blocks (64, 128, 256, 512 filters; stride 2 from stage 2), global average pool,
one linear output. The global pool is a mean over time, which equals an
adaptive average pool to length 1 and has a deterministic backward on CUDA.

Requires PyTorch (requirements-dl.txt).
"""

import torch
from torch import nn

STAGES = ((64, 1), (128, 2), (256, 2), (512, 2))
BLOCKS_PER_STAGE = 2


class BasicBlock1d(nn.Module):
    def __init__(self, in_channels, out_channels, stride):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, 3, stride, 1, bias=False)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(out_channels, out_channels, 3, 1, 1, bias=False)
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = None
        if stride != 1 or in_channels != out_channels:
            self.downsample = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, 1, stride, bias=False),
                nn.BatchNorm1d(out_channels))

    def forward(self, x):
        identity = x if self.downsample is None else self.downsample(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return self.relu(out + identity)


class ResNet18_1d(nn.Module):
    """``(batch, in_channels, samples)`` -> ``(batch,)``."""

    def __init__(self, in_channels=2, outputs=1):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(in_channels, 64, 7, 2, 3, bias=False), nn.BatchNorm1d(64),
            nn.ReLU(inplace=True), nn.MaxPool1d(3, 2, 1))
        layers, channels = [], 64
        for width, stride in STAGES:
            for block in range(BLOCKS_PER_STAGE):
                layers.append(BasicBlock1d(channels, width, stride if block == 0 else 1))
                channels = width
        self.layers = nn.Sequential(*layers)
        self.fc = nn.Linear(channels, outputs)
        self.outputs = outputs
        # torchvision ResNet initialisation: He normal (fan_out) for convolutions,
        # batch norm weight 1 and bias 0; the linear layer keeps PyTorch's default.
        for module in self.modules():
            if isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(module.weight, mode="fan_out",
                                        nonlinearity="relu")
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, x):
        x = self.layers(self.stem(x)).mean(dim=-1)
        x = self.fc(x)
        return x.squeeze(-1) if self.outputs == 1 else x


def parameter_count(model) -> int:
    return sum(p.numel() for p in model.parameters())


def set_deterministic(seed):
    """Seeds and deterministic kernels (CUDA needs CUBLAS_WORKSPACE_CONFIG set
    before its first use; the B5 runner sets it before importing torch)."""
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
