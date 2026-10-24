#!/bin/bash
# Track03 with road-paint matching (24/10; causal - rules 10/22). Run on the host:
#   bash midterm01/tools/run_track3_paint.sh [OUT.csv]
# Needs the docker image sdc-reg and ffmpeg on the host (h265 decoding).
# 1. tools/run_track3.sh: the LoGeR / IMU tracker (t3_Z3a, causal) = the prior
# 2. tools/bag_h265.py + ffmpeg: front-camera images from the bag (grey, rows 420-799; messages 14.. decodable)
# 3. tools/paint_map.py: road surface + paint rasters of map.pcd (corridor of 30 m around the prior: for frame k only
#    the map within ~25 m of the prior's pose at k is used, so the crop changes nothing)
# 4. tools/paint_measure.py: per frame k, image k matched to the map paint around the prior's pose at k
# 5. tools/paint_fuse.py: causal Kalman filter on the prior's error (frames <= k)
# Parameters: camera pitch 1.0 / yaw -1.5 deg (calibrated on Track01 + Track02 at their reference poses), kappa 20,
# kappa scaled by motion (0.3 m), sd floor 0.3 / 0.15 m, lateral lever -0.10 m (Track02 calibration).
# Public scores 24/10: lever -0.25 -> 0.56 (t3_PA1), -0.10 -> 0.49 (t3_PA2), floor 0.5/0.25 -> 0.55 (t3_PA3); Z3a 0.80.
set -e
cd "$(dirname "$0")/../.."                      # ~/SDC-midterm01
OUT=${1:-src/localization/result/track3/t3_PA2.csv}
PRIOR=src/localization/result/track3/t3_Z3a.csv
CR=${CACHE_ROOT:-cache}                          # images / rasters / measurements (not committed)
C=$CR/Track3
run() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/w" -w /w/midterm01 sdc-reg:latest "$@"; }
[ -f "midterm01/$PRIOR" ] || bash midterm01/tools/run_track3.sh "$PRIOR"
mkdir -p $C/img $C/paint
if [ ! -f $C/img/f_gray.json ]; then
  run python3 tools/bag_h265.py 3 /w/$C/img/f.h265
  FIRST=$(cat $C/img/f.h265.first)
  ffmpeg -v error -y -i $C/img/f.h265 -vf "crop=1440:380:0:420,format=gray" -f rawvideo $C/img/f_gray_r420.raw
  ffmpeg -v error -y -i data/Track3/Track3_images/camera_info/gige_100_f_hdr_mask.png -pix_fmt gray -f rawvideo \
    $C/img/f_mask.raw
  echo "{\"file\": \"f_gray_r420.raw\", \"row0\": 420, \"rows\": 380, \"width\": 1440, \"first_frame\": $FIRST}" \
    > $C/img/f_gray.json
fi
[ -f $C/paint_map.npz ] || run python3 tools/paint_map.py 3 "$PRIOR" /w/$C/paint_map.npz
run python3 tools/paint_measure.py 3 "$PRIOR" /w/$C/paint/meas_prior.npz --cache /w/$CR --procs 10
run python3 tools/paint_fuse.py "$PRIOR" /w/$C/paint/meas_prior.npz "$OUT" --kappa 20 --kappa-motion 0.3 \
  --sd-floor 0.3,0.15 --lever-along 0 --lever-lat -0.10 --diag "${OUT%.csv}_diag.csv"
