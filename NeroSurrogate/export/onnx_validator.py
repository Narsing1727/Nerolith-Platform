import numpy as np
import torch
import onnxruntime as ort
from loguru import logger
from config import BEST_CKPT_PATH, ONNX_MODEL_PATH, N_CHANNELS, DEVICE
from model.unet import NeroSurrogateUNet
from trainer.checkpoint import load_checkpoint


def validate_onnx(onnx_path=ONNX_MODEL_PATH, ckpt_path=BEST_CKPT_PATH,
                  tolerance=1e-4, input_h=64, input_w=64):
    model = NeroSurrogateUNet()
    load_checkpoint(model, path=ckpt_path, device=DEVICE)
    model.eval()

    dummy = torch.randn(1, N_CHANNELS, input_h, input_w)
    with torch.no_grad():
        pt_out = model(dummy).numpy()

    sess     = ort.InferenceSession(str(onnx_path))
    ort_out  = sess.run(["flood_depth"], {"input": dummy.numpy()})[0]
    max_diff = np.abs(pt_out - ort_out).max()
    passed   = max_diff < tolerance
    logger.info(f"ONNX validation | max_diff={max_diff:.2e} | {'PASS' if passed else 'FAIL'}")
    return passed
