#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from datetime import datetime, timedelta
from dateutil.tz import gettz
from collections import defaultdict, Counter
from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ---------------- Settings ----------------
TIMEZONE = gettz(os.environ.get("TZ", "Asia/Seoul"))
FILE_EXTS = {".md", ".mdx"}        # 집계 대상
DAYS_FOR_BAR = 30                   # 공부시간 차트 기간
WEEKS_FOR_HEATMAP = 53              # 잔디 기간(약 1년)
OUTPUT_DIR = Path("charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# GitHub 잔디 팔레트
GRASS_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

mpl.rcParams.update({
    "figure.dpi": 144,
    "font.size": 11,
    "axes.grid": True,
    "grid.color": "#e5e7eb",
    "grid.linewidth": 0.8,
    "axes.edgecolor": "#e5e7eb",
    "axes.titleweight": "semibold",
    "axes.labelcolor": "#111827",
    "text.color": "#111827",
    "xtick.color": "#374151",
    "ytick.color": "#374151",
})

# ---------------- Git helpers ----------------
def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()

def list_commits():
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
    out = run(["git", "show", "--name-only", "--pretty=format:", commit_hash])
    for path in out.splitlines():
        if not path.strip():
            continue
        _, ext = os.path.splitext(path.strip())
        if ext.lower() in FILE_EXTS:
            return True
    return False

# ---------------- Collect data ----------------
commits = list_commits()
md_commits = []
for h, iso in commits:
    if commit_touched_markdown(h):
        dt_utc = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(TIMEZONE)
        md_commits.append((h, dt_local))

# 일자별 첫/마지막 커밋, 커밋 수
by_date = defaultdict(list)
for _, dt in md_commits:
    by_date[dt.date()].append(dt)

daily_duration_min = {}
daily_commit_count = {}
for d, times in by_date.items():
    times.sort()
    dur = (times[-1] - times[0]).total_seconds() / 60.0
    daily_duration_min[d] = max(0, round(dur))
    daily_commit_count[d] = len(times)

# ---------------- Study time dataframe ----------------
today_local = datetime.now(TIMEZONE).date()
start_bar = today_local - timedelta(days=DAYS_FOR_BAR - 1)
dates = pd.date_range(start_bar, today_local, freq="D")
bar_df = pd.DataFrame({"date": dates.date})
bar_df["study_min"] = bar_df["date"].map(lambda d: daily_duration_min.get(d, 0))
bar_df["commits"]   = bar_df["date"].map(lambda d: daily_commit_count.get(d, 0))

# 부드러운 곡선을 위한 이동평균(7일)
def smooth(series, window=7):
    if len(series) == 0:
        return series
    return pd.Series(series).rolling(window=window, min_periods=1, center=True).mean().values

bar_df["study_min_smooth"] = smooth(bar_df["study_min"], window=7)

# ---------------- Plot 1: Pretty study time ----------------
fig, ax1 = plt.subplots(figsize=(12, 4.8))
# 주말 영역 음영
for i, d in enumerate(bar_df["date"]):
    if pd.Timestamp(d).weekday() >= 5:
        ax1.axvspan(i - 0.5, i + 0.5, color="#f9fafb", zorder=0)

# 막대(분) + 부드러운 라인(분)
bar = ax1.bar(range(len(bar_df)), bar_df["study_min"], width=0.8, color="#93c5fd", edgecolor="#60a5fa", linewidth=0.5, label="Study minutes")
ax1.plot(range(len(bar_df)), bar_df["study_min_smooth"], linewidth=2.2, color="#1d4ed8", label="7d avg (min)")

ax1.set_title(f"Daily Study Time (first~last Markdown commit, KST) – last {DAYS_FOR_BAR} days")
ax1.set_ylabel("Minutes")

# 보조축: 커밋 수 (점/선)
ax2 = ax1.twinx()
ax2.plot(range(len(bar_df)), bar_df["commits"], marker="o", markersize=3.5, linewidth=1.4, color="#10b981", label="Commits")
ax2.set_ylabel("Commits")

# x축 라벨: 날짜 간격 줄이기
tick_idx = np.linspace(0, len(bar_df)-1, num=min(10, len(bar_df))).astype(int)
ax1.set_xticks(tick_idx)
ax1.set_xticklabels([pd.Timestamp(bar_df["date"].iloc[i]).strftime("%m/%d") for i in tick_idx], rotation=0)

# 범례 깔끔하게 묶기
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, loc="upper left", ncols=3)

