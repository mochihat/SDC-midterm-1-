# Offline experiments: scan matching (tools/gicp_refine.py: small_gicp ICP / GICP / VGICP) and yaw fusion
# (tools/yaw_fusion.py: reads the IMU from the rosbag with rosbags) + numpy/scipy.
FROM python:3.11-slim-bookworm
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 small_gicp==1.0.0 numpy==1.26.4 scipy==1.13.1 \
        rosbags==0.10.4
WORKDIR /work
