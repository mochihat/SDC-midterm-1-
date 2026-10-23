#!/bin/bash
# Track03 (no GNSS, causal - rules 10/22): the submitted file is the direct output of this script.
# Run on the host:  bash midterm01/tools/run_track3.sh [OUT.csv]
# 1. tools/cache_ply.py: raw_ply (ASCII) -> binary arrays + road heights (deterministic, ~15 s)
# 2. tools/track_localize.py: GICP + correlative scan matching on the LiDAR map, scan-to-scan odometry, IMU gyro / ZUPT;
#    every output row is written when its frame is processed (frames <= k only). Configuration "A2h" (23/10):
#    gyro integration fixed, ZUPT + online gyro bias, CSM +-15 m (kappa 15), GICP noise 0.7 m lateral / 2 m along,
#    no map-yaw pull while standing, multi-hypothesis start (11 yaws +-30 deg, best hypothesis per frame).
# Same output for any --threads (checked 23/10).
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
OUT=${1:-src/localization/result/track3/t3_A2h.csv}
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
mkdir -p cache
run python3 tools/cache_ply.py 3 --data /w/data --cache /w/cache
run python3 tools/track_localize.py 3 --data /w/data --cache /w/cache --init /w/data/Track3/init_guess.txt \
  --ply raw_ply --level-init --threads 10 \
  --yaw-offset 0.66 --bias-along -0.27 --bias-lat 0 --tau-yaw 10 \
  --hyp-yaw=-30,-24,-18,-12,-6,0,6,12,18,24,30 \
  --odometry 6 --zupt-acc 0.1 --bias-online 500 \
  --csm-window 15 --csm-kappa 15 --sigma-match-along 2 --hold-yaw-standing \
  --out "$OUT" --diag "${OUT%.csv}_diag.csv"
