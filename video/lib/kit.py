"""Declarative chapters: a list of beats (narration line + what to show) rendered with the shared style.

    BEATS = [
        ("câu đọc", [("title", "1", "Bức tranh lớn", "phụ đề")]),
        ("câu đọc", [("caption", "chữ trên cùng"), ("bullets", ["ý 1", "ý 2"])]),
        ("câu đọc", [("image", "map_top_track1.png", 5.5)]),
        ("câu đọc", [("custom", some_function)]),          # some_function(scene) -> list of mobjects shown
        ...
    ]
Every beat replaces the previous one unless its show-list starts with ("keep",).
Element types: title, big, caption, bullets, image, formula, code, summary, table, note, custom, keep.
"""
import os

from manim import (DOWN, LEFT, RIGHT, UP, Code, FadeIn, GrowFromCenter, ImageMobject, MathTex, Rectangle,
                   UpdateFromAlphaFunc, VGroup, rate_functions)

from style import ACCENT, BLUE, FG, RED, BeatScene, T

ROOT = os.environ.get("VIDEO_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIG = os.path.join(ROOT, "assets", "figures")


def lines_of(beats):
    return [b[0] for b in beats]


def default_sfx(beats):
    """whoosh on the first beat and on title/image beats, pop on text beats, ding on summaries."""
    sfx = {}
    for i, (_, show) in enumerate(beats):
        kinds = {e[0] for e in show}
        if i == 0 or "title" in kinds or "image" in kinds:
            sfx[i] = [("whoosh", 0.0)]
        elif "summary" in kinds:
            sfx[i] = [("ding", 0.3)]
        else:
            sfx[i] = [("pop", 0.0)]
    return sfx


class ScriptScene(BeatScene):
    BEATS = []

    def construct(self):
        shown = []
        for _, show in self.BEATS:
            keep = bool(show) and show[0][0] == "keep"
            if not keep:
                self.clear(*shown)
                shown = []
            for el in show:
                if el[0] == "keep":
                    continue
                shown += self.show_element(el)
            self.end_beat()
        self.wait(0.5)

    # ---- element renderers ---------------------------------------------------------------
    def show_element(self, el):
        kind, args = el[0], el[1:]
        return getattr(self, "el_" + kind)(*args)

    def el_title(self, number, title, subtitle=""):
        return [self.title_card(number, title, subtitle)]

    def el_big(self, text, sub=None, color=ACCENT, size=90):
        big = T(text, size, color, "BOLD")
        if big.width > 13.4:
            big.scale_to_fit_width(13.4)
        group = [big]
        if sub:
            s = T(sub, 40, FG).next_to(big, DOWN, buff=0.45)
            if s.width > 13.4:
                s.scale_to_fit_width(13.4)
            VGroup(big, s).move_to(0)
            group.append(s)
        self.pop_text(big)
        if sub:
            self.play(FadeIn(group[1], shift=UP * 0.3), run_time=0.4)
        self.highlight(big)
        return group

    def el_caption(self, text, color=ACCENT):
        return [self.caption(text, color=color)]

    def el_bullets(self, items, size=36, top=2.2, colors=None):
        """Items appear one after another, spread over the narration line."""
        rows = VGroup(*[T(s, size, (colors or {}).get(i, FG)) for i, s in enumerate(items)])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        if rows.width > 13:
            rows.scale_to_fit_width(13)
        rows.move_to(UP * (top - rows.height / 2))
        left = self.durs[self.beat_i] - self.beat_used - 0.3
        step = max(0.35, left / (len(items) + 0.5))
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.4), run_time=0.3, rate_func=rate_functions.ease_out_back)
            if step > 0.35:
                self.wait(step - 0.3)
                self.beat_used += step - 0.3
        return [rows]

    def el_image(self, name, height=5.4, shift=DOWN * 0.3):
        img = ImageMobject(os.path.join(FIG, name))
        img.height = height
        if img.width > 13.4:
            img.width = 13.4
        img.shift(shift)
        frame = Rectangle(width=img.width + 0.1, height=img.height + 0.1, color=FG, stroke_width=2).move_to(img)
        img.set_opacity(0)
        self.add(img)
        self.play(self.image_fade(img, True), FadeIn(frame), run_time=0.6)
        left = self.durs[self.beat_i] - self.beat_used - 0.1
        if left > 1.0:  # slow zoom (Ken Burns), done with an updater so the pixel array is not interpolated
            h0, fh, fw = img.height, frame.height, frame.width

            def zoom(m, alpha):
                m.height = h0 * (1 + 0.04 * alpha)

            def zoom_frame(m, alpha):
                m.stretch_to_fit_height(fh * (1 + 0.04 * alpha))
                m.stretch_to_fit_width(fw * (1 + 0.04 * alpha))

            self.play(UpdateFromAlphaFunc(img, zoom), UpdateFromAlphaFunc(frame, zoom_frame), run_time=left - 0.3,
                      rate_func=rate_functions.linear)
        return [img, frame]

    def el_formula(self, tex, size=48, pos=DOWN * 0.3):
        f = MathTex(tex, font_size=size, color=FG).move_to(pos)
        if f.width > 13:
            f.scale_to_fit_width(13)
        self.play(FadeIn(f, shift=UP * 0.2), run_time=0.6)
        self.highlight(f)
        return [f]

    def el_code(self, code, language="cpp", size=20, pos=DOWN * 0.4):
        c = Code(code=code, language=language, font="Noto Sans Mono", font_size=size, background="window",
                 insert_line_no=False, style="monokai", tab_width=4)
        if c.width > 13:
            c.scale_to_fit_width(13)
        if c.height > 5.6:
            c.scale_to_fit_height(5.6)
        c.move_to(pos)
        self.play(FadeIn(c, shift=UP * 0.2), run_time=0.6)
        return [c]

    def el_summary(self, items):
        return [self.summary_card(items)]

    def el_note(self, text, color=BLUE, size=30, pos=DOWN * 3.2):
        n = T(text, size, color).move_to(pos)
        if n.width > 13.4:
            n.scale_to_fit_width(13.4)
        self.play(FadeIn(n, shift=UP * 0.2), run_time=0.4)
        return [n]

    def el_table(self, rows, size=26, col_gap=0.6, top=2.3):
        cols = len(rows[0])
        cells = [[T(str(c), size, ACCENT if r == 0 else FG, "BOLD" if r == 0 else "NORMAL") for c in row]
                 for r, row in enumerate(rows)]
        widths = [max(cells[r][c].width for r in range(len(rows))) for c in range(cols)]
        y = top
        group = VGroup()
        total = sum(widths) + col_gap * (cols - 1)
        for r, row in enumerate(cells):
            x = -total / 2
            h = max(c.height for c in row)
            for c, cell in enumerate(row):
                cell.move_to([x + cell.width / 2, y - h / 2, 0])
                x += widths[c] + col_gap
                group.add(cell)
            y -= h + 0.3
        if group.width > 13.4:
            group.scale_to_fit_width(13.4)
        for r in range(len(rows)):
            row = VGroup(*group[r * cols:(r + 1) * cols])
            self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.25)
        return [group]

    def el_custom(self, fn):
        return list(fn(self))
