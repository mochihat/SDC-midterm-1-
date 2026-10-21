"""Table + chart of every Kaggle submission, split by where the result comes from.

Classes (after the TA ruling of 20/10, docs/nhat-ky/08 §12):
  pipeline     algorithm output only (parameters may be picked by score = ordinary tuning, allowed)
  mixed        algorithm output built on top of a file that contains a leaderboard-fitted part
               (e.g. GICP started from / yaw taken from a score-weighted combination)
  leaderboard  probes and score-weighted combinations (leaderboard-based fitting, not allowed for grading)
  other        test uploads / wrong-track error

Scores: Kaggle now shows public scores truncated to 2 decimals; the 5-decimal values come from
docs/nhat-ky/data/kaggle_submissions.csv (logged before 21/10) or docs/nhat-ky/data/precise_scores.json.

Usage: python3 tools/submission_stats.py   (writes docs/nhat-ky/09-thong-ke-nop-bai.md, data/submission_stats.csv,
       fig/submission_progress.png)
"""
import csv
import json
import os
import re
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs", "nhat-ky")
DATA = os.path.join(DOCS, "data")

PIPELINE = {
    "1": r"^(kaggle_track1_result|gnss_1|gnss_smooth_1|gnss_heading_1|rts_pos_gnssyaw.*|phys_yawb_1|phys_yawb_ndt_1|"
         r"lagyaw_pos_best_1|clean_.*)$",
    "2": r"^(gnss_2|gnss_smooth_2|gnss_heading_2|fusion_s9r4_headingyaw_2|rts_heading.*|lagyaw_pos_best_2|"
         r"yawtau0\.75_pos_best_2|gnssyaw_pos_rts_2|clean_.*)$",
}
LEADERBOARD = r"^(probe_.*|yawproj_.*|posproj_.*|posyaw_v\d_\d|lb_posyaw_.*|corr_r\d_\d|bump\d_\d_\d|pp_t\d_r\d)$"
OTHER = r"^(trial)$"

COLORS = {"pipeline": "#2a78d6", "mixed": "#eb6834", "leaderboard": "#1baf7a"}
MARKERS = {"pipeline": "o", "mixed": "s", "leaderboard": "^"}
LABEL_VI = {"pipeline": "Pipeline (thuật toán)", "mixed": "Lai (dựa trên file có phần chọn theo điểm)",
            "leaderboard": "Dò / tổ hợp theo leaderboard", "other": "Khác"}
NOTE = {
    "kaggle_track1_result": "chạy code mẫu TA lần đầu (sai tỉ lệ)",
    "gnss_1": "nội suy GNSS", "gnss_2": "nội suy GNSS",
    "gnss_heading_2": "yaw = hướng chạy", "rts_heading_2": "Kalman CTRV + RTS",
    "rts_pos_gnssyaw_1": "Kalman CTRV + RTS", "phys_yawb_1": "+ bỏ lệch yaw GNSS 0.42°",
    "yawproj_v1_1": "tổ hợp yaw theo điểm", "posproj_v1_1": "tổ hợp vị trí NDT theo điểm",
    "ndt3c_s08_pos_1": "NDT 3cameras tỉ lệ 0.8", "gicp_ground_all_pos_1": "GICP + tỉ lệ mặt đường",
    "gicp_ground_pass2_pos_1": "GICP lượt 2", "pass2dm_bestyaw_1": "GICP 2 lượt + demean",
    "cfz1_tau7": "+ yaw gyro τ7", "cfz2_tau15": "yaw gyro τ15", "cf_tau5_2": "yaw gyro τ5",
    "lb_posyaw_v1_1": "tổ hợp 18 trường + 7 yaw", "lb_posyaw_v1_2": "tổ hợp",
    "corr_r1_1": "sửa từ dò dao động 0–6", "corr_r1_2": "sửa từ dò dao động 0–6",
    "posproj_t2_v1_2": "tổ hợp vị trí theo điểm", "startfix_on_v3_2": "yaw khởi hành bằng gyro",
}


def is_probe(name):
    """Deliberately perturbed measurement files - not attempts at a better result."""
    return name.startswith(("probe_", "bump"))


