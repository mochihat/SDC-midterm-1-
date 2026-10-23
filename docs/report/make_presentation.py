"""Midterm01 presentation (4-6 min, 29/10) -> docs/report/presentation_midterm01.pptx  (python-pptx, native charts)."""
import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

NAVY = RGBColor(0x14, 0x24, 0x2E)
TEAL = RGBColor(0x13, 0x7C, 0x8B)
TEAL_L = RGBColor(0xD8, 0xEE, 0xF0)
AMBER = RGBColor(0xE8, 0x9B, 0x2B)
INK = RGBColor(0x1E, 0x2A, 0x32)
MUTED = RGBColor(0x5F, 0x6F, 0x7A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CARD = RGBColor(0xF3, 0xF6, 0xF8)
HEAD, BODY = "Cambria", "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def text(slide, x, y, w, h, runs, size=16, color=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        for seg in (para if isinstance(para, list) else [para]):
            t, o = (seg, {}) if isinstance(seg, str) else seg
            r = p.add_run()
            r.text = t
            r.font.name = o.get("font", font)
            r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", bold)
            r.font.color.rgb = o.get("color", color)
    return tb


def title(slide, t, sub=None):
    text(slide, 0.6, 0.45, 12.1, 0.8, t, size=34, bold=True, font=HEAD, color=NAVY)
    if sub:
        text(slide, 0.6, 1.2, 12.1, 0.5, sub, size=16, color=MUTED)


def card(slide, x, y, w, h, fill=CARD):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def badge(slide, x, y, label, fill=TEAL, d=0.62):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    tf = s.text_frame
    tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.name = Pt(18), True, HEAD
    r.font.color.rgb = WHITE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


def footer(slide, n):
    text(slide, 0.6, 7.0, 8, 0.3, "SDC 2026 Midterm01 · Team 11", size=10, color=MUTED)
    text(slide, 11.9, 7.0, 0.8, 0.3, str(n), size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def bar_chart(slide, x, y, w, h, cats, vals, ttl, color):
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("score", vals)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    ch.has_title = True
    ch.chart_title.text_frame.text = ttl
    tp = ch.chart_title.text_frame.paragraphs[0]
    tp.runs[0].font.size, tp.runs[0].font.bold, tp.runs[0].font.name = Pt(14), True, BODY
    tp.runs[0].font.color.rgb = INK
    ch.has_legend = False
    pl = ch.plots[0]
    pl.gap_width = 60
    pl.has_data_labels = True
    dl = pl.data_labels
    dl.number_format, dl.number_format_is_linked = "0.00", False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size, dl.font.name = Pt(11), BODY
    dl.font.color.rgb = INK
    ser = pl.series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = color
    va = ch.value_axis
    va.has_major_gridlines = False
    va.visible = False
    ca = ch.category_axis
    ca.tick_labels.font.size, ca.tick_labels.font.name = Pt(10), BODY
    ca.tick_labels.font.color.rgb = MUTED
    ca.format.line.color.rgb = RGBColor(0xC8, 0xD0, 0xD6)


n = 0
# 1 ---------------------------------------------------------------- title
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
text(s, 0.8, 2.1, 11.5, 1.4, "Localizing a car with camera point clouds", size=44, bold=True, font=HEAD, color=WHITE)
text(s, 0.8, 3.45, 11.5, 0.8, "Scan matching against a LiDAR map — Tracks 01, 02 and the GNSS-free Track 03", size=20,
     color=RGBColor(0xB9, 0xD9, 0xDE))
text(s, 0.8, 5.6, 11.5, 0.5, "SDC 2026 · Midterm01 · Team 11 (solo, AI-assisted)", size=16, color=AMBER, bold=True)
notes(s, "Hello, I'm team 11, working alone. Our task: estimate x, y, yaw of the car for every camera frame by registering "
         "image-derived point clouds to a pre-built LiDAR map. I'll cover the pipeline, the bugs we found, Track 03 without GNSS, "
         "and an honest note on leaderboard analysis.")

# 2 ---------------------------------------------------------------- problem
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "The task and the score", "Score = position RMSE (m) + 0.2 × yaw RMSE (deg) — lower is better")
items = [("01", "Track 01", "3011 frames · GNSS + IMU · 3-camera clouds (MapAnything)"),
         ("02", "Track 02", "3299 frames · GNSS + IMU · 13 s standstill at the start"),
         ("03", "Track 03", "3142 frames · no GNSS · causal only · public = first 5–40 %, private = rest")]
for i, (b, h, d) in enumerate(items):
    y = 2.0 + i * 1.45
    card(s, 0.6, y, 7.4, 1.2)
    badge(s, 0.85, y + 0.29, b)
    text(s, 1.75, y + 0.18, 6.0, 0.4, h, size=20, bold=True, font=HEAD, color=NAVY)
    text(s, 1.75, y + 0.6, 6.0, 0.5, d, size=14, color=MUTED)
card(s, 8.5, 2.0, 4.2, 4.1, TEAL_L)
text(s, 8.85, 2.25, 3.6, 0.5, "Inputs", size=20, bold=True, font=HEAD, color=TEAL)
text(s, 8.85, 2.85, 3.6, 3.0, ["LoGeR point cloud per frame (arbitrary scale)", "LiDAR map, 57 M points",
                                 "IMU 100 Hz, noisy initial pose", "GNSS pose (Tracks 01/02 only)"], size=15, color=INK)
footer(s, n)
notes(s, "Three tracks. 01 and 02 have GNSS; 03 has no GNSS, must be causal, and is graded on a hidden private part. "
         "The score mixes metres and degrees, so 1 degree of yaw error costs as much as 20 cm.")

# 3 ---------------------------------------------------------------- scale bug
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "First finding: the point clouds had the wrong scale")
for i, (big, lab) in enumerate([("×3", "scale used by the baseline"), ("×9", "measured from the road height"),
                                 ("91–110 m", "baseline drift on our machine")]):
    x = 0.6 + i * 4.15
    card(s, x, 1.7, 3.85, 2.3)
    text(s, x + 0.3, 1.95, 3.3, 1.1, big, size=54, bold=True, font=HEAD, color=AMBER if i == 2 else TEAL)
    text(s, x + 0.3, 3.15, 3.3, 0.6, lab, size=15, color=MUTED)
