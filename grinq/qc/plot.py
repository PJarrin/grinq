import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path


def qcsum2plt(file, save=True, show=False):
    """
    Make plots from yearly QC stats

    :param file: yearly statistics
    :param save:  save to file
    :param show: display plots
    :return: none
    """

    def add_rect(ax, x, y, w, h, color):
        ax.add_patch(plt.Rectangle(
            (x - w / 2, y - h / 2), w, h, facecolor=color, edgecolor='none'))


    qc_sum = np.genfromtxt(file, comments="#", usecols=range(2, 28), missing_values="-",
                           filling_values=np.nan, dtype=float)

    qc_date = np.genfromtxt(file, usecols=(0), dtype=str)
    dtime = [datetime.strptime(d, '%Y-%m-%d') for d in qc_date]

    # convert once nad use everywhere
    t = mdates.date2num(dtime)

    # Extract metadata from file
    with open(file, "r") as f:
        for line in f:
            if line.startswith("#"):
                first_line = line
                break

    code = first_line.split()[1]
    const = os.path.basename(file).split('_')[2]


    # Detect available MP values
    mp_names = ["mp1", "mp2", "mp3", "mp4", "mp5", "mp6", "mp7", "mp8"]
    mp_indices = list(range(15, 23))

    mp_cols = [(name, idx) for name, idx in zip(mp_names, mp_indices)
        if np.any(~np.isnan(qc_sum[:, idx]) & (qc_sum[:, idx] != 0))]


    if len(t) > 1:
        dt = float(np.median(np.diff(t)))
    else:
        dt = 1.0

    # Define dynamic width for figure (5–366 days)
    n_days = (t[-1] - t[0])

    fig_width = np.interp(n_days, [5, 366], [5, 22])
    fig_width = np.clip(fig_width, 5, 22)

    fig, axs = plt.subplots(3, 1, figsize=(fig_width, 8), sharex=True, gridspec_kw={'height_ratios': [0.7, 1.0, 0.7]})

    myfmt = mdates.DateFormatter('%Y-%m-%d')

    for ax in axs:
        ax.xaxis.set_major_formatter(myfmt)
        ax.grid(which='major', color='#797676', linestyle='--', alpha=0.2)


    # Middle Panel: multipath
    ax = axs[1]

    nmp = len(mp_cols)
    row_spacing = 1.0
    bar_height = 0.2
    rect_width = 0.5 * dt  # consistent with sampling interval

    cmap = plt.cm.viridis
    norm = plt.Normalize(0, 1)

    y_positions = []
    labels = []

    for i, (name, idx) in enumerate(mp_cols):

        y = (nmp - i - 0.5) * row_spacing
        y_positions.append(y)
        labels.append(name)

        col = qc_sum[:, idx] / 100.0  # cm to meters

        for j in range(len(col)):

            v = col[j]
            if np.isnan(v) or v <= 0:
                continue

            v = np.clip(v, 0, 1)

            add_rect(ax, t[j], y, rect_width, bar_height, cmap(norm(v)))

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.set_ylim(0, nmp * row_spacing + 0.15)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])


    # Top PANEL: Cycle splits
    ax = axs[0]

    csall_col_idx = 23
    cs = np.nan_to_num(qc_sum[:, csall_col_idx])

    # single row
    y = 0.5

    # Cycle-slip colour palette
    cmap_cs = plt.cm.hot

    # Fixed percentage scale
    norm_cs = plt.Normalize(0, 50)  # 0-1 %

    for j in range(len(cs)):

        v = cs[j]

        if np.isnan(v) or v <= 0:
            continue

        add_rect(ax, t[j], y, rect_width, bar_height / 2, cmap_cs(norm_cs(v)))

    ax.set_yticks([y])
    ax.set_yticklabels(["csAll"])
    ax.set_ylim(0, 1)

    # Cycle-slip colorbar
    sm_cs = plt.cm.ScalarMappable(cmap=cmap_cs, norm=norm_cs)
    sm_cs.set_array([])

    cax_cs = fig.add_axes([0.87, 0.68, 0.008, 0.18])

    fig.colorbar(sm_cs, cax=cax_cs, label="Cycle slips (%)")

    """
    # time-line format
    cs = np.nan_to_num(qc_sum[:, csall_col_idx])
    ax.plot(t, cs, 'o', color='red', markersize=5, linewidth=1)
    ax.set_ylabel("Cycle slips (csAll)")
    ax.grid(alpha=0.2)
    """

    # BOTTOM PANEL: Rinex size
    ax = axs[2]

    rinex_mb = qc_sum[:, -1] / 1024.0  # KB to MB
    # rinex_mb = qc_sum[:, -1] # KB
    ax.plot(t, rinex_mb, 'o', color='blue', markersize=5, linewidth=1)
    ax.set_ylabel("RINEX size (MB)")
    ax.set_xlabel("Date (YY-MM-DD)")
    fig.suptitle(f"{code.upper()} Quality Check: {const} - Constellation", fontsize=13, y=0.92)

    # Set GLOBAL X-LIMITS (for alignment)
    xmin = t[0] - dt
    xmax = t[-1] + dt

    for ax in axs:
        ax.set_xlim(xmin, xmax)


    # Set ticks format and location of colored bar (NO tight_layout!)
    axs[0].tick_params(labelbottom=False)
    axs[1].tick_params(labelbottom=False)

    fig.subplots_adjust(hspace=0.15, right=0.86)

    # [left, bottom, width, height]
    cax = fig.add_axes([0.87, 0.38, 0.008, 0.22])
    fig.colorbar(sm, cax=cax, label="Multipath (m)")

    if save:
        fig.savefig(Path(file).with_suffix(".jpg"), dpi=150)
        print(f" -- Saved plot: {Path(file).with_suffix('.jpg')}")

    if show:
        plt.show()
