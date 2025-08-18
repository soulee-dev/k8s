#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from datetime import datetime, timedelta, timezone
from dateutil.tz import gettz
from collections import defaultdict, Counter
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -------- Settings --------
TIMEZONE = gettz(os.environ.get("TZ", "Asia/Seoul"))
DAYS_FOR_BAR = 30               # 최근 30일 바 차트
WEEKS_FOR_HEATMAP = 53          # 53주(약 1년) 잔디
FILE_EXTS = {".md", ".mdx"}     # Markdown만 집계
OUTPUT_DIR = Path("charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------- Git helpers --------
def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()

def list_commits():
    """
    Return list of (hash, committed_iso8601) for all non-merge commits.
    """
    fmt = "%H %cI"
    out = run(["git", "log", "--no-merges", f"--pretty=format:{fmt}"])
    rows = []
    for line in out.splitlines():
        try:
            h, ts = line.split(" ", 1)
            rows.append((h, ts))
        except ValueError:
            pass
    return rows

def commit_touched_markdown(commit_hash: str) -> bool:
    """
    Check if commit touches any *.md / *.mdx file.
    """
    out = run(["git", "show", "--name-only", "--pretty=format:", commit_hash])
    for path in out.splitlines():
        _, ext = os.path.splitext(path.strip())
        if ext.lower() in FILE_EXTS:
            return True
    return False

# -------- Collect per-day commits (KST) --------
commits = list_commits()
md_commits = []
for h, iso in commits:
    if commit_touched_markdown(h):
        dt_utc = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(TIMEZONE)
        md_commits.append((h, dt_local))

# group by local date
by_date = defaultdict(list)
for _, dt in md_commits:
    d = dt.date()
    by_date[d].append(dt)

# compute study duration per day (first to last commit)
# If only one commit, duration = 0 minutes (or set a floor if you prefer)
daily_duration_min = {}
daily_commit_count = {}
for d, times in by_date.items():
    times.sort()
    duration = (times[-1] - times[0]).total_seconds() / 60.0
    daily_duration_min[d] = max(0, round(duration))
    daily_commit_count[d] = len(times)

# -------- Build DataFrame for last N days --------
today_local = datetime.now(TIMEZONE).date()
start_bar = today_local - timedelta(days=DAYS_FOR_BAR - 1)
dates = pd.date_range(start_bar, today_local, freq="D")
bar_df = pd.DataFrame({
    "date": dates.date,
})
bar_df["study_min"] = bar_df["date"].map(lambda d: daily_duration_min.get(d, 0))
bar_df["commits"]   = bar_df["date"].map(lambda d: daily_commit_count.get(d, 0))

# -------- Plot 1: Study time bar (SVG) --------
plt.figure(figsize=(12, 4))
plt.bar(bar_df["date"].astype(str), bar_df["study_min"])
plt.xticks(rotation=60)
plt.title(f"Daily Study Time (first~last Markdown commit, KST) – last {DAYS_FOR_BAR} days")
plt.xlabel("Date")
plt.ylabel("Minutes")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "study_time.svg", format="svg")
plt.close()

# -------- Prepare heatmap data (52–53 weeks like GitHub) --------
# Build date list from oldest Sunday to today (GitHub starts weeks on Sunday)
# Find start date = (today - 7*WEEKS) aligned to Sunday
today_dt = datetime.now(TIMEZONE).date()
start_heat = today_dt - timedelta(weeks=WEEKS_FOR_HEATMAP)
# Align to Sunday
start_heat -= timedelta(days=(start_heat.weekday() + 1) % 7)

all_days = [start_heat + timedelta(days=i) for i in range((today_dt - start_heat).days + 1)]
counts = Counter({d: daily_commit_count.get(d, 0) for d in all_days})

# Heatmap grid: rows=7 (Sun..Sat), cols=weeks
cols = (len(all_days) + 6) // 7
grid = [[0]*cols for _ in range(7)]
for idx, day in enumerate(all_days):
    col = idx // 7
    row = day.weekday() + 1  # Monday=1..Sunday=0; fix to Sunday=0
    row = row % 7
    grid[row][col] = counts[day]

# Normalize to 0..4 "levels"
flat = [c for col in range(cols) for c in [grid[r][col] for r in range(7)]]
mx = max(flat) if flat else 0
def level(c):
    if mx == 0: return 0
    q = c / mx
    if q == 0: return 0
    elif q <= 0.25: return 1
    elif q <= 0.5: return 2
    elif q <= 0.75: return 3
    else: return 4

levels = [[level(grid[r][c]) for c in range(cols)] for r in range(7)]

# -------- Plot 2: Contributions heatmap (SVG) --------
# Simple square grid using matplotlib
cell = 0.4
w = cell * cols + 2
h = cell * 7 + 1.2
plt.figure(figsize=(w, h))
for r in range(7):
    for c in range(cols):
        v = levels[r][c]
        # draw as gray scale; GitHub-like would be greens, but we avoid explicit colors per instructions
        plt.gca().add_patch(plt.Rectangle((c*cell, (6-r)*cell), cell*cell, cell*cell, linewidth=0.2,
                                          edgecolor="black",
                                          facecolor=str(0.9 - 0.18*v)))
plt.xlim(0, cols*cell)
plt.ylim(0, 7*cell)
plt.axis("off")
plt.title("Markdown Commit Heatmap (last ~52 weeks, KST)")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "contributions.svg", format="svg")
plt.close()

# -------- Tiny summary TSV (optional) --------
with open(OUTPUT_DIR / "summary.tsv", "w", encoding="utf-8") as f:
    print("date\tstudy_minutes\tcommits", file=f)
    for _, row in bar_df.iterrows():
        print(f"{row['date']}\t{row['study_min']}\t{row['commits']}", file=f)

print("Charts generated at:", OUTPUT_DIR.resolve())