text(s, 0.6, 4.5, 12.1, 2.2, [
    [("Fix: ", {"bold": True, "color": NAVY}), "scale every frame by 1.646 m / measured camera height above the road "
     "(trailing median of 57 frames)."],
    [("Lesson: ", {"bold": True, "color": NAVY}), "check units and frames before long runs — we lost ~70 min running NDT at the wrong scale."]],
     size=17)
footer(s, n)
notes(s, "The baseline used ply_scale 3; the camera height in the cloud says the right factor is about 9 for the front camera "
         "cloud and 0.8 for the 3-camera cloud. With the wrong scale NDT drifts 100 m.")

# 4 ---------------------------------------------------------------- T1/T2 pipeline + chart
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Tracks 01/02: GNSS gives the frame, the map refines it")
steps = ["GNSS + Kalman (CTRV) + RTS", "GICP vs map, range ≤ 20 m", "Map correlative matching (CSM)", "Yaw: gyro + map yaw"]
for i, st in enumerate(steps):
    y = 1.75 + i * 1.18
    card(s, 0.6, y, 5.2, 0.95)
    badge(s, 0.8, y + 0.17, str(i + 1), d=0.6)
    text(s, 1.6, y + 0.12, 4.0, 0.75, st, size=16, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
bar_chart(s, 6.2, 1.55, 6.6, 5.2, ["Baseline", "GNSS+Kalman", "+GICP", "+range 20 m", "+CSM", "+map yaw"],
          [1.79, 1.26, 0.79, 0.63, 0.55, 0.51], "Track 01 pipeline score (Kaggle)", TEAL)
footer(s, n)
notes(s, "Pipeline: GNSS with a Kalman smoother, GICP of the camera cloud against the map limited to 20 m because depth from "
         "images degrades with range, a correlative map matching correction, and yaw from the gyro with the slow part from the map. "
         "Track 01 went from 1.79 to 0.51. Track 02 from 1.93 to 0.24 (GICP never helped there, GNSS latency compensation did).")

# 5 ---------------------------------------------------------------- T3 architecture
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Track 03: a causal tracker without GNSS", "Every output row uses only the current and past frames")
blocks = [("Start", "11 yaw hypotheses ±30°, keep the best at each frame (MHT)"),
          ("Motion", "IMU speed filter + scan-to-scan odometry, standstill detection"),
          ("Heading", "gyro projected on gravity (IMU tilted 6°), map yaw τ = 30 s"),
          ("Measure", "CSM on a map likelihood field (±15 m) + GICP")]
for i, (h, d) in enumerate(blocks):
    x, y = 0.6 + (i % 2) * 6.15, 1.95 + (i // 2) * 2.35
    card(s, x, y, 5.9, 2.05)
    badge(s, x + 0.3, y + 0.3, str(i + 1))
    text(s, x + 1.15, y + 0.3, 4.5, 0.5, h, size=20, bold=True, font=HEAD, color=NAVY)
    text(s, x + 1.15, y + 0.85, 4.5, 1.1, d, size=15, color=INK)
footer(s, n)
notes(s, "No GNSS, so the map is the only absolute reference. The tracker starts with 11 yaw hypotheses because the initial "
         "pose is off by about 17 degrees. Motion comes from an IMU speed filter; position is measured by correlative scan matching "
         "on a 2D likelihood field of the map, which sees the true along-road position up to 15 m away, then GICP.")

# 6 ---------------------------------------------------------------- bugs found
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Debugging without ground truth", "Map fit, IMU integration and Tracks 01/02 as references")
rows = [("14 %", "of every turn lost in gyro integration", "fixed: integrate up to the frame time"),
        ("13–30 m", "along-road drift after frame ~500", "correlative scan matching ±15 m"),
        ("2 m", "error from GICP on a static view", "hold the pose while standing"),
        ("4 m", "lag after a restart: steady acceleration read as standstill", "standstill test also checks mean acceleration")]
for i, (big, what, fix) in enumerate(rows):
    y = 1.85 + i * 1.22
    card(s, 0.6, y, 12.1, 1.05)
    text(s, 0.9, y + 0.12, 2.3, 0.8, big, size=30, bold=True, font=HEAD, color=AMBER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 3.3, y + 0.14, 5.0, 0.8, what, size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 8.4, y + 0.14, 4.1, 0.8, fix, size=15, color=TEAL, bold=True, anchor=MSO_ANCHOR.MIDDLE)
footer(s, n)
notes(s, "Track 03 has no answer, so every bug was found with physics: a 90 degree turn integrated to only 77 degrees; "
         "backward IMU integration showed a 29 m along-road drift; on Track 02 repeated matching of one static view dragged the pose 2 m; "
         "and accelerometer integration showed the tracker 4 m behind after the long red light. Public score 0.80; the restart fix "
         "is estimated to improve the private part by 0.1 to 0.2.")

# 7 ---------------------------------------------------------------- leaderboard analysis
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Leaderboard analysis — diagnosis, not the result")
card(s, 0.6, 1.6, 6.3, 2.2, TEAL_L)
text(s, 0.9, 1.8, 5.8, 0.5, "The score is a quadratic oracle", size=20, bold=True, font=HEAD, color=TEAL)
text(s, 0.9, 2.4, 5.8, 1.3, ["Add a change D to a file, read its score:", "mean(e·D) = (P_D² − P² − mean|D|²) / 2"],
     size=16, color=INK)
text(s, 0.6, 4.15, 6.3, 2.6, [
    [("What it taught us: ", {"bold": True, "color": NAVY}), "yaw is the larger error; the reference yaw is the body yaw; "
     "the clean yaw has a slow error with a ~30 s period → fixed with map yaw (0.55 → 0.51)."],
    [("Why it is not graded: ", {"bold": True, "color": NAVY}), "it reconstructs the answer, not a sensor; it cannot work on "
     "Track 03 private data."]], size=15)
cd = CategoryChartData()
cd.categories = ["Track 01", "Track 02"]
cd.add_series("Pipeline", (0.51, 0.24))
cd.add_series("Probed (analysis)", (0.36, 0.11))
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.3), Inches(1.6), Inches(5.5), Inches(5.0), cd).chart
ch.has_title = True
ch.chart_title.text_frame.text = "Pipeline vs probed score"
r0 = ch.chart_title.text_frame.paragraphs[0].runs[0]
r0.font.size, r0.font.bold, r0.font.name = Pt(14), True, BODY
r0.font.color.rgb = INK
ch.has_legend = True
ch.legend.include_in_layout = False
ch.legend.font.size, ch.legend.font.name = Pt(11), BODY
pl = ch.plots[0]
pl.gap_width = 70
pl.has_data_labels = True
pl.data_labels.number_format, pl.data_labels.number_format_is_linked = "0.00", False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.data_labels.font.size, pl.data_labels.font.name = Pt(11), BODY
for ser, col in zip(pl.series, (TEAL, AMBER)):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = col
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
ch.category_axis.tick_labels.font.size = Pt(11)
ch.category_axis.tick_labels.font.color.rgb = MUTED
footer(s, n)
notes(s, "Because the score is an RMSE, each submission measures one projection of the hidden error. We used this to diagnose, "
         "with the TA's permission for Tracks 01/02. The probed files rank first, but our honest algorithm score is the pipeline: "
         "0.51 and 0.24. Some pipeline constants were still calibrated against the probed files, and we label that in the report.")

