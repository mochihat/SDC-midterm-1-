"""Front-camera h265 stream of a track bag -> raw .h265 file + per-message times (24/10, for tools/paint_images.sh).

The bag's /lucid_cameras_x00/gige_100_f_hdr/h265 messages (sensor_msgs/Image, encoding h265) carry one encoded frame
each; message k is camera frame k (the raw_ply file names carry the same bag times). Track03's stream starts mid-GOP:
the first key frame (VPS/SPS/PPS + IDR) is message 14, so ffmpeg decodes messages 14.. only (first_frame = 14).

Usage: python3 tools/bag_h265.py TRACK OUT.h265 [--data /w/data] [--camera f]
"""
import argparse
import os

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("out")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--camera", default="f", choices=["f", "fl", "fr"])
    a = p.parse_args()
    ts = get_typestore(Stores.ROS2_HUMBLE)
    first_key = None
    n = 0
    with Reader(os.path.join(a.data, f"Track{a.track}")) as r, open(a.out, "wb") as f, open(a.out + ".ts", "w") as g:
        cons = [c for c in r.connections if c.topic.endswith(f"gige_100_{a.camera}_hdr/h265")]
        for c, t, raw in r.messages(connections=cons):
            m = ts.deserialize_cdr(raw, c.msgtype)
            d = bytes(m.data)
            if first_key is None:
                i = d.find(b"\x00\x00\x01")
                while i >= 0:
                    if (d[i + 3] >> 1) & 0x3F in (19, 20, 21, 32):       # IDR / CRA / VPS
                        first_key = n
                        break
                    i = d.find(b"\x00\x00\x01", i + 3)
            f.write(d)
            g.write(f"{n},{m.header.stamp.sec * 1000000000 + m.header.stamp.nanosec},{t},{len(d)}\n")
            n += 1
    print(f"wrote {a.out}: {n} messages, first key frame at message {first_key}")
    with open(a.out + ".first", "w") as f:
        f.write(f"{first_key}\n")


if __name__ == "__main__":
    main()
