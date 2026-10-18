"""Shared look for all chapters: colours, kinetic text, title and summary cards, beat timing."""
import json
import os

from manim import (DOWN, LEFT, RIGHT, UP, BackgroundRectangle, FadeIn, FadeOut, GrowFromCenter, Indicate,
                   LaggedStart, RoundedRectangle, Scene, Text, VGroup, Write, config, rate_functions)

BG = "#101321"
FG = "#F5F5F5"
ACCENT = "#FFD23F"   # key words
BLUE = "#3BCEAC"     # target / map
RED = "#EE4266"      # source / moving cloud
PURPLE = "#8E7DBE"
FONT = "Noto Sans"

config.background_color = BG


def timing(chapter):
    """Narration timing written by lib/tts.py (falls back to 3 s per line for a silent preview)."""
    path = os.path.join(os.environ.get("VIDEO_ROOT", "."), "audio", chapter, "timing.json")
    data = json.load(open(path))
    return [line["dur"] + data["gap"] for line in data["lines"]]


def T(text, size=40, color=FG, weight="NORMAL"):
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


class BeatScene(Scene):
    """A scene whose beats last exactly as long as the narration lines."""
    CHAPTER = ""

    def setup(self):
        self.durs = timing(self.CHAPTER)
        self.beat_i = 0
        self.beat_used = 0.0

    def play(self, *args, **kwargs):
        before = self.renderer.time
        super().play(*args, **kwargs)
        self.beat_used += self.renderer.time - before

    def end_beat(self):
        """Wait out the rest of the current narration line, then start the next beat."""
        left = self.durs[self.beat_i] - self.beat_used
        if left > 0.02:
            self.wait(left)
        self.beat_i += 1
        self.beat_used = 0.0

    # ---- kinetic typography -------------------------------------------------
    def pop_text(self, mob, run_time=0.35):
        self.play(GrowFromCenter(mob), run_time=run_time, rate_func=rate_functions.ease_out_back)

    def caption(self, text, color=ACCENT, size=44, pos=UP * 3.2):
        mob = T(text, size, color, "BOLD").move_to(pos)
        bg = BackgroundRectangle(mob, color=BG, fill_opacity=0.85, buff=0.15)
        group = VGroup(bg, mob)
        self.pop_text(group)
        return group

    def title_card(self, number, title, subtitle=""):
        box = RoundedRectangle(corner_radius=0.3, width=11, height=3, color=ACCENT, stroke_width=4)
        num = T(number, 36, ACCENT, "BOLD").next_to(box.get_top(), DOWN, buff=0.35)
        ttl = T(title, 60, FG, "BOLD").move_to(box.get_center())
        group = VGroup(box, num, ttl)
        if subtitle:
            group.add(T(subtitle, 30, BLUE).next_to(ttl, DOWN, buff=0.25))
        self.play(LaggedStart(FadeIn(box, scale=1.2), Write(num), GrowFromCenter(ttl), lag_ratio=0.3), run_time=1.0)
        if subtitle:
            self.play(FadeIn(group[-1], shift=UP * 0.2), run_time=0.4)
        return group

    def summary_card(self, items):
        head = T("NHỚ 3 Ý NÀY", 52, ACCENT, "BOLD").to_edge(UP, buff=0.8)
        rows = VGroup(*[T(f"{i + 1}. {s}", 34) for i, s in enumerate(items)]).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        rows.next_to(head, DOWN, buff=0.7)
        self.play(GrowFromCenter(head), run_time=0.4)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.4), run_time=0.35)
        return VGroup(head, rows)

    def highlight(self, mob):
        self.play(Indicate(mob, color=ACCENT, scale_factor=1.15), run_time=0.5)

    def clear(self, *mobs, run_time=0.3):
        mobs = [m for m in mobs if m is not None]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)
