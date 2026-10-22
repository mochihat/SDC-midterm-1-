#!/bin/bash
# Track02 with GICP, same steps as Track01 in run_clean_pipeline.sh (the graded Track02 file uses no scan matching).
# Run on the host:  MAX_RANGE=20 bash midterm01/tools/run_track2_gicp.sh [OUT_DIR]
# Reason to retry (23/10): on Track01 limiting the image clouds to 20 m improved Kaggle 0.80 -> 0.63; with 40 m GICP
# always made Track02 worse (0.28 -> 0.30..0.37). Switches: MAX_RANGE (default 20), TURN_WEIGHT (default 1).
# Writes OUT_DIR/result_2.csv (default src/localization/result/reg/cand/t2_gicp_range${MAX_RANGE}).
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
R=src/localization/result
MR=${MAX_RANGE:-20}
OUT=${1:-$R/reg/cand/t2_gicp_range$MR}
mkdir -p "midterm01/$OUT"
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
fuse() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/midterm01:/w" -w /w sdc-reg:latest \
  python3 src/localization/processing_codes/fuse_to_csv.py "$@" --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3 --demean \
  --turn-weight "${TURN_WEIGHT:-1}"; }

echo "== Track02: Kalman positions + gyro yaw (tau 15 s) as the GICP prior"
run python3 tools/yaw_fusion.py 2 --data /w/data --positions $R/rts_heading_2.csv --gyro-axis z --tau 15 \
  --heading-sigma 1.0 --out $OUT/prior_2.csv
prev=$OUT/prior_2.csv
for k in 1 2; do
  echo "== Track02: GICP pass $k (3cameras_ply, scale from road height, range <= $MR m)"
  run python3 tools/gicp_refine.py 2 --data /w/data --map map_voxel_0.3m.pcd --map-res 0.3 --prior $prev \
    --pose-source c3s10T2 --stride 1 --ground-height 1.646 --ground-window 57 --max-range "$MR" --method GICP \
    --out $OUT/gicp_p${k}_Track2_debug.csv
  fuse $prev $OUT/gicp_p${k}_Track2_debug.csv $OUT/p${k}dm_pos_2.csv
  prev=$OUT/p${k}dm_pos_2.csv
done
echo "== Track02: final yaw (gyro + motion heading of the Kalman track)"
run python3 tools/yaw_fusion.py 2 --data /w/data --positions $prev --heading-from $R/rts_heading_2.csv \
  --gyro-axis z --tau 15 --heading-sigma 1.0 --out $OUT/result_2.csv
echo "done: midterm01/$OUT/result_2.csv"
