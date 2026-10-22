#!/bin/bash
# Pipeline-only result files (no leaderboard-fitted part), steps 3-6 of docs/HUONG-DAN-CHAY.md.
# Run on the host from ~/SDC-midterm01:  bash midterm01/tools/run_clean_pipeline.sh [OUT_DIR]
# Needs: docker image sdc-reg (docker build -t sdc-reg midterm01/docker/reg), the GNSS/Kalman priors
# src/localization/result/phys_yawb_1.csv and rts_heading_2.csv (step 2), the C++ NDT runs c3s08 (Track01)
# and c3s10T2 (Track02) that give z / roll / pitch, and data/TrackN/map_voxel_0.3m.pcd (tools/map_voxel.py).
# Writes OUT_DIR/result_1.csv and OUT_DIR/result_2.csv (default src/localization/result/reg/rerun).
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
R=src/localization/result
OUT=${1:-$R/reg/rerun}
mkdir -p "midterm01/$OUT"
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
# TURN_WEIGHT (default 1 = pipeline): weight of turning frames in the smoothing (fuse_to_csv.py --turn-weight).
fuse() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/midterm01:/w" -w /w sdc-reg:latest \
  python3 src/localization/processing_codes/fuse_to_csv.py "$@" --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3 --demean \
  --turn-weight "${TURN_WEIGHT:-1}"; }

echo "== Track01: yaw prior from the gyro (complementary filter, tau 7 s)"
run python3 tools/yaw_fusion.py 1 --data /w/data --positions $R/phys_yawb_1.csv --gyro-axis z --tau 7 \
  --heading-sigma 1.5 --out $OUT/prior_1.csv
prev=$OUT/prior_1.csv
for k in 1 2; do
  echo "== Track01: GICP pass $k (3cameras_ply, scale from road height, map 0.3 m)"
  run python3 tools/gicp_refine.py 1 --data /w/data --map map_voxel_0.3m.pcd --map-res 0.3 --prior $prev \
    --pose-source c3s08 --stride 1 --ground-height 1.646 --ground-window 57 --method GICP \
    --out $OUT/gicp_p${k}_Track1_debug.csv
  echo "== Track01: fuse pass $k (gate, de-mean, smooth 2 s)"
  fuse $prev $OUT/gicp_p${k}_Track1_debug.csv $OUT/p${k}dm_pos_1.csv
  prev=$OUT/p${k}dm_pos_1.csv
done
echo "== Track01: final yaw (gyro + motion heading of the Kalman track)"
run python3 tools/yaw_fusion.py 1 --data /w/data --positions $prev --heading-from $R/phys_yawb_1.csv \
  --gyro-axis z --tau 7 --heading-sigma 1.5 --out $OUT/result_1.csv

echo "== Track02: Kalman positions + gyro yaw (tau 15 s); no scan matching"
run python3 tools/yaw_fusion.py 2 --data /w/data --positions $R/rts_heading_2.csv --gyro-axis z --tau 15 \
  --heading-sigma 1.0 --out $OUT/result_2.csv

echo "done: midterm01/$OUT/result_1.csv, midterm01/$OUT/result_2.csv"
