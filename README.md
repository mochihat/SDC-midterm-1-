# SDC-midterm-1-
record what i do 

SDC 2026 Midterm 01 – image point cloud localization (Kaggle Track01 / Track02).

## Layout
- `src/localization/` – ROS 2 package (TA template, extended with a GNSS-prior guided NDT)
- `src/localization/processing_codes/`
  - `txt_to_idx_x_y_yaw.py` – TA script: result txt -> Kaggle csv
  - `gnss_to_csv.py` – GNSS (`/localizer_node/gnss_pose`) linearly interpolated to every frame
  - `gnss_smooth_to_csv.py` – smoothed GNSS prior (Gaussian + cubic spline), optional heading yaw
  - `fuse_to_csv.py` – adds smoothed, gated NDT corrections onto the GNSS prior
- `run_baseline.sh` – original NDT baseline, no RViz
- `run_fusion.sh` – GNSS-prior guided NDT, writes `<tag>_TrackN_result.txt` and `<tag>_TrackN_debug.csv`
- `docker/` – Dockerfile / docker-compose used (copy next to `midterm01/` to build)

Data (not in git) is expected at `/root/data/Track1`, `/root/data/Track2` inside the container.

## Run (inside container)
```bash
cd /root/midterm
colcon build --build-base build_dev --install-base install_dev
cd src/localization/processing_codes
python3 gnss_smooth_to_csv.py /root/data/Track1 Track1 ../result/gnss_smooth_1.csv 1.5 gnss
bash /root/midterm/run_fusion.sh 1 exp -p frame_stride:=10 -p ply_scale:=3.0
python3 fuse_to_csv.py ../result/gnss_smooth_1.csv ../result/exp_Track1_debug.csv ../result/result_1.csv
```

## New localization parameters
| parameter | meaning |
|---|---|
| `prior_file` | csv `idx,x,y,yaw` per frame; NDT starts from it |
| `frame_stride` | run NDT every N frames (others take the prior) |
| `max_correction_xy`, `max_correction_yaw_deg` | reject NDT results further than this from the prior |
| `max_input_range` | drop image points further than this (m, after scaling) |
| `debug_file` | per-frame csv with prior / guess / NDT pose and score |
