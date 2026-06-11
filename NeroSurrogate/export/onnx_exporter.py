import torch
import onnx
from loguru import logger
from config import BEST_CKPT_PATH, ONNX_MODEL_PATH, N_CHANNELS, DEVICE
from model.unet import NeroSurrogateUNet
from trainer.checkpoint import load_checkpoint


def export_onnx(ckpt_path=BEST_CKPT_PATH, output_path=ONNX_MODEL_PATH,
                input_h=64, input_w=64):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = NeroSurrogateUNet()
    load_checkpoint(model, path=ckpt_path, device=DEVICE)
    model.eval().to("cpu")

    dummy = torch.randn(1, N_CHANNELS, input_h, input_w)
    torch.onnx.export(
        model, dummy, str(output_path),
        export_params=True, opset_version=17, do_constant_folding=True,
        input_names=["input"], output_names=["flood_depth"],
        dynamic_axes={"input": {0: "batch", 2: "height", 3: "width"},
                      "flood_depth": {0: "batch", 2: "height", 3: "width"}},
    )
    onnx.checker.check_model(onnx.load(str(output_path)))
    logger.info(f"ONNX export → {output_path} ({output_path.stat().st_size/1e6:.1f} MB)")
    return output_path
