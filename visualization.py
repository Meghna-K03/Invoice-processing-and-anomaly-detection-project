import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import os

# ── LOAD DATA ────────────────────────────────────────────────
csv_path = os.path.join(
    os.path.dirname(__file__),
    "output",
    "final_results.csv"
)


df = pd.read_csv(csv_path)

# convert Total Amount to numeric safely
df['Total Amount'] = pd.to_numeric(df['Total Amount'], errors='coerce').fillna(0.0)

amounts     = df['Total Amount'].tolist()
is_anomaly  = df['is_anomaly'].tolist()

normal_amounts  = df[df['is_anomaly'] == False]['Total Amount'].tolist()
anomaly_amounts = df[df['is_anomaly'] == True]['Total Amount'].tolist()

# ── FIGURE 1: BOX PLOT ─────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 7))
fig.suptitle('Invoice Amount Distribution — Box Plot Analysis',
             fontsize=16, fontweight='bold')

# ── Left plot: all invoices ──
bp1 = axes[0].boxplot(
    amounts,
    patch_artist=True,
    medianprops=dict(color='red', linewidth=2.5),
    boxprops=dict(facecolor='#AED6F1', color='#2874A6'),
    whiskerprops=dict(color='#2874A6', linewidth=1.5),
    capprops=dict(color='#2874A6', linewidth=1.5),
    flierprops=dict(marker='o', color='red',
                    markerfacecolor='red', markersize=8)
)
axes[0].set_title('All 117 Invoices', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Total Amount ($)', fontsize=11)
axes[0].set_xlabel('All Invoices', fontsize=11)
axes[0].yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'${x:,.0f}')
)
axes[0].grid(axis='y', alpha=0.3)
axes[0].set_facecolor('#F8F9FA')

# annotate how many outliers are above the whisker
q1  = np.percentile(amounts, 25)
q3  = np.percentile(amounts, 75)
iqr = q3 - q1
upper_fence   = q3 + 1.5 * iqr
outlier_vals  = [a for a in amounts if a > upper_fence]
axes[0].annotate(
    f'{len(outlier_vals)} outliers\nabove whisker',
    xy=(1, max(outlier_vals)),
    xytext=(1.15, max(outlier_vals) * 0.85),
    fontsize=9, color='red',
    arrowprops=dict(arrowstyle='->', color='red')
)

# ── Right plot: normal vs anomaly side by side ──
bp2 = axes[1].boxplot(
    [normal_amounts, anomaly_amounts],
    patch_artist=True,
    medianprops=dict(color='black', linewidth=2),
    flierprops=dict(marker='o', markersize=7)
)
bp2['boxes'][0].set_facecolor('#82E0AA')   # green=normal
bp2['boxes'][1].set_facecolor('#F1948A')   # red=anomaly
bp2['whiskers'][0].set_color('#1E8449')
bp2['whiskers'][1].set_color('#1E8449')
bp2['whiskers'][2].set_color('#C0392B')
bp2['whiskers'][3].set_color('#C0392B')

axes[1].set_title('Normal vs Anomaly Invoices', fontsize=13, fontweight='bold')
axes[1].set_ylabel('Total Amount ($)', fontsize=11)
axes[1].set_xticks([1, 2])
axes[1].set_xticklabels(
    [f'Normal\n(n={len(normal_amounts)})',
     f'Anomaly\n(n={len(anomaly_amounts)})'],
    fontsize=11
)
axes[1].yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'${x:,.0f}')
)
axes[1].grid(axis='y', alpha=0.3)
axes[1].set_facecolor('#F8F9FA')

# add median stats in a text box
axes[1].text(
    0.98, 0.97,
    f'Normal median  : ${np.median(normal_amounts):,.0f}\n'
    f'Anomaly median : ${np.median(anomaly_amounts):,.0f}',
    transform=axes[1].transAxes,
    fontsize=9, verticalalignment='top', horizontalalignment='right',
    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8)
)

