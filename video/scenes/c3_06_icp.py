"""Chương 3.6 – ICP (Iterative Closest Point). ICP steps are computed for real with numpy."""
import os
import sys

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Arrow, BackgroundRectangle, Create, Cross, DashedLine, Dot, FadeIn,
                   FadeOut, Line, MathTex, Transform, VGroup)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from style import ACCENT, BG, BLUE, FG, PURPLE, RED, BeatScene, T  # noqa: E402

CHAPTER = "c3_06_icp"

LINES = [
    "Giờ tới món chính: scan matching – khớp hai đám điểm.",
    "Thuật toán kinh điển nhất là ICP, viết tắt của Iterative Closest Point.",
    "Tưởng tượng hai tấm bản đồ in trên giấy kính, đặt chồng lên nhau, lệch một chút.",
    "Bước một: với mỗi điểm trên tấm trên, tìm điểm gần nhất trên tấm dưới. Gọi là ghép cặp, correspondence.",
    "Bước hai: tính phép xoay và phép dịch làm các cặp đó sát nhau nhất.",
    "Bước ba: dời tấm trên theo phép đó. Rồi lặp lại, tới khi nó không nhúc nhích nữa.",
    "Có hai kiểu. Point-to-point: kéo điểm về điểm. Point-to-plane: kéo điểm về mặt phẳng gần nhất, "
    "thường hội tụ nhanh hơn trên tường và mặt đường.",
    "Điểm yếu: ICP chỉ tìm được cực tiểu gần nhất. Đặt lệch quá xa lúc đầu là nó khớp sai, mà vẫn rất tự tin là mình đúng.",
    "Vì vậy điểm xuất phát, initial guess, cực kỳ quan trọng.",
    "Lưu ý: bài của mình chưa dùng ICP. Mình dùng NDT, món tiếp theo.",
]

# Sound effects per beat: (name, offset in seconds; negative = from the end of the beat).
SFX = {0: [("whoosh", 0.0), ("pop", 0.9)], 1: [("pop", 0.0)], 2: [("whoosh", 0.0)], 3: [("pop", 0.0)],
       4: [("pop", 0.0)], 5: [("pop", 0.0), ("ding", -0.8)], 6: [("whoosh", 0.0)], 7: [("pop", 0.0)],
       8: [("ding", 0.2)], 9: [("pop", 0.0)]}

# Demo set-up (checked numerically: the first converges, the second stops at a visibly wrong pose).
GOOD_START_DEG, GOOD_SHIFT, GOOD_ITERS = -12.0, (0.5, -0.3), 10
BAD_START_DEG, BAD_ITERS = 50.0, 30


# ---------------------------------------------------------------- ICP maths
def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def polyline(points, step):
    out = []
    for a, b in zip(points, points[1:]):
        a, b = np.array(a, float), np.array(b, float)
        n = max(2, int(np.linalg.norm(b - a) / step))
        out += [a + (b - a) * k / n for k in range(n)]
    out.append(np.array(points[-1], float))
    return np.array(out)


def icp_step(src, dst):
    """One point-to-point ICP iteration: nearest neighbours, then the best rotation + translation (SVD)."""
    d = np.linalg.norm(src[:, None, :] - dst[None, :, :], axis=2)
    idx = d.argmin(axis=1)
    q = dst[idx]
    cs, cq = src.mean(0), q.mean(0)
    U, _, Vt = np.linalg.svd((src - cs).T @ (q - cq))
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    t = cq - R @ cs
    return R, t, idx, d[np.arange(len(src)), idx].mean()


def run_icp(src, dst, iters):
    states, cur = [src.copy()], src.copy()
    errs, idxs = [], []
    for _ in range(iters):
        R, t, idx, err = icp_step(cur, dst)
        idxs.append(idx)
        errs.append(err)
        cur = cur @ R.T + t
        states.append(cur.copy())
    return states, idxs, errs


def street():
    """A street corner seen from above: building walls, a kerb and a lamp post."""
    walls = polyline([(-3.2, 1.7), (0.6, 1.7), (0.6, 0.5), (2.8, 0.5)], 0.22)
    kerb = polyline([(-3.2, -1.2), (1.4, -1.2), (2.1, -1.9)], 0.25)
    pole = np.array([[1.9, -0.4], [2.0, -0.35], [1.95, -0.5]])
    return np.vstack([walls, kerb, pole])


# ---------------------------------------------------------------- drawing helpers
S, O = 0.95, LEFT * 0.3 + DOWN * 0.35   # plot scale and origin on screen


