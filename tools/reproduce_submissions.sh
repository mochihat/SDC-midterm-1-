#!/bin/bash
# Rebuild every CSV submitted to Kaggle from the raw data, in the order they were made,
# then compare each one with the copy kept in docs/nhat-ky/submissions/.
# Run inside the container:  bash /root/midterm/tools/reproduce_submissions.sh [OUT_DIR]
# The NDT-based files reuse the NDT debug CSVs stored in docs/nhat-ky/data/ndt_debug/
# (re-running NDT itself takes hours; see run_fusion.sh).
set -e
ROOT=/root/midterm
P=$ROOT/src/localization/processing_codes
T=$ROOT/tools
DOC=$ROOT/docs/nhat-ky
DBG=$DOC/data/ndt_debug
OUT=${1:-/tmp/reproduce}
mkdir -p "$OUT"
cd "$P"

# [1] GNSS (/localizer_node/gnss_pose, 4 Hz) linearly interpolated to every frame timestamp.
python3 gnss_to_csv.py /root/data/Track1 Track1 "$OUT/gnss_1.csv"
python3 gnss_to_csv.py /root/data/Track2 Track2 "$OUT/gnss_2.csv"

# [2] Gaussian smoothing (sigma = 1.5 GNSS samples) + cubic spline; yaw = GNSS yaw or motion heading.
for n in 1 2; do
  python3 gnss_smooth_to_csv.py /root/data/Track$n Track$n "$OUT/gnss_smooth_$n.csv" 1.5 gnss
  python3 gnss_smooth_to_csv.py /root/data/Track$n Track$n "$OUT/gnss_heading_$n.csv" 1.5 heading
done

# [3] Track2: NDT corrections (ply_scale 9, ndt_resolution 4, stride 20) fused onto [2] heading prior.
python3 fuse_to_csv.py "$OUT/gnss_heading_2.csv" "$DBG/e2s9r4_Track2_debug.csv" "$OUT/fusion_s9r4_headingyaw_2.csv" \
  --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3 > /dev/null

# [4] CTRV Kalman filter + RTS smoother, noise chosen by maximum likelihood on the GNSS data.
cd "$T"
python3 rts_smoother.py /root/data/Track2 Track2 "$OUT/rts_heading_2.csv" --yaw heading > /dev/null
#     Track1: process noise fixed to physical values (q_a = 1 m/s^2, q_w = 0.1 rad/s^2);
#     positions from the smoother, yaw kept from [2] gnss_smooth_1.
python3 rts_smoother.py /root/data/Track1 Track1 "$OUT/rts_phys_qa1.0_1.csv" --yaw gnss --qa 1.0 --qw 0.1 > /dev/null
python3 csv_ops.py merge "$OUT/rts_pos_gnssyaw_1.csv" --pos "$OUT/rts_phys_qa1.0_1.csv" --yaw "$OUT/gnss_smooth_1.csv"

# [5] Time-offset probes: frame timestamps shifted by -0.1 s / +0.1 s before sampling the trajectory.
for dt in -0.1 0.1; do
  python3 rts_smoother.py /root/data/Track2 Track2 "$OUT/rts_heading_dt${dt}_2.csv" --yaw heading --time-offset $dt > /dev/null
  python3 rts_smoother.py /root/data/Track1 Track1 "$OUT/rts_phys_dt${dt}_1.csv" --yaw gnss --qa 1.0 --qw 0.1 --time-offset $dt > /dev/null
  python3 csv_ops.py merge "$OUT/rts_pos_gnssyaw_dt${dt}_1.csv" --pos "$OUT/rts_phys_dt${dt}_1.csv" --yaw "$OUT/gnss_smooth_1.csv"
done

# [6] Track1 probes on [4]: constant lateral offset (+-0.5 m) and constant yaw offset (+-1 deg).
python3 csv_ops.py offset "$OUT/rts_pos_gnssyaw_1.csv" "$OUT/probe_lat+0.5_1.csv" --lateral 0.5
python3 csv_ops.py offset "$OUT/rts_pos_gnssyaw_1.csv" "$OUT/probe_lat-0.5_1.csv" --lateral -0.5
python3 csv_ops.py offset "$OUT/rts_pos_gnssyaw_1.csv" "$OUT/probe_yaw+1_1.csv" --yaw-deg 1
python3 csv_ops.py offset "$OUT/rts_pos_gnssyaw_1.csv" "$OUT/probe_yaw-1_1.csv" --yaw-deg -1

# [7] Track1: remove the GNSS yaw mounting offset b = -0.42 deg estimated by the smoother in [4],
#     then the same with NDT (scale 9, res 4) position corrections.
python3 csv_ops.py offset "$OUT/rts_pos_gnssyaw_1.csv" "$OUT/phys_yawb_1.csv" --yaw-deg 0.42
cd "$P"
python3 fuse_to_csv.py "$OUT/phys_yawb_1.csv" "$DBG/e2s9r4_Track1_debug.csv" "$OUT/phys_yawb_ndt_1.csv" \
  --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3 > /dev/null

# Compare with what was submitted.
status=0
for f in "$DOC"/submissions/track*/*.csv; do
  name=$(basename "$f")
  if cmp -s "$f" "$OUT/$name"; then
    echo "identical  $name"
  else
    echo "DIFFERENT  $name"
    status=1
  fi
done
exit $status
