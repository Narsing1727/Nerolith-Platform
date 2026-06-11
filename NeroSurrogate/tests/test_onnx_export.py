import pytest
import torch
import numpy as np
from config import N_CHANNELS


def test_export_and_validate(tmp_path):
    try:
        import onnx, onnxruntime as ort
    except ImportError:
        pytest.skip("onnx/onnxruntime not installed")

    from model.unet import NeroSurrogateUNet
    model = NeroSurrogateUNet()
    model.eval()
    dummy = torch.randn(1, N_CHANNELS, 64, 64)
    path  = tmp_path / "test.onnx"

    torch.onnx.export(model, dummy, str(path), opset_version=17,
                      input_names=["input"], output_names=["flood_depth"],
                      dynamic_axes={"input": {0:"batch",2:"height",3:"width"},
                                    "flood_depth": {0:"batch",2:"height",3:"width"}})

    onnx.checker.check_model(onnx.load(str(path)))
    ort_out = ort.InferenceSession(str(path)).run(["flood_depth"], {"input": dummy.numpy()})[0]
    with torch.no_grad():
        pt_out = model(dummy).numpy()
    assert np.abs(pt_out - ort_out).max() < 1e-4
