#!/bin/bash
# GNSS-prior guided NDT for one track (no RViz). Writes <TAG>_TrackN_result.txt and <TAG>_TrackN_debug.csv.
# Usage (inside container): bash /root/midterm/run_fusion.sh N TAG [extra ros args...]
#   e.g. bash /root/midterm/run_fusion.sh 2 s3 -p frame_stride:=10 -p ply_scale:=3.0
set -e
N=$1; TAG=$2; shift 2; T=Track$N; R=/root/midterm/src/localization/result
source /opt/ros/humble/setup.bash
source /root/midterm/install_dev/setup.bash
ros2 run localization localization --ros-args \
  -p map_path:=/root/data/$T -p map_file:=map.pcd -p map_cache_file:=map_downsampled_1m.pcd \
  -p ply_path:=/root/data/$T/raw_ply -p init_guess_file:=/root/data/$T/init_guess.txt \
  -p prior_file:=$R/gnss_smooth_$N.csv \
  -p save_path:=$R/ -p save_file:=${TAG}_${T}_result.txt -p debug_file:=${TAG}_${T}_debug.csv \
  -p keep_alive:=false "$@"
chown 1000:1000 $R/${TAG}_${T}_*
