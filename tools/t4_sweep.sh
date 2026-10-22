#!/bin/bash
# T4 – offline one-parameter-at-a-time sweep of the Track01 GICP pass 1 (same clean prior, everything else = pipeline).
# Run on the host from anywhere:  bash midterm01/tools/t4_sweep.sh
# Writes src/localization/result/reg/t4/<name>_Track1_debug.csv and <name>_pos_1.csv (fused, pass 1 only);
# summarise with tools/t4_summary.py.
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
R=src/localization/result/reg
OUT=$R/t4
mkdir -p "midterm01/$OUT"
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
PRIOR=$R/clean/clean_prior_1.csv
BASE="--data /w/data --prior $PRIOR --pose-source c3s08 --stride 1 --ground-window 57 --method GICP"

if [ ! -f data/Track1/map_voxel_0.2m.pcd ]; then
  echo "== building data/Track1/map_voxel_0.2m.pcd (new file; the 0.3 m map is not touched)"
  run python3 tools/map_voxel.py /w/data/Track1/map.pcd /w/data/Track1/map_voxel_0.2m.pcd 0.2
fi

go() {  # name, extra args
  local name=$1; shift
  if [ -f "midterm01/$OUT/${name}_Track1_debug.csv" ]; then echo "== $name: exists, skipped"; return; fi
  echo "== $name: $*"
  run python3 tools/gicp_refine.py 1 $BASE "$@" --out $OUT/${name}_Track1_debug.csv 2>&1 | grep -E "wrote|rror"
  run python3 src/localization/processing_codes/fuse_to_csv.py $PRIOR $OUT/${name}_Track1_debug.csv \
    $OUT/${name}_pos_1.csv --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3 --demean | tail -1
}
# reference = pipeline pass 1 settings
go ref       --map map_voxel_0.3m.pcd --map-res 0.3 --ground-height 1.646 --max-range 40
go res0.2    --map map_voxel_0.2m.pcd --map-res 0.2 --ground-height 1.646 --max-range 40
go res0.5    --map map_voxel_0.3m.pcd --map-res 0.5 --ground-height 1.646 --max-range 40
go range20   --map map_voxel_0.3m.pcd --map-res 0.3 --ground-height 1.646 --max-range 20
go range30   --map map_voxel_0.3m.pcd --map-res 0.3 --ground-height 1.646 --max-range 30
go scale0.95 --map map_voxel_0.3m.pcd --map-res 0.3 --ground-height 1.5637 --max-range 40
go scale1.05 --map map_voxel_0.3m.pcd --map-res 0.3 --ground-height 1.7283 --max-range 40
echo "done"
