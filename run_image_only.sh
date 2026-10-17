#!/bin/bash
# Image-only localization (no GNSS / IMU): NDT of the scaled LoGeR point clouds against the LiDAR map,
# starting from init_guess.txt, each frame starting from the previous pose (like the TA baseline) but with
# the corrected point cloud scale (x9 instead of x3) and a finer NDT grid.
# Writes <TAG>_TrackN_result.txt, <TAG>_TrackN_debug.csv and the Kaggle csv <TAG>_TrackN.csv.
# Usage (inside container): bash /root/midterm/run_image_only.sh N TAG [extra ros args...]
#   e.g. bash /root/midterm/run_image_only.sh 2 img_test -p max_frames:=150
set -e
N=$1; TAG=$2; shift 2; T=Track$N; R=/root/midterm/src/localization/result
source /opt/ros/humble/setup.bash
source /root/midterm/install_dev/setup.bash
ros2 run localization localization --ros-args \
  -p map_path:=/root/data/$T -p map_file:=map.pcd -p map_cache_file:=map_downsampled_1m.pcd \
  -p ply_path:=/root/data/$T/raw_ply -p init_guess_file:=/root/data/$T/init_guess.txt \
  -p save_path:=$R/ -p save_file:=${TAG}_${T}_result.txt -p debug_file:=${TAG}_${T}_debug.csv \
  -p keep_alive:=false \
  -p ply_scale:=9.0 -p ndt_resolution:=4.0 -p input_voxel_leaf_size:=1.0 -p ndt_max_iterations:=30 \
  -p submap_half_size:=60.0 -p max_input_range:=40.0 "$@"
python3 /root/midterm/src/localization/processing_codes/txt_to_idx_x_y_yaw.py $R/${TAG}_${T}_result.txt $R/${TAG}_${T}.csv
chown 1000:1000 $R/${TAG}_${T}*
