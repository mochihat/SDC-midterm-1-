#!/bin/bash
# Track03 (no GNSS, causal - rules 10/22): the submitted file is the direct output of this script.
# Run on the host:  bash midterm01/tools/run_track3.sh [OUT.csv]
# 1. tools/cache_ply.py: raw_ply (ASCII) -> binary arrays + road heights (deterministic, ~15 s)
# 2. tools/track_localize.py: GICP + correlative scan matching on the LiDAR map, IMU speed filter, gyro yaw, ZUPT;
#    every output row is written when its frame is processed (frames <= k only). Configuration "L2" (23/10 afternoon):
#    = "A2h" (gyro integration fixed, ZUPT + online gyro bias, CSM +-15 m kappa 15, GICP noise 0.7 m lateral / 2 m along,
#    no map-yaw pull while standing, 11 start yaws +-30 deg) + CSM camera lever -1.0 m along / +0.12 m lateral
#    (the likelihood peak sits 1.0 m behind the true reference on Track01 AND Track02) + speed from the IMU
#    (accelerometer, centripetal speed in turns, ZUPT; odometry only as a gated measurement).
#    Lever -0.7 ("L2b"): on Track01/02 the clouds are ~10 % too large (best map fit x0.90 at the true poses) and the
#    CSM peak sits 1.0 m behind the reference; at the right scale it sits at -0.12 m. Track03's own clouds fit best at
#    x0.925-0.95 (scale_check / online estimate) -> lever -0.56..-0.78 at scale 1.0. Rescaling the clouds instead
#    (--scale-mult / --scale-online) lost the lock in the Track03 turn, so the scale stays 1.0.
#    Submitted versions: t3_A2h (drop the last three option lines), t3_L2 (lever -1.0), t3_L2b (drop the last option line).
#    "W3h" (23/10 evening, validated on Track01/02 with --reset-ref and on Track03 by map fit / dynamic consistency):
#    the IMU is mounted ~6 deg off level -> yaw rate = gyro vector . causal gravity direction (--gyro-axis up, bias
#    prior -0.24 deg/s fitted on Track01/02); map-yaw time constant 30 s (10 s during the first 10 s: start
#    hypotheses are 6 deg apart) -> yaw RMS Track02 0.88 -> 0.40 deg, Track01 0.64 -> 0.55 deg; the speed filter's
#    variance widens the along-track prior (turns); no GICP update while standing (one static view: Track02's
#    230 standing frames drag the position 2 m off).
# Same output for any --threads (checked 23/10).
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
OUT=${1:-src/localization/result/track3/t3_W3h.csv}
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
mkdir -p cache
run python3 tools/cache_ply.py 3 --data /w/data --cache /w/cache
run python3 tools/track_localize.py 3 --data /w/data --cache /w/cache --init /w/data/Track3/init_guess.txt \
  --ply raw_ply --level-init --threads 10 \
  --yaw-offset 0.66 --bias-along -0.27 --bias-lat 0 \
  --hyp-yaw=-30,-24,-18,-12,-6,0,6,12,18,24,30 \
  --odometry 6 --zupt-acc 0.1 --bias-online 500 \
  --csm-window 15 --csm-kappa 15 --sigma-match-along 2 --hold-yaw-standing \
  --csm-bias-along -0.7 --csm-bias-lat 0.12 \
  --speed-filter \
  --gyro-axis up --gyro-bias -0.24 --tau-yaw 30 --tau-yaw-start 10 --tau-yaw-start-time 10 --along-speed-noise 28 \
  --hold-position-standing \
  --out "$OUT" --diag "${OUT%.csv}_diag.csv"
