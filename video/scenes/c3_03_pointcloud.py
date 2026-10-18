"""Chương 3.3 – Point cloud, .ply, .pcd, bản đồ LiDAR."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402

PLY_HEAD = """ply
format ascii 1.0
element vertex 41058
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
0.24258637 0.14924264 -0.12434131 206 204 219
0.2428726 0.15082306 -0.12454903 205 205 217
0.25840233 -0.12307531 -0.11768234 200 200 204"""

PCD_HEAD = """# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z intensity
SIZE 4 4 4 4
TYPE F F F F
WIDTH 00000000000059531846
POINTS 00000000000059531846
DATA ascii"""

CHAPTER = "c3_03_pointcloud"

BEATS = [
    ("Món thứ ba: point cloud. Point cloud là một đống điểm ba chiều. Mỗi điểm có x, y, z, có khi có thêm màu.",
     [("title", "3.3", "Point cloud · .ply · .pcd", "đám điểm 3D")]),
    ("File ply là định dạng phổ biến. raw_ply của đề là dạng chữ, đọc được bằng mắt: phần đầu khai báo, "
     "sau đó mỗi dòng một điểm, gồm x, y, z và màu.",
     [("caption", "Đầu file raw_ply thật (frame 0)"), ("code", PLY_HEAD, "text", 22)]),
    ("File pcd là định dạng của thư viện PCL, Point Cloud Library, thư viện C++ mà code của đề dùng.",
     [("caption", "Đầu file map.pcd thật"), ("code", PCD_HEAD, "text", 22)]),
    ("Bản đồ map.pcd của Track01 có gần sáu mươi triệu điểm, nặng 2.7 GB. Đây là nó nhìn từ trên xuống, "
     "kèm đường xe chạy.",
     [("image", "map_top_track1.png", 5.8)]),
    ("Bản đồ kiểu này thường được dựng bằng cách cho xe có LiDAR chạy nhiều vòng, rồi ghép tất cả các lần quét lại với nhau.",
     [("big", "59.5 TRIỆU ĐIỂM", "ghép từ nhiều lần quét LiDAR")]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_03_PointCloud(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
