#!/bin/bash
# One chunk (frames START .. START+COUNT-1) of a GNSS-prior guided NDT run, so a track can be split over
# several CPU cores. Frames are independent given the prior (only z/roll/pitch carry over between frames).
# Writes result/chunks/<TAG>_<START>_debug.csv; merge the chunks with tools/merge_debug.py.
# Usage (inside container): PRIOR=prior.csv bash /root/midterm/run_chunk.sh N TAG START COUNT [extra ros args...]
set -e
N=$1; TAG=$2; START=$3; COUNT=$4; shift 4; T=Track$N; R=/root/midterm/src/localization/result
source /opt/ros/humble/setup.bash
source /root/midterm/install_par/setup.bash
mkdir -p $R/chunks
ros2 run localization localization --ros-args \
  -p map_path:=/root/data/$T -p map_file:=map.pcd -p map_cache_file:=map_downsampled_1m.pcd \
  -p ply_path:=/root/data/$T/raw_ply -p init_guess_file:=/root/data/$T/init_guess.txt \
  -p prior_file:=$PRIOR -p start_frame:=$START -p max_frames:=$COUNT \
  -p save_path:=$R/chunks/ -p save_file:=${TAG}_${START}_result.txt -p debug_file:=${TAG}_${START}_debug.csv \
  -p keep_alive:=false "$@"
chown 1000:1000 $R/chunks/${TAG}_${START}_*