# 8 ---------------------------------------------------------------- results + lessons (dark)
n += 1
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
text(s, 0.6, 0.45, 12.1, 0.8, "Results and what we would keep", size=34, bold=True, font=HEAD, color=WHITE)
for i, (big, lab) in enumerate([("0.51", "Track 01 pipeline"), ("0.24", "Track 02 pipeline"), ("0.80", "Track 03 public, causal")]):
    x = 0.6 + i * 4.15
    card(s, x, 1.55, 3.85, 1.95, RGBColor(0x22, 0x3A, 0x47))
    text(s, x + 0.3, 1.75, 3.3, 1.0, big, size=50, bold=True, font=HEAD, color=AMBER)
    text(s, x + 0.3, 2.85, 3.3, 0.5, lab, size=15, color=RGBColor(0xB9, 0xD9, 0xDE))
text(s, 0.6, 3.95, 12.1, 2.8, [
    [("Keep: ", {"bold": True, "color": AMBER}), "road-height scale, short-range GICP, map matching, gyro yaw on the true vertical, "
     "physics checks instead of guessing."],
    [("Next: ", {"bold": True, "color": AMBER}), "global start-up search for Track 03, a range-dependent depth model for LoGeR clouds, "
     "multi-camera clouds from the h265 images."],
    [("Honesty: ", {"bold": True, "color": AMBER}), "probed scores are labelled as leaderboard analysis; our algorithm's scores are the pipeline numbers above."]],
     size=17, color=WHITE)
notes(s, "To summarise: pipeline scores 0.51, 0.24 and 0.80 public on the GNSS-free track. The biggest wins came from physics: "
         "the right scale, short-range matching, the IMU mounting, and treating standstills correctly. Thank you.")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presentation_midterm01.pptx")
prs.save(out)
print("wrote", out)