def to_screen(p):
    return O + S * np.array([p[0], p[1], 0.0])


def dots(points, color, radius=0.055):
    return VGroup(*[Dot(to_screen(p), radius=radius, color=color) for p in points])


def move_dots(group, points):
    return [d.animate.move_to(to_screen(p)) for d, p in zip(group, points)]


def links(src_points, tgt_points, idx):
    return VGroup(*[Line(to_screen(src_points[i]), to_screen(tgt_points[j]), stroke_width=1.5, color=PURPLE)
                    for i, j in enumerate(idx)])


class C3_06_ICP(BeatScene):
    CHAPTER = CHAPTER

    def construct(self):
        rng = np.random.default_rng(0)
        target = street()
        source = target @ rot(np.radians(GOOD_START_DEG)).T + np.array(GOOD_SHIFT) + rng.normal(0, 0.03, target.shape)
        states, idxs, errs = run_icp(source, target, GOOD_ITERS)

        # 0 – hook
        card = self.title_card("3.6", "ICP", "khớp hai đám điểm")
        self.end_beat()

        # 1 – name
        self.clear(card)
        big = T("ICP", 120, ACCENT, "BOLD").shift(UP * 0.6)
        sub = T("Iterative Closest Point", 44, FG).next_to(big, DOWN, buff=0.4)
        self.pop_text(big)
        self.play(FadeIn(sub, shift=UP * 0.3), run_time=0.4)
        self.highlight(big)
        self.end_beat()

        # 2 – two transparent sheets
        self.clear(big, sub)
        cap = self.caption("ICP = ghép 2 tấm giấy kính")
        tgt = dots(target, BLUE)
        src = dots(source, RED)
        legend = VGroup(T("● tấm dưới: bản đồ", 24, BLUE), T("● tấm trên: point cloud", 24, RED))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_corner(UP + LEFT, buff=0.4).shift(DOWN * 0.9)
        self.play(FadeIn(tgt, lag_ratio=0.02), FadeIn(legend[0]), run_time=0.8)
        self.play(FadeIn(src, lag_ratio=0.02, shift=UP * 0.3), FadeIn(legend[1]), run_time=0.8)
        self.end_beat()

        # 3 – correspondences
        cap2 = self.caption("1. tìm điểm gần nhất")
        self.remove(cap)
        lk = links(states[0], target, idxs[0])
        self.play(Create(lk, lag_ratio=0.02), run_time=1.2)
        self.end_beat()

        # 4 – solve R, t
        cap3 = self.caption("2. tính R, t")
        self.remove(cap2)
        formula = MathTex(r"\min_{R,\,t}\ \sum_i \lVert R\,p_i + t - q_i \rVert^2", font_size=40, color=FG)
        formula.to_edge(DOWN, buff=0.35)
        box = BackgroundRectangle(formula, color=BG, fill_opacity=0.92, buff=0.2)
        self.play(FadeIn(box), FadeIn(formula, shift=UP * 0.2), run_time=0.6)
        self.highlight(formula)
        self.end_beat()

        # 5 – iterate until it stops moving
        cap4 = self.caption("3. dời & lặp lại")
        self.remove(cap3)
        counter = T(f"vòng 1 · sai số TB {errs[0]:.2f}", 28, ACCENT).to_corner(UP + RIGHT, buff=0.4).shift(DOWN * 0.9)
        self.play(FadeIn(counter), FadeOut(formula), FadeOut(box), run_time=0.3)
        for k in range(1, len(states)):
            nxt = links(states[k], target, idxs[k] if k < len(idxs) else idxs[-1])
            err_k = errs[k] if k < len(errs) else errs[-1]
            txt = T(f"vòng {k + 1} · sai số TB {err_k:.2f}", 28, ACCENT).move_to(counter)
            self.play(*move_dots(src, states[k]), Transform(lk, nxt), Transform(counter, txt),
                      run_time=0.6 if k < 4 else 0.3)
        self.play(FadeOut(lk), run_time=0.3)
        ok = T("ĐÃ KHỚP – không nhúc nhích nữa", 32, BLUE, "BOLD").to_edge(DOWN, buff=0.4)
        self.pop_text(ok)
        self.end_beat()

        # 6 – point-to-point vs point-to-plane
        self.clear(cap4, counter, ok, tgt, src, legend)
        titles = VGroup(T("point-to-point", 34, RED, "BOLD").move_to(LEFT * 3.5 + UP * 2.6),
                        T("point-to-plane", 34, BLUE, "BOLD").move_to(RIGHT * 3.5 + UP * 2.6))
        divider = DashedLine(UP * 3, DOWN * 3, color=FG, stroke_opacity=0.4)
        panels = VGroup()
        direction = np.array([1.0, -0.25, 0.0]) / np.linalg.norm([1.0, -0.25])
        normal = np.array([0.25, 1.0, 0.0]) / np.linalg.norm([0.25, 1.0])
        for cx, plane in ((-3.5, False), (3.5, True)):
            c = np.array([cx, 0.0, 0])
            wall_pts = [c + direction * s for s in (-2.4, -1.2, 0.0, 1.2, 2.4)]   # sparse samples of a wall
            surface = Line(wall_pts[0] - direction * 0.4, wall_pts[-1] + direction * 0.4, color=BLUE,
                           stroke_opacity=0.6, stroke_width=3)
            wall = VGroup(*[Dot(p, radius=0.08, color=BLUE) for p in wall_pts])
            p = c + direction * 0.6 + normal * 1.5                                 # between two samples
            pdot = Dot(p, radius=0.1, color=RED)
            if plane:
                end = p - np.dot(p - c, normal) * normal                           # foot of the perpendicular
                note = T("vuông góc xuống bề mặt", 24, ACCENT)
            else:
                end = min(wall_pts, key=lambda q: np.linalg.norm(q - p))           # nearest sample point
                note = T("về điểm mẫu gần nhất", 24, ACCENT)
            arrow = Arrow(p, end, buff=0.08, color=ACCENT, stroke_width=5, max_tip_length_to_length_ratio=0.2)
            note.next_to(pdot, UP, buff=0.25)
            panels.add(VGroup(surface, wall, pdot, arrow, note))
        self.play(FadeIn(titles), Create(divider), run_time=0.5)
        self.play(FadeIn(panels[0], lag_ratio=0.1), run_time=0.8)
        self.play(FadeIn(panels[1], lag_ratio=0.1), run_time=0.8)
        tag = T("thường hội tụ nhanh hơn\ntrên tường, mặt đường", 26, BLUE).move_to(RIGHT * 3.5 + DOWN * 2.3)
        self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.4)
        self.end_beat()

        # 7 – local minimum: a start that is too far off converges to a wrong pose and stops there
        self.clear(titles, divider, panels, tag)
        cap5 = self.caption("Cẩn thận: cực tiểu cục bộ")
        bad_src = target @ rot(np.radians(BAD_START_DEG)).T
        bad_states, _, bad_errs = run_icp(bad_src, target, BAD_ITERS)
        bt = dots(target, BLUE, radius=0.07)
        bs = dots(bad_states[0], RED, radius=0.045)
        start_note = T(f"xuất phát lệch {BAD_START_DEG:.0f}°", 28, RED).to_corner(UP + RIGHT, buff=0.4).shift(DOWN * 0.9)
        self.play(FadeIn(bt), FadeIn(bs), FadeIn(start_note), run_time=0.6)
        for k in range(1, len(bad_states), 3):
            self.play(*move_dots(bs, bad_states[k]), run_time=0.22)
        claim = T(f"đứng yên ở sai số {bad_errs[-1]:.2f} – nhưng khớp SAI", 30, ACCENT, "BOLD").to_edge(DOWN, buff=0.35)
        cross = Cross(bs, stroke_color=RED, stroke_width=6).scale(0.6)
        self.play(FadeIn(claim, shift=UP * 0.2), Create(cross), run_time=0.6)
        self.end_beat()

        # 8 – initial guess
        self.clear(cap5, bt, bs, start_note, claim, cross)
        ig = T("INITIAL GUESS", 90, ACCENT, "BOLD")
        sub2 = T("điểm xuất phát quyết định tất cả", 38).next_to(ig, DOWN, buff=0.5)
        self.pop_text(ig)
        self.play(FadeIn(sub2, shift=UP * 0.3), run_time=0.4)
        self.highlight(ig)
        self.end_beat()

        # 9 – honesty note
        self.clear(ig, sub2)
        note1 = T("Bài của mình: chưa dùng ICP", 46, FG, "BOLD").shift(UP * 0.6)
        note2 = T("→ dùng NDT (phần tiếp theo)", 42, BLUE).next_to(note1, DOWN, buff=0.5)
        self.pop_text(note1)
        self.play(FadeIn(note2, shift=RIGHT * 0.4), run_time=0.4)
        self.end_beat()
        self.wait(0.5)
