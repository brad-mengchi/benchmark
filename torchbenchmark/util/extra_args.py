import argparse
from typing import List
from torchbenchmark.util.backends.fx2trt import enable_fx2trt
from torchbenchmark.util.backends.fuser import enable_fuser
from torchbenchmark.util.backends.torch_trt import enable_torchtrt
from torchbenchmark.util.framework.vision.args import enable_fp16

# Dispatch arguments based on model type
def parse_args(model: 'torchbenchmark.util.model.BenchmarkModel', extra_args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fx2trt", action='store_true', help="enable fx2trt")
    parser.add_argument("--fuser", type=str, default="", help="enable fuser")
    parser.add_argument("--torch_trt", action='store_true', help="enable torch_tensorrt")
    parser.add_argument("--eval-fp16", action='store_false', help="enable fp16 on torchvision models")
    args = parser.parse_args(extra_args)
    args.device = model.device
    args.jit = model.jit
    args.test = model.test
    args.batch_size = model.batch_size
    args.precision = 'fp32'
    if args.device == "cpu":
        args.fuser = None
    if not (model.device == "cuda" and model.test == "eval"):
        if args.fx2trt or args.torch_trt:
            raise NotImplementedError("TensorRT only works for CUDA inference tests.")
    if hasattr(model, 'TORCHVISION_MODEL') and model.TORCHVISION_MODEL:
        args.cudagraph = False
        args.torchvision = True
        if not (args.test == 'eval' and args.device == 'cuda'):
            args.eval_fp16 = False
    else:
        args.eval_fp16 = False
    if args.eval_fp16:
        args.precision = 'fp16'
    return args

def apply_args(model: 'torchbenchmark.util.model.BenchmarkModel', args: argparse.Namespace):
    if args.eval_fp16:
        assert args.torchvision and args.test == 'eval' and args.device == 'cuda', "Eval fp16 is only available on CUDA for torchvison models."
        model.model, model.example_inputs = enable_fp16(model.model, model.example_inputs)
    if args.fx2trt:
        if args.jit:
            raise NotImplementedError("fx2trt with JIT is not available.")
        module, exmaple_inputs = model.get_module()
        model.set_module(enable_fx2trt(args.batch_size, fp16=(args.precision=='fp16'), model=module, example_inputs=exmaple_inputs))
    if args.fuser:
        enable_fuser(args.fuser)
    if args.torch_trt:
        module, exmaple_inputs = model.get_module()
        model.set_module(enable_torchtrt(precision=args.precision, model=module, example_inputs=exmaple_inputs))

