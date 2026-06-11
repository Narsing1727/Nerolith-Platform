import argparse
import sys
from loguru import logger
from config import LOG_DIR, N_SCENARIOS, N_JOBS

LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(LOG_DIR / "nerosurrogate.log", level="DEBUG", rotation="10 MB")


def mode_generate(args):
    from dataset_generator.scenario_runner import run_scenarios
    run_scenarios(n=args.n, n_jobs=args.jobs, seed=args.seed)


def mode_train(args):
    from trainer.train import run_training
    run_training(resume=args.resume)


def mode_export(args):
    from export.onnx_exporter  import export_onnx
    from export.onnx_validator  import validate_onnx
    from export.cpp_header_gen  import generate_cpp_header
    path = export_onnx()
    if not validate_onnx(onnx_path=path):
        logger.error("ONNX validation failed")
        sys.exit(1)
    generate_cpp_header()
    logger.info("Export complete")


def mode_infer(args):
    from engine_bridge.grid_io import load_grid
    from inference.surrogate_runner import SurrogateRunner
    runner = SurrogateRunner()
    dem    = load_grid(args.dem)
    flood  = runner.predict(dem, args.rainfall, args.duration,
                            args.dtheta, args.manning_n, args.cell_size)
    logger.info(f"Result: {runner.predict_stats(flood)}")


def main():
    p   = argparse.ArgumentParser(prog="NeroSurrogate")
    sub = p.add_subparsers(dest="mode", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--n",    type=int, default=N_SCENARIOS)
    g.add_argument("--jobs", type=int, default=N_JOBS)
    g.add_argument("--seed", type=int, default=42)

    t = sub.add_parser("train")
    t.add_argument("--resume", action="store_true")

    sub.add_parser("export")

    i = sub.add_parser("infer")
    i.add_argument("--dem",       required=True)
    i.add_argument("--rainfall",  type=float, default=50.0)
    i.add_argument("--duration",  type=float, default=6.0)
    i.add_argument("--dtheta",    type=float, default=0.3)
    i.add_argument("--manning-n", type=float, default=0.035, dest="manning_n")
    i.add_argument("--cell-size", type=float, default=30.0,  dest="cell_size")

    args = p.parse_args()
    {"generate": mode_generate, "train": mode_train,
     "export": mode_export,     "infer": mode_infer}[args.mode](args)


if __name__ == "__main__":
    main()