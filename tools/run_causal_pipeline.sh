#!/bin/bash
# CAUSAL pipeline (rule 10/22: "use current and past frames only, no backward or non-causal smoothing").
# Run on the host:  bash midterm01/tools/run_causal_pipeline.sh [OUT_DIR]      (~8 min)
# Track01: forward Kalman (fixed noise config) -> causal gyro yaw (PI, tau 7) -> GICP pass 1 (range 20 m) -> causal fusion
#          (median of last 5, running-mean de-bias, one-sided EMA) -> GICP pass 2 -> causal fusion -> causal gyro yaw
# Track02: forward Kalman -> GICP (range 20 m) used only for the yaw while standing still -> causal gyro yaw (tau 15)
# Switches: MAX_RANGE (20), EMA_TAU (2 s), TURN_WEIGHT (0), TAU1 (7), TAU2 (15).
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
R=src/localization/result
OUT=${1:-$R/causal/pipeline}
mkdir -p "midterm01/$OUT"
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
MR=${MAX_RANGE:-20}
fuse() { run python3 src/localization/processing_codes/fuse_to_csv.py "$@" --causal --yaw-weight 0 --sigma-s "${EMA_TAU:-2}" \
  --max-xy 2 --max-yaw-deg 3 --demean --turn-weight "${TURN_WEIGHT:-0}"; }
gicp() { run python3 tools/gicp_refine.py "$1" --data /w/data --map map_voxel_0.3m.pcd --map-res 0.3 --prior "$2" \
  --pose-source "$3" --stride 1 --ground-height 1.646 --ground-window 57 --ground-causal --max-range $MR --method GICP --out "$4"; }

echo "== Track01: forward Kalman filter (no RTS), fixed noise config"
run python3 tools/rts_smoother.py /w/data/Track1 Track1 $OUT/kf_1.csv --yaw gnss --causal --sigma-p 0.05 --sigma-yaw 2.0 --qa 1.0 --qw 0.1
run python3 tools/rts_smoother.py /w/data/Track1 Track1 $OUT/kfh_1.csv --yaw heading --causal --sigma-p 0.05 --sigma-yaw 2.0 --qa 1.0 --qw 0.1
run python3 tools/causal_yaw.py 1 --data /w/data --positions $OUT/kf_1.csv --heading-from $OUT/kfh_1.csv --tau "${TAU1:-7}" --out $OUT/prior_1.csv
prev=$OUT/prior_1.csv
for k in 1 2; do
  echo "== Track01: GICP pass $k (range $MR m) + causal fusion"
  gicp 1 $prev c3s08 $OUT/gicp_p${k}_Track1_debug.csv
  fuse $prev $OUT/gicp_p${k}_Track1_debug.csv $OUT/p${k}_pos_1.csv
  prev=$OUT/p${k}_pos_1.csv
done
run python3 tools/causal_yaw.py 1 --data /w/data --positions $prev --heading-from $OUT/kfh_1.csv --tau "${TAU1:-7}" --out $OUT/result_1.csv

echo "== Track02: forward Kalman + causal gyro yaw (map yaw while standing)"
run python3 tools/rts_smoother.py /w/data/Track2 Track2 $OUT/kf_2.csv --yaw heading --causal --sigma-p 0.006 --sigma-yaw 1.0 --qa 1.0 --qw 0.03
run python3 tools/causal_yaw.py 2 --data /w/data --positions $OUT/kf_2.csv --heading-from $OUT/kf_2.csv --tau "${TAU2:-15}" --out $OUT/prior_2.csv
gicp 2 $OUT/prior_2.csv c3s10T2 $OUT/gicp_p1_Track2_debug.csv
run python3 tools/causal_yaw.py 2 --data /w/data --positions $OUT/kf_2.csv --heading-from $OUT/kf_2.csv --tau "${TAU2:-15}" \
  --gicp-debug $OUT/gicp_p1_Track2_debug.csv --out $OUT/result_2.csv
echo "done: midterm01/$OUT/result_1.csv, midterm01/$OUT/result_2.csv"
