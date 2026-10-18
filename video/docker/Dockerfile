# Render environment for the lecture video: Manim CE + LaTeX + ffmpeg + edge-tts.
# Emoji come from Symbola (outline glyphs): Manim turns text into vector paths and cannot draw color emoji fonts.
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg build-essential pkg-config libcairo2-dev libpango1.0-dev \
        texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science \
        dvisvgm cm-super fonts-noto-core fonts-symbola \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --default-timeout=120 --retries 10 manim==0.18.1 edge-tts==7.3.1 numpy==1.26.4 matplotlib==3.8.4 scipy==1.13.1 pillow==10.4.0

WORKDIR /work
