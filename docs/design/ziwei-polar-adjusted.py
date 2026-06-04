import numpy as np
import matplotlib.pyplot as plt


BG = "#F4F3F0"
COLOR_SOLID = "#96928A"
COLOR_HOLLOW = BG
COLOR_LINE = "#A9A59D"
COLOR_DASH = "#D6D2CA"


fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": "polar"})
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.grid(False)
ax.set_yticklabels([])
ax.set_xticklabels([])
ax.spines["polar"].set_visible(False)

# 让 90 度在正上方，方向按常见视觉稿顺时针排布，方便对照原图。
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)


def draw_arc_nodes(r, start_deg, end_deg, num_nodes, is_hollow=False, size=150, lw=1.55):
    if end_deg < start_deg:
        end_deg += 360
    angles = np.linspace(np.radians(start_deg), np.radians(end_deg), num_nodes)
    rs = np.full_like(angles, r)
    if num_nodes > 1:
        ax.plot(angles, rs, color=COLOR_LINE, linewidth=lw, zorder=1)
    ax.scatter(
        angles,
        rs,
        s=size,
        facecolors=COLOR_HOLLOW if is_hollow else COLOR_SOLID,
        edgecolors=COLOR_SOLID,
        linewidths=2.4,
        zorder=2,
    )


def draw_single_node(r, deg, is_hollow=False, size=150):
    draw_arc_nodes(r, deg, deg, 1, is_hollow=is_hollow, size=size)


def draw_spoke(deg, r0, r1):
    rad = np.radians(deg)
    ax.plot([rad, rad], [r0, r1], color=COLOR_LINE, linewidth=1.45, zorder=1)


theta = np.linspace(0, 2 * np.pi, 360)
ax.plot(theta, np.full_like(theta, 4.02), color=COLOR_DASH, linestyle=(0, (5, 8)), linewidth=1.2, alpha=0.9)
ax.plot(theta, np.full_like(theta, 1.68), color=COLOR_LINE, linewidth=1.0, alpha=0.88)

# 第一层：中心十字星点。
ax.scatter([0], [0], s=165, color=COLOR_SOLID, zorder=3)
for deg in [35, 145, 215, 325]:
    draw_spoke(deg, 0.0, 0.68)
    ax.scatter([np.radians(deg)], [0.68], s=145, color=COLOR_SOLID, zorder=3)

# 第二层：内圈主环，视觉上偏左下到右侧，接近参考图的疏密。
draw_arc_nodes(r=1.66, start_deg=328, end_deg=80, num_nodes=7, is_hollow=False, size=138)
draw_arc_nodes(r=1.66, start_deg=182, end_deg=252, num_nodes=6, is_hollow=False, size=138)

# 第三层：中圈离散短段。
draw_arc_nodes(r=2.64, start_deg=318, end_deg=342, num_nodes=4, is_hollow=False, size=138)
draw_arc_nodes(r=2.55, start_deg=102, end_deg=132, num_nodes=3, is_hollow=True, size=132)
draw_arc_nodes(r=2.72, start_deg=220, end_deg=242, num_nodes=2, is_hollow=False, size=138)
draw_arc_nodes(r=2.77, start_deg=74, end_deg=74, num_nodes=1, is_hollow=True, size=132)
draw_arc_nodes(r=2.48, start_deg=286, end_deg=304, num_nodes=2, is_hollow=False, size=138)

# 第四层：外圈三段。空心段在左上到上方，实心段在右侧和下方。
draw_arc_nodes(r=3.78, start_deg=278, end_deg=8, num_nodes=10, is_hollow=True, size=146)
draw_arc_nodes(r=3.78, start_deg=20, end_deg=92, num_nodes=7, is_hollow=False, size=146)
draw_arc_nodes(r=3.78, start_deg=118, end_deg=175, num_nodes=5, is_hollow=False, size=146)
draw_arc_nodes(r=3.78, start_deg=194, end_deg=266, num_nodes=8, is_hollow=True, size=146)

ax.set_rmax(4.45)
plt.tight_layout(pad=0)
plt.savefig("/tmp/shian-ziwei-polar-adjusted.png", dpi=220, facecolor=BG, bbox_inches="tight", pad_inches=0.02)
