"""Regenerate figures/*.png from results/*.json. Usage: python3 tools/make_charts.py"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RES, FIG = ROOT / "results", ROOT / "figures"
FIG.mkdir(exist_ok=True)
BLUE, ORANGE, GRAY = "#2b6cb0", "#dd6b20", "#718096"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def ppo_curve():
    d = json.load(open(RES / "ppo_curve.json"))["curve"]
    x = [r["iteration"] for r in d]
    y = [r["vs_il_winrate"] * 100 for r in d]
    lo = [r["vs_il_winrate"] * 100 - r["vs_il_ci95"][0] * 100 for r in d]
    hi = [r["vs_il_ci95"][1] * 100 - r["vs_il_winrate"] * 100 for r in d]
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    ax.axhline(50, color=GRAY, ls="--", lw=1)
    ax.errorbar(x, y, yerr=[lo, hi], color=BLUE, marker="o", capsize=4, lw=2)
    for xi, yi in zip(x, y):
        ax.text(xi + 0.4, yi - 2.6, f"{yi:.1f}%", ha="left")
    ax.set_xticks(x)
    ax.set_xlabel("PPO iteration")
    ax.set_ylabel("Win rate vs. IL baseline (%)")
    ax.set_ylim(35, 85)
    ax.set_title("Self-play RL vs. imitation baseline (200 games each, 95% CI)")
    fig.tight_layout()
    fig.savefig(FIG / "ppo_curve.png")
    plt.close(fig)


def online():
    d = json.load(open(RES / "online_play.json"))
    seg = [s for s in d["by_opponent_trophies"] if s["bucket"] != "unknown" and s["games"]]
    labels = [s["bucket"] for s in seg]
    rates = [s["winrate"] * 100 for s in seg]
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    bars = ax.bar(labels, rates, color=ORANGE)
    for b, s in zip(bars, seg):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{s['wins']}/{s['games']}", ha="center", fontsize=10)
    ov = d["overall"]
    ax.axhline(ov["winrate"] * 100, color=GRAY, ls="--", lw=1)
    ax.set_ylim(0, 118)
    ax.text(0.99, 0.97, f"overall {ov['winrate']*100:.1f}% ({ov['wins']}/{ov['games']}, dashed line)", transform=ax.transAxes, ha="right", va="top", color=GRAY, fontsize=10)
    ax.set_xlabel("Opponent trophies (games with known trophies)")
    ax.set_ylabel("Win rate (%)")
    ax.set_title("Online games by opponent trophy range")
    fig.tight_layout()
    fig.savefig(FIG / "online_by_trophies.png")
    plt.close(fig)


def perf():
    d = json.load(open(RES / "performance.json"))
    fig, ax = plt.subplots(figsize=(5.5, 3.6), dpi=150)
    v = [d["cpu_seconds_per_game_before"], d["cpu_seconds_per_game_after"]]
    bars = ax.bar(["before", "after"], v, color=[GRAY, BLUE], width=0.5)
    for b, val in zip(bars, v):
        ax.text(b.get_x() + b.get_width() / 2, val + 0.3, f"{val:g} s", ha="center")
    ax.set_ylabel("CPU seconds per game")
    ax.set_ylim(0, 17)
    ax.set_title(f"Per-game CPU cost ({d['overall_speedup']}x overall)")
    fig.tight_layout()
    fig.savefig(FIG / "cpu_per_game.png")
    plt.close(fig)


def official_ppo():
    d = json.load(open(RES / "official_ppo.json"))
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=150)
    ax.axhline(50, color=GRAY, ls="--", lw=1)
    cols = {"official-ppo3": BLUE, "official-ppo4": ORANGE, "official-ppo5": "#2f855a"}
    pos = 0
    ticks, labels = [], []
    for run, rows in d["interim"].items():
        rows = [r for r in rows if r["opponent"] == "start_checkpoint"]
        for r in rows:
            y = r["winrate"] * 100
            ax.errorbar(pos, y, yerr=[[y - r["ci95"][0] * 100], [r["ci95"][1] * 100 - y]], fmt="o", color=cols[run], capsize=4)
            ax.text(pos, r["ci95"][1] * 100 + 1.2, f"{y:.1f}", ha="center", fontsize=9)
            ticks.append(pos); labels.append(f"{run[-4:].upper()}\nit {r['iteration']}")
            pos += 1
        f = d["final_vs_start"].get(run)
        if f:
            y = f["winrate"] * 100
            ax.errorbar(pos, y, yerr=[[y - f["ci95"][0] * 100], [f["ci95"][1] * 100 - y]], fmt="s", color=cols[run], capsize=4, mfc="white")
            ax.text(pos, f["ci95"][1] * 100 + 1.2, f"{y:.1f}", ha="center", fontsize=9)
            ticks.append(pos); labels.append(f"{run[-4:].upper()}\nfinal"); pos += 1
        pos += 0.6
    ax.set_xticks(ticks); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(38, 68)
    ax.set_ylabel("Win rate vs. start checkpoint (%)")
    ax.set_title("Official-contract PPO: no run separates from its start (circle 200 games, square 400)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "official_ppo.png")
    plt.close(fig)


def rollout():
    d = json.load(open(RES / "rollout_profile.json"))
    rows = sorted(d["breakdown_seconds"], key=lambda r: r[1])
    tot = sum(r[1] for r in rows)
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
    cols = [ORANGE if r[0].startswith("State-integrity") else (GRAY if r[0] == "Game-logic tick" else BLUE) for r in rows]
    ax.barh([r[0] for r in rows], [r[1] for r in rows], color=cols)
    for i, r in enumerate(rows):
        ax.text(r[1] + 0.1, i, f"{r[1]:.2f} s ({r[1] / tot * 100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(0, 10.5)
    ax.set_xlabel("Seconds per game (one 4042-tick game, total %.1f s)" % tot)
    ax.set_title("Where one rollout game spends its time")
    fig.tight_layout()
    fig.savefig(FIG / "rollout_breakdown.png")
    plt.close(fig)


def cfv():
    d = json.load(open(RES / "cfv_roots.json"))
    rows = d["rows"]
    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=150)
    ax.axhline(0, color=GRAY, lw=1)
    for i, r in enumerate(rows):
        c = BLUE if r["group"] == "drop" else ORANGE
        y = r["delta"]
        ax.errorbar(i, y, yerr=[[y - r["ci95"][0]], [r["ci95"][1] - y]], fmt="o" if r["confirmed"] else "o", color=c, mfc=c if r["confirmed"] else "white", capsize=3)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([f"{r['root']:03d}" for r in rows], fontsize=8, rotation=90)
    ax.set_xlabel("Root (filled = lower CI bound > 0; blue = key position, orange = negative control)")
    ax.set_ylabel("Paired win difference (B - A), 64 pairs")
    ax.set_title(f"IN PROGRESS: {d['completed_roots']} of {d['planned_roots']} roots complete (95% CI, uncorrected)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "cfv_roots.png")
    plt.close(fig)


if __name__ == "__main__":
    ppo_curve(); online(); perf(); official_ppo(); rollout(); cfv()
