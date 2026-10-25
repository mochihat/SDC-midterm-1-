#!/bin/bash
# Track03 with road-paint matching (24/10; causal - rules 10/22). Run on the host:
#   bash midterm01/tools/run_track3_paint.sh [OUT.csv]
# Needs the docker image sdc-reg and ffmpeg on the host (h265 decoding).
# 1. tools/run_track3.sh: the LoGeR / IMU tracker (t3_Z3a, causal) = the prior
# 2. tools/bag_h265.py + ffmpeg: front-camera images from the bag (grey, rows 420-799; messages 14.. decodable)
# 3. tools/paint_map.py: road surface + paint rasters of map.pcd (corridor of 30 m around the prior: for frame k only
#    the map within ~25 m of the prior's pose at k is used, so the crop changes nothing)
# 4. tools/paint_measure.py: per frame k, image k matched to the map paint around the prior's pose at k
# 5. tools/paint_fuse.py: causal Kalman filter on the prior's error (frames <= k); PASSES=N repeats 4-5 with the
#    search windows centred on the previous pass (Z3a errors beyond the +-2 / +-1.5 m windows in the turn / at the end)
# Parameters: camera pitch 1.0 / yaw -1.5 deg (calibrated on Track01 + Track02 at their reference poses), kappa 20,
# kappa scaled by motion (0.3 m), sd floor 0.3 / 0.15 m, lateral lever -0.10 m (Track02 calibration).
# Public scores 24/10: lever -0.25 -> 0.56 (t3_PA1), -0.10 -> 0.49 (t3_PA2), floor 0.5/0.25 -> 0.55 (t3_PA3); Z3a 0.80.
# 25/10: FUSE_EXTRA="--motion imu --imu-vmin 4 --imu-wmax 3 --kappa-imu K" = the pose moves with the IMU speed (scale
# state) where that speed is good (--times: the front camera's capture times, used by --motion imu only).
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
if [ "${SIDE:-0}" = 1 ]; then
  for cam in fl fr; do
    [ -f $C/img/${cam}_gray.json ] && continue
    run python3 tools/bag_h265.py 3 /w/$C/img/$cam.h265 --camera $cam
    F=$(cat $C/img/$cam.h265.first)
    ffmpeg -v error -y -i $C/img/$cam.h265 -vf "crop=1440:508:0:420,scale=720:254,format=gray" -f rawvideo \
      $C/img/${cam}_gray_h_r420.raw
    echo "{\"file\": \"${cam}_gray_h_r420.raw\", \"row0\": 420, \"rows\": 508, \"width\": 1440, \"first_frame\": $F, \"scale\": 0.5}" \
      > $C/img/${cam}_gray.json
  done
fi
[ -f $C/paint_map.npz ] || run python3 tools/paint_map.py 3 "$PRIOR" /w/$C/paint_map.npz
# passes 2..: the search windows of frame k centred on the previous pass's pose at k (causal: that pose uses frames
# <= k); the filter state still is the error of the prior (Z3a). Pass 1 = t3_PA2 (public 0.49).
FUSE="${FUSE:---kappa 20 --kappa-motion 0.3 --sd-floor 0.3,0.15 --lever-along 0 --lever-lat -0.10} ${FUSE_EXTRA:-}"
PASSES=${PASSES:-1}
CEN="$PRIOR"
for i in $(seq 1 $PASSES); do
  if [ $i -lt $PASSES ]; then P_OUT=src/localization/result/track3/paint_pass$i.csv; else P_OUT="$OUT"; fi
  run python3 tools/paint_measure.py 3 "$CEN" /w/$C/paint/meas_pass$i.npz --cache /w/$CR --procs 10
  SIDE_OPT=""
  if [ "${SIDE:-0}" = 1 ]; then
    # front-left / front-right cameras as a second NCC volume on the same search grid and centres
    run python3 tools/paint_measure.py 3 "$CEN" /w/$C/paint/meas_side_pass$i.npz --cache /w/$CR --procs 10 \
      --side --separate --along=-4,18 --lat=-9,9 --norm 30
    SIDE_OPT="--meas-side /w/$C/paint/meas_side_pass$i.npz"
  fi
  run python3 tools/paint_fuse.py "$PRIOR" /w/$C/paint/meas_pass$i.npz "$P_OUT" --center "$CEN" $FUSE $SIDE_OPT \
    --times /w/$C/img/f.h265.ts --diag "${P_OUT%.csv}_diag.csv"
  CEN="$P_OUT"
done
