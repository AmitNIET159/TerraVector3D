"""Command-line interface for BhuDrishti Geospatial AI.

Usage
-----
    python -m src.cli <command> [options]

Commands: normalize, analyze-floor-plan, detect-floors, confidence,
          generate-synthetic-pointcloud, run-all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    print(f"  -> saved {path}")


# -- subcommand handlers ----------------------------------------------------

def cmd_normalize(args: argparse.Namespace) -> dict:
    from .geojson_normalizer import normalize_geojson
    result = normalize_geojson(args.parcel)
    _save_json(result, Path(args.output))
    return result


def cmd_analyze_floor_plan(args: argparse.Namespace) -> dict:
    from .floor_plan_analyzer import analyze_floor_plan
    mpp = args.metres_per_pixel
    result = analyze_floor_plan(args.image, metres_per_pixel=mpp)
    _save_json(result, Path(args.output))
    return result


def cmd_detect_floors(args: argparse.Namespace) -> dict:
    from .pointcloud_floor_detector import detect_floor_levels
    ply = args.ply
    if ply is None or not Path(ply).exists():
        print("  No PLY provided — generating synthetic point cloud ...")
        from .synthetic_pointcloud_generator import generate_synthetic_pointcloud
        ply = str(Path(args.output).parent / "synthetic_building.ply")
        generate_synthetic_pointcloud(ply)
    result = detect_floor_levels(ply)
    _save_json(result, Path(args.output))
    return result


def cmd_confidence(args: argparse.Namespace) -> dict:
    from .confidence_engine import calculate_confidence
    sources: dict = {}
    if args.source_quality is not None:
        sources["source_quality"] = args.source_quality
    if args.image_quality is not None:
        sources["image_quality"] = args.image_quality
    if args.pointcloud_density is not None:
        sources["pointcloud_density"] = args.pointcloud_density
    if args.model_certainty is not None:
        sources["model_certainty"] = args.model_certainty
    if args.validation_result is not None:
        sources["validation_result"] = args.validation_result
    result = calculate_confidence(sources)
    _save_json(result, Path(args.output))
    return result


def cmd_generate_synthetic(args: argparse.Namespace) -> str:
    from .synthetic_pointcloud_generator import generate_synthetic_pointcloud
    out = generate_synthetic_pointcloud(
        output_path=args.output,
        num_floors=args.num_floors,
        include_basement=not args.no_basement,
        floor_height_m=args.floor_height,
        points_per_slab=args.points_per_slab,
        noise_m=args.noise,
        random_seed=args.seed,
    )
    print(f"  -> saved {out}")
    return out


def cmd_run_all(args: argparse.Namespace) -> None:
    """Run the full pipeline."""
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] Normalising GeoJSON ...")
    from .geojson_normalizer import normalize_geojson
    norm = normalize_geojson(args.parcel)
    _save_json(norm, out_dir / "normalized_parcel.json")

    print("[2/5] Analysing floor plan ...")
    from .floor_plan_analyzer import analyze_floor_plan
    fp = analyze_floor_plan(args.floor_plan, metres_per_pixel=args.metres_per_pixel)
    _save_json(fp, out_dir / "floor_plan_suggestions.json")

    ply_path = args.ply
    if ply_path is None or not Path(ply_path).exists():
        print("[3/5] Generating synthetic point cloud ...")
        from .synthetic_pointcloud_generator import generate_synthetic_pointcloud
        ply_path = str(out_dir / "synthetic_building.ply")
        generate_synthetic_pointcloud(ply_path)
    else:
        print("[3/5] Using existing point cloud ...")

    print("[4/5] Detecting floor levels ...")
    from .pointcloud_floor_detector import detect_floor_levels
    pc = detect_floor_levels(ply_path)
    _save_json(pc, out_dir / "pointcloud_floor_suggestions.json")

    print("[5/5] Calculating confidence ...")
    from .confidence_engine import calculate_confidence
    # Gather scores from prior results
    sources = {
        "source_quality": norm.get("confidence_score", 0.5),
    }
    # image quality: mean unit confidence
    units = fp.get("proposed_units", [])
    if units:
        sources["image_quality"] = sum(
            u["confidence_score"] for u in units
        ) / len(units)
    # pointcloud density: mean cadastral-level confidence
    cadastral = pc.get("suggested_cadastral_levels", [])
    if cadastral:
        sources["pointcloud_density"] = sum(
            lv["confidence_score"] for lv in cadastral
        ) / len(cadastral)
        sources["model_certainty"] = sources["pointcloud_density"]
    # method agreement
    if "method_agreement_score" in pc:
        sources["method_agreement_score"] = pc["method_agreement_score"]
    # validation: 1.0 if methods agree, 0.5 otherwise
    if pc.get("warnings"):
        sources["validation_result"] = 0.50
    else:
        sources["validation_result"] = 0.90

    conf = calculate_confidence(sources)
    _save_json(conf, out_dir / "confidence_result.json")

    print("\n[OK] Pipeline complete. All outputs saved to", out_dir)


# -- argument parser --------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bhudrishti-geospatial-ai",
        description="BhuDrishti Geospatial AI — local AI-assisted geospatial processing.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # normalize
    p_norm = sub.add_parser("normalize", help="Normalise a GeoJSON parcel.")
    p_norm.add_argument("--parcel", required=True, help="Path to .geojson file.")
    p_norm.add_argument("--output", default="output/normalized_parcel.json")

    # analyze-floor-plan
    p_fp = sub.add_parser("analyze-floor-plan", help="Analyse a floor-plan image.")
    p_fp.add_argument("--image", required=True, help="Path to PNG/JPG image.")
    p_fp.add_argument("--metres-per-pixel", type=float, default=None)
    p_fp.add_argument("--output", default="output/floor_plan_suggestions.json")

    # detect-floors
    p_pc = sub.add_parser("detect-floors", help="Detect floor levels from point cloud.")
    p_pc.add_argument("--ply", default=None, help="Path to .PLY file (auto-generated if absent).")
    p_pc.add_argument("--output", default="output/pointcloud_floor_suggestions.json")

    # confidence
    p_conf = sub.add_parser("confidence", help="Calculate combined confidence.")
    p_conf.add_argument("--source-quality", type=float, default=None)
    p_conf.add_argument("--image-quality", type=float, default=None)
    p_conf.add_argument("--pointcloud-density", type=float, default=None)
    p_conf.add_argument("--model-certainty", type=float, default=None)
    p_conf.add_argument("--validation-result", type=float, default=None)
    p_conf.add_argument("--output", default="output/confidence_result.json")

    # generate-synthetic-pointcloud
    p_syn = sub.add_parser("generate-synthetic-pointcloud", help="Generate synthetic PLY.")
    p_syn.add_argument("--output", default="output/synthetic_building.ply")
    p_syn.add_argument("--num-floors", type=int, default=5)
    p_syn.add_argument("--no-basement", action="store_true")
    p_syn.add_argument("--floor-height", type=float, default=3.0)
    p_syn.add_argument("--points-per-slab", type=int, default=2500)
    p_syn.add_argument("--noise", type=float, default=0.02)
    p_syn.add_argument("--seed", type=int, default=42)

    # run-all
    p_all = sub.add_parser("run-all", help="Run the full pipeline.")
    p_all.add_argument("--parcel", default="input/sample_parcel.geojson")
    p_all.add_argument("--floor-plan", default="input/sample_floor_plan.png")
    p_all.add_argument("--ply", default=None)
    p_all.add_argument("--metres-per-pixel", type=float, default=0.05)
    p_all.add_argument("--output-dir", default="output")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "normalize": cmd_normalize,
        "analyze-floor-plan": cmd_analyze_floor_plan,
        "detect-floors": cmd_detect_floors,
        "confidence": cmd_confidence,
        "generate-synthetic-pointcloud": cmd_generate_synthetic,
        "run-all": cmd_run_all,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)
    handler(args)


if __name__ == "__main__":
    main()