def classify(track, name):
    if re.match(OTHER, name):
        return "other"
    if re.match(PIPELINE[track], name):
        return "pipeline"
    if re.match(LEADERBOARD, name):
        return "leaderboard"
    return "mixed"


def load():
    raw = json.load(open(os.path.join(DATA, "kaggle_submissions_raw.json")))
    logged = {}
    with open(os.path.join(DATA, "kaggle_submissions.csv")) as f:
        for r in csv.DictReader(f):
            logged[r["kaggle_file_name"]] = r["public_score"]
    prec = {k.split("|", 1)[1]: v for k, v in json.load(open(os.path.join(DATA, "precise_scores.json"))).items()}
    rows = []
    for track, subs in raw.items():
        for s in subs:
            desc = s.get("description") or ""
            src = desc[5:] if desc.startswith("bot: ") else s["fileName"]  # Kaggle drops "+" from file names
            name = re.sub(r"(_[0-9a-f]{6})?\.csv$", "", src)
            shown = s["publicScore"] or ""
            score, exact = None, False
            if s["fileName"] in logged and logged[s["fileName"]]:
                score, exact = float(logged[s["fileName"]]), True
            elif name + ".csv" in prec and shown and abs(prec[name + ".csv"] - float(shown)) < 0.01:
                score, exact = prec[name + ".csv"], True
            elif shown:
                score = float(shown)
            t = datetime.strptime(s["date"][:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=8)
            cls = "other" if s["status"] != "complete" else classify(track, name)
            rows.append(dict(track=track, time=t, file=name, score=score, exact=exact, cls=cls,
                             note=NOTE.get(name, "")))
    rows.sort(key=lambda r: (r["track"], r["time"]))
    return rows


def fmt(r):
    if r["score"] is None:
        return "lỗi"
    return f"{r['score']:.5f}" if r["exact"] else f"{r['score']:.2f}*"


def chart(rows, path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
    for ax, track, base in zip(axes, ["1", "2"], [1.79075, 1.92587]):
        rs = [r for r in rows if r["track"] == track and r["cls"] in COLORS and r["score"] is not None
              and r["score"] < 2]
        for cls in COLORS:
            pts = [r for r in rs if r["cls"] == cls]
            ax.scatter([r["time"] for r in pts], [r["score"] for r in pts], s=14, marker=MARKERS[cls],
                       color=COLORS[cls], alpha=0.35, linewidths=0)
            best, xs, ys = None, [], []
            for r in pts:
                if is_probe(r["file"]):
                    continue
                if best is None or r["score"] < best:
                    best = r["score"]
                    xs.append(r["time"])
                    ys.append(best)
            if xs:
                xs.append(max(r["time"] for r in rs))
                ys.append(ys[-1])
                ax.step(xs, ys, where="post", color=COLORS[cls], lw=2, label=LABEL_VI[cls])
                ax.annotate(f"{ys[-1]:.3f}", (xs[-1], ys[-1]), xytext=(4, 0), textcoords="offset points",
                            va="center", fontsize=8, color="#333333")
        ax.set_title(f"Track0{track} – điểm tốt nhất theo thời gian (thấp hơn = tốt hơn)", fontsize=10)
        ax.set_ylabel("điểm (m + 0.2·độ)")
        ax.grid(axis="y", color="#e5e5e5", lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=8)
        ax.text(0.01, 0.02, f"baseline TA {base}", transform=ax.transAxes, fontsize=8, color="#666666")
        import matplotlib.dates as md
        ax.xaxis.set_major_formatter(md.DateFormatter("%d/%m"))
        ax.xaxis.set_major_locator(md.DayLocator())
    axes[0].legend(fontsize=8, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(path)


def main():
    rows = load()
    with open(os.path.join(DATA, "submission_stats.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["track", "time_utc+8", "file", "score", "score_exact", "class", "note"])
        for r in rows:
            w.writerow([r["track"], r["time"].strftime("%Y-%m-%d %H:%M"), r["file"],
                        "" if r["score"] is None else r["score"], int(r["exact"]), r["cls"], r["note"]])
    os.makedirs(os.path.join(DOCS, "fig"), exist_ok=True)
    chart(rows, os.path.join(DOCS, "fig", "submission_progress.png"))

    out = ["# 09 – Thống kê các lần nộp Kaggle (tự sinh bằng `tools/submission_stats.py`)", "",
           "Phân loại theo trả lời của TA (20/10, xem [08 §12](08-gicp-va-scale.md)):", "",
           "| Loại | Ý nghĩa | Dùng làm bài chấm? |", "|---|---|---|",
           "| **Pipeline** | chỉ thuật toán (GNSS + Kalman, NDT/GICP, gyro); tham số chọn theo điểm = chỉnh tham số bình thường | ✅ |",
           "| **Lai** | thuật toán chạy trên nền một file có phần chọn theo điểm (vd. GICP khởi tạo từ yaw tổ hợp, "
           "vị trí Track02 tổ hợp) – có thể dựng lại sạch (`clean_*`) | ⚠️ phải dựng lại |",
           "| **Leaderboard** | file dò (`probe_*`, `bump*`) và tổ hợp trọng số theo điểm (`*proj*`, `lb_*`, `corr_*`) | ❌ |",
           "", "Điểm có `*` là điểm Kaggle hiện tại (chỉ 2 chữ số, Kaggle **cắt** bớt chứ không làm tròn); "
           "các điểm khác lấy từ log lúc nộp (5 chữ số). Giờ là UTC+8.", "",
           "![Tiến độ](fig/submission_progress.png)", "",
           "**Nhận xét.** Đường *Lai* (cam) là tiến bộ thuật toán thật (NDT → GICP → tỉ lệ mặt đường → demean → yaw gyro); "
           "nó chỉ \"lai\" vì chạy trên nền file có phần chọn theo điểm. Bản dựng lại sạch của file Lai tốt nhất "
           "(`clean_cfz1_tau7`, `clean_cfz2_tau15`, xem 08 §12) **chưa nộp**, dự kiến ~0.79 / ~0.28 – tức là đường "
           "Pipeline (xanh) sẽ xuống ngang đường cam. Khoảng cách tới đường xanh lá (0.46 / 0.19) là phần đến từ dò "
           "leaderboard, không được tính.", ""]
    for track in ["1", "2"]:
        rs = [r for r in rows if r["track"] == track]
        out += [f"## Track0{track}", "", "| Loại | Số lần nộp | Tốt nhất | File |", "|---|---|---|---|"]
        for cls in ["pipeline", "mixed", "leaderboard", "other"]:
            c = [r for r in rs if r["cls"] == cls]
            sc = [r for r in c if r["score"] is not None]
            b = min(sc, key=lambda r: r["score"]) if sc else None
            out.append(f"| {LABEL_VI[cls]} | {len(c)} | {fmt(b) if b else '–'} | {'`' + b['file'] + '`' if b else ''} |")
        out += ["", "**Các mốc cải thiện** (mỗi dòng là lần một loại đạt điểm tốt hơn; bỏ qua file dò `probe_*`/`bump*` vì chúng cố ý làm lệch):", "",
                "| Thời gian | File | Loại | Điểm | Ghi chú |", "|---|---|---|---|---|"]
        best = {}
        for r in rs:
            if r["score"] is None or r["cls"] == "other" or is_probe(r["file"]):
                continue
            if r["score"] < best.get(r["cls"], 1e9):
                best[r["cls"]] = r["score"]
                out.append(f"| {r['time']:%d/%m %H:%M} | `{r['file']}` | {LABEL_VI[r['cls']].split(' (')[0]} | "
                           f"{fmt(r)} | {r['note']} |")
        out += ["", "<details><summary>Tất cả các lần nộp</summary>", "",
                "| # | Thời gian | File | Loại | Điểm |", "|---|---|---|---|---|"]
        for i, r in enumerate(rs, 1):
            out.append(f"| {i} | {r['time']:%d/%m %H:%M} | `{r['file']}` | {LABEL_VI[r['cls']].split(' (')[0]} | {fmt(r)} |")
        out += ["", "</details>", ""]
    open(os.path.join(DOCS, "09-thong-ke-nop-bai.md"), "w").write("\n".join(out))
    for track in ["1", "2"]:
        n = sum(r["track"] == track for r in rows)
        print(f"Track0{track}: {n} submissions")


if __name__ == "__main__":
    main()
