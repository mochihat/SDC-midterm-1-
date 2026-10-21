# SDC-midterm-1-
record what i do 

SDC 2026 Midterm 01 – image point cloud localization (Kaggle Track01 / Track02).

**Trạng thái dự án, luật và việc tiếp theo: [CLAUDE.md](CLAUDE.md)** · **Hướng dẫn chạy từ code tới kết quả: [docs/HUONG-DAN-CHAY.md](docs/HUONG-DAN-CHAY.md)**

**Process log (Vietnamese): [docs/nhat-ky/](docs/nhat-ky/README.md)** – data analysis, NDT experiments, every Kaggle
submission (how it was made, what changed, why, score, conclusion), error analysis and lessons learned.
Best so far: Track01 `phys_yawb_1.csv` 1.25338, Track02 `rts_heading_2.csv` 0.40778
(`bash /root/midterm/tools/reproduce_submissions.sh` rebuilds every submitted file).

## Layout
- `src/localization/` – ROS 2 package (TA template, extended with a GNSS-prior guided NDT)
- `src/localization/processing_codes/`
  - `txt_to_idx_x_y_yaw.py` – TA script: result txt -> Kaggle csv
  - `gnss_to_csv.py` – GNSS (`/localizer_node/gnss_pose`) linearly interpolated to every frame
  - `gnss_smooth_to_csv.py` – smoothed GNSS prior (Gaussian + cubic spline), optional heading yaw
  - `fuse_to_csv.py` – adds smoothed, gated NDT corrections onto the GNSS prior
- `run_baseline.sh` – original NDT baseline, no RViz
- `run_fusion.sh` – GNSS-prior guided NDT, writes `<tag>_TrackN_result.txt` and `<tag>_TrackN_debug.csv`
- `tools/`
  - `rts_smoother.py` – CTRV Kalman filter + RTS smoother over the GNSS poses (noise by maximum likelihood, GNSS yaw offset)
  - `csv_ops.py`, `compare_csv.py` – combine / offset / compare submission CSVs
  - `reproduce_submissions.sh` – rebuild every submitted CSV and compare with `docs/nhat-ky/submissions/`
  - `analyze_probes.py`, `analyze_gnss_imu.py`, `ground_scale.py`, `check_frame_alignment.py`, `pc_io.py` – analysis
- `docker/` – Dockerfile / docker-compose used (copy next to `midterm01/` to build)
- `docs/nhat-ky/` – process log, submitted files, analysis outputs

Data (not in git) is expected at `/root/data/Track1`, `/root/data/Track2` inside the container.

## Run (inside container)
```bash
cd /root/midterm
colcon build --build-base build_dev --install-base install_dev
cd src/localization/processing_codes
python3 gnss_smooth_to_csv.py /root/data/Track1 Track1 ../result/gnss_smooth_1.csv 1.5 gnss
# point clouds need ply_scale ~9 (not the template's 3); NDT resolution 4 m
bash /root/midterm/run_fusion.sh 1 exp -p frame_stride:=20 -p ply_scale:=9.0 -p ndt_resolution:=4.0
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