fig.tight_layout()
fig.savefig(OUTPUT_DIR / "study_time.svg", format="svg")
plt.close(fig)

# ---------------- Heatmap data ----------------
# 시작일(일요일 정렬) ~ 오늘
start_heat = today_local - timedelta(weeks=WEEKS_FOR_HEATMAP)
start_heat -= timedelta(days=(start_heat.weekday() + 1) % 7)  # Sunday align
all_days = [start_heat + timedelta(days=i) for i in range((today_local - start_heat).days + 1)]
counts = Counter({d: daily_commit_count.get(d, 0) for d in all_days})

cols = (len(all_days) + 6) // 7
grid = [[0]*cols for _ in range(7)]
for idx, day in enumerate(all_days):
    col = idx // 7
    row = (day.weekday() + 1) % 7  # Sunday=0
    grid[row][col] = counts[day]

# 등급 기준: 최댓값 기반 대신 분위수(0, .25, .5, .75)로 잘라서 outlier 영향 축소
flat = [grid[r][c] for c in range(cols) for r in range(7)]
mx = max(flat) if flat else 0
if mx == 0:
    thresholds = [0, 1, 2, 3]  # 아무 커밋 없을 때
else:
    q1, q2, q3 = np.quantile([v for v in flat if v > 0], [0.25, 0.5, 0.75]) if any(v>0 for v in flat) else (1,2,3)
    thresholds = [q1, q2, q3]

def to_level(v: int) -> int:
    if v <= 0: return 0
    if v <= thresholds[0]: return 1
    if v <= thresholds[1]: return 2
    if v <= thresholds[2]: return 3
    return 4

levels = [[to_level(grid[r][c]) for c in range(cols)] for r in range(7)]

# ---------------- Plot 2: GitHub-like green grass ----------------
cell = 0.42
pad_x = 1.5
pad_y = 1.2
fig_w = cell * cols + pad_x
fig_h = cell * 7 + pad_y
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_axis_off()

# 셀 그리기 (라운드 느낌: 얇은 테두리 + 약간의 간격)
for r in range(7):
    for c in range(cols):
        lv = levels[r][c]
        color = GRASS_COLORS[lv]
        rect = Rectangle((c*cell, (6-r)*cell), cell*0.95, cell*0.95,
                         linewidth=0.25, edgecolor="#d1d5db", facecolor=color)
        ax.add_patch(rect)

# 월 라벨: 각 월의 첫 번째 열 위에 표시
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
month_seen = set()
for idx, day in enumerate(all_days):
    if day.day == 1:
        c = idx // 7
        if c not in month_seen:
            month_seen.add(c)
            ax.text(c*cell, 7*cell + 0.15, month_names[day.month-1], fontsize=10, va="bottom", ha="left", color="#111827")

# 요일 라벨(간소화: Mon, Wed, Fri)
for r, label in [(6-1, "Mon"), (6-3, "Wed"), (6-5, "Fri")]:
    ax.text(-0.6, r*cell + cell*0.2, label, fontsize=9, ha="right", va="center", color="#6b7280")

# 제목
ax.text(0, 7*cell + 0.6, "Markdown Commit Heatmap (last ~52 weeks, KST)", fontsize=12, fontweight="semibold", ha="left")

# 범례(색상 샘플)
legend_x = cols*cell - 4*cell
ax.text(legend_x - 0.4, -0.9, "Less", fontsize=9, color="#6b7280")
for i, col in enumerate(GRASS_COLORS):
    rect = Rectangle((legend_x + i*cell*0.65, -1.05), cell*0.55, cell*0.55, facecolor=col, edgecolor="#d1d5db", linewidth=0.25)
    ax.add_patch(rect)
ax.text(legend_x + 4*cell*0.65 + 0.1, -0.9, "More", fontsize=9, color="#6b7280")

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "contributions.svg", format="svg", bbox_inches="tight")
plt.close(fig)

# ---------------- Summary file ----------------
with open(OUTPUT_DIR / "summary.tsv", "w", encoding="utf-8") as f:
    print("date\tstudy_minutes\tcommits", file=f)
    for _, row in bar_df.iterrows():
        print(f"{row['date']}\t{row['study_min']}\t{row['commits']}", file=f)

print("Pretty charts generated at:", OUTPUT_DIR.resolve())
