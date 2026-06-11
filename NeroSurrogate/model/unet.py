import torch
import torch.nn as nn
import torch.nn.functional as F
from config import N_CHANNELS, UNET_BASE_FILTERS, UNET_DEPTH, DROPOUT


class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Dropout2d(DROPOUT),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    def forward(self, x): return self.block(x)


class EncoderBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = ConvBlock(in_ch, out_ch)
        self.pool = nn.MaxPool2d(2)
    def forward(self, x):
        skip = self.conv(x)
        return self.pool(skip), skip


class DecoderBlock(nn.Module):
    def __init__(self, in_ch, skip_ch, out_ch):
        super().__init__()
        self.up   = nn.ConvTranspose2d(in_ch, out_ch, 2, stride=2)
        self.conv = ConvBlock(out_ch + skip_ch, out_ch)
    def forward(self, x, skip):
        x = self.up(x)
        if x.shape != skip.shape:
            x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        return self.conv(torch.cat([x, skip], dim=1))


class NeroSurrogateUNet(nn.Module):
    def __init__(self, in_channels=N_CHANNELS, base_filters=UNET_BASE_FILTERS, depth=UNET_DEPTH):
        super().__init__()
        self.encoders = nn.ModuleList()
        enc_channels  = []
        ch = in_channels
        for i in range(depth):
            out_ch = base_filters * (2 ** i)
            self.encoders.append(EncoderBlock(ch, out_ch))
            enc_channels.append(out_ch)
            ch = out_ch

        self.bottleneck = ConvBlock(ch, base_filters * (2 ** depth))
        ch = base_filters * (2 ** depth)

        self.decoders = nn.ModuleList()
        for i in reversed(range(depth)):
            out_ch = base_filters * (2 ** i)
            self.decoders.append(DecoderBlock(ch, enc_channels[i], out_ch))
            ch = out_ch

        self.head = nn.Sequential(nn.Conv2d(ch, 1, 1), nn.ReLU())

    def forward(self, x):
        skips = []
        for enc in self.encoders:
            x, skip = enc(x)
            skips.append(skip)
        x = self.bottleneck(x)
        for dec, skip in zip(self.decoders, reversed(skips)):
            x = dec(x, skip)
        return self.head(x)

    def count_params(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