plt.tight_layout()
output_dir = os.path.join(os.path.dirname(__file__), 'output')
plt.savefig(os.path.join(output_dir, 'boxplot.png'), dpi=150, bbox_inches='tight',
            facecolor='white')

print("Box plot saved to output/boxplot.png")


# ── FIGURE 2: SCATTER PLOT ─────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle('Invoice Amount Distribution — Anomaly Scatter Plot',
             fontsize=16, fontweight='bold')

indices = list(range(len(amounts)))

# ── Left plot: full range ──
for i, (amt, flag) in enumerate(zip(amounts, is_anomaly)):
    axes[0].scatter(
        i, amt,
        c='#E74C3C' if flag else '#2980B9',
        s=120      if flag else 50,
        alpha=0.9  if flag else 0.6,
        zorder=3   if flag else 2
    )

# threshold lines
axes[0].axhline(y=50000, color='orange', linestyle='--',
                linewidth=1.5, label='High threshold ($50,000)', alpha=0.8)
axes[0].axhline(y=10, color='purple', linestyle='--',
                linewidth=1.5, label='Low threshold ($10)', alpha=0.8)

# label the biggest outliers
big = [(i, a) for i, (a, f) in enumerate(zip(amounts, is_anomaly))
       if f and a > 40000]
for idx, amt in big:
    axes[0].annotate(
        f'${amt:,.0f}',
        xy=(idx, amt), xytext=(idx + 3, amt * 0.9),
        fontsize=8, color='#C0392B', fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1)
    )
normal_patch  = mpatches.Patch(color='#2980B9',
                                label=f'Normal ({len(normal_amounts)})')
anomaly_patch = mpatches.Patch(color='#E74C3C',
                                label=f'Anomaly ({len(anomaly_amounts)})')
axes[0].legend(handles=[normal_patch, anomaly_patch],
               loc='upper left', fontsize=9)
axes[0].set_title('All Invoices: Normal vs Anomaly',
                  fontsize=13, fontweight='bold')
axes[0].set_xlabel('Invoice Index', fontsize=11)
axes[0].set_ylabel('Total Amount ($)', fontsize=11)
axes[0].yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'${x:,.0f}')
)
axes[0].grid(alpha=0.3)
axes[0].set_facecolor('#F8F9FA')

# ── Right plot: zoomed in (< $30,000) ──
for i, (amt, flag) in enumerate(zip(amounts, is_anomaly)):
    if amt <= 30000:
        axes[1].scatter(
            i, amt,
            c='#E74C3C' if flag else '#2980B9',
            s=120      if flag else 50,
            alpha=0.9  if flag else 0.6
        )

axes[1].axhline(y=10, color='purple', linestyle='--',
                linewidth=1.5, label='Low threshold ($10)', alpha=0.8)
axes[1].axhline(
    y=np.median(normal_amounts), color='green',
    linestyle=':', linewidth=1.5,
    label=f'Normal median (${np.median(normal_amounts):,.0f})',
    alpha=0.8
)

axes[1].legend(loc='upper right', fontsize=9)
axes[1].set_title(
    'Zoomed In: Amounts up to $30,000\n(excludes 4 extreme outliers)',
    fontsize=12, fontweight='bold'
)
axes[1].set_xlabel('Invoice Index', fontsize=11)
axes[1].set_ylabel('Total Amount ($)', fontsize=11)
axes[1].yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'${x:,.0f}')
)
axes[1].grid(alpha=0.3)
axes[1].set_facecolor('#F8F9FA')

# re-add legend with color patches for zoomed plot
normal_patch  = mpatches.Patch(color='#2980B9', label='Normal')
anomaly_patch = mpatches.Patch(color='#E74C3C', label='Anomaly')
existing = axes[1].get_legend_handles_labels()
axes[1].legend(
    handles=[normal_patch, anomaly_patch] + existing[0][2:],
    loc='upper right', fontsize=9
)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'scatterplot.png'), dpi=150, bbox_inches='tight',
            facecolor='white')

print("Scatter plot saved to output/scatterplot.png")
print("\nCheck the output/ folder for the saved plots!")