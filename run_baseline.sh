#!/bin/bash
# Run baseline localization (no RViz) for one track, then convert to Kaggle CSV.
# Usage (inside container): bash /root/midterm/run_baseline.sh 1|2
set -e
N=$1; T=Track$N; R=/root/midterm/src/localization/result
source /opt/ros/humble/setup.bash
source /root/midterm/install/setup.bash
ros2 run localization localization --ros-args \
  -p map_path:=/root/data/$T -p map_file:=map.pcd -p map_cache_file:=map_downsampled_1m.pcd \
  -p ply_path:=/root/data/$T/raw_ply -p init_guess_file:=/root/data/$T/init_guess.txt \
  -p save_path:=$R/ -p save_file:=${T}_result.txt -p keep_alive:=false
python3 /root/midterm/src/localization/processing_codes/txt_to_idx_x_y_yaw.py $R/${T}_result.txt $R/result_$N.csv
echo "DONE $T: $(wc -l < $R/${T}_result.txt) poses -> $R/result_$N.csv"
