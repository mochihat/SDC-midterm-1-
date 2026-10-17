"""Produce one Kaggle CSV for one track from a pipeline config (run inside the container).

Config (JSON); any value may instead be a {"1": ..., "2": ...} per-track dict:
  {
    "name": "fusion_s9_v1",
    "prior": {"sigma": 1.5, "yaw": "gnss" | "heading"},
    "ndt":   null | {"ply_scale": 9.0, "ndt_resolution": 4.0, "frame_stride": 10, ...any ros param},
    "fuse":  {"weight": 1.0, "yaw_weight": 0.0, "sigma_s": 2.0, "max_xy": 2.0, "max_yaw_deg": 3.0}
  }

Usage:
  python3 generate_result.py TRACK CONFIG_JSON OUT_CSV
Prints one JSON line with a summary (shift from prior, NDT acceptance) on success.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "src", "localization", "processing_codes")
WORK = os.path.join(ROOT, "src", "localization", "result", "autogen")


def per_track(value, track):
    if isinstance(value, dict) and set(value) <= {"1", "2"} and value:
        return value.get(track)
    if isinstance(value, dict):
        return {k: per_track(v, track) for k, v in value.items()}
    return value


def run(cmd, **kw):
    print("+", " ".join(cmd), file=sys.stderr, flush=True)
    return subprocess.run(cmd, check=True, **kw)


def main(track, config_json, out_csv):
    cfg = per_track(json.loads(config_json), track)
    name, tdir = cfg["name"], f"/root/data/Track{track}"
    os.makedirs(WORK, exist_ok=True)
    tag = f"{name}_T{track}"

    prior_cfg = cfg.get("prior") or {}
    prior_csv = os.path.join(WORK, f"{tag}_prior.csv")
    run(["python3", os.path.join(PROC, "gnss_smooth_to_csv.py"), tdir, f"Track{track}", prior_csv,
         str(prior_cfg.get("sigma", 1.5)), prior_cfg.get("yaw", "gnss")], cwd=PROC)

    summary = {"name": name, "track": track}
    ndt = cfg.get("ndt")
    if not ndt:
        os.replace(prior_csv, out_csv)
    else:
        ros_args = []
        for k, v in ndt.items():
            ros_args += ["-p", f"{k}:={v}"]
        run(["bash", os.path.join(ROOT, "run_fusion.sh"), track, f"autogen/{tag}"] + ros_args,
            env={**os.environ, "PRIOR": prior_csv}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        debug_csv = os.path.join(WORK, f"{tag}_Track{track}_debug.csv")
        fuse = cfg.get("fuse") or {}
        args = ["python3", os.path.join(PROC, "fuse_to_csv.py"), prior_csv, debug_csv, out_csv]
        for k in ("weight", "yaw_weight", "sigma_s", "max_xy", "max_yaw_deg"):
            if k in fuse:
                args += [f"--{k.replace('_', '-')}", str(fuse[k])]
        res = run(args, cwd=PROC, capture_output=True, text=True)
        summary["fuse_log"] = res.stdout.strip()

    summary["out"] = out_csv
    print(json.dumps(summary))


if __name__ == "__main__":
    main(*sys.argv[1:4])
