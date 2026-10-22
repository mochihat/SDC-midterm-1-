"""Pad a partial causal run (first N frames) to all frames by holding the last pose (for a public-leaderboard check
of the first part only; the padding is a constant hold, not a correction). Usage: pad_track.py IN.csv N_FRAMES OUT.csv"""
import sys
rows = [l.strip() for l in open(sys.argv[1]) if l.strip()]
head, body = rows[0], rows[1:]
n = int(sys.argv[2])
last = body[-1].split(",")
with open(sys.argv[3], "w") as f:
    f.write(head + "\n")
    for r in body:
        f.write(r + "\n")
    for i in range(len(body), n):
        f.write(f"{i},{last[1]},{last[2]},{last[3]}\n")
print(f"{sys.argv[3]}: {len(body)} frames + {n - len(body)} held")
