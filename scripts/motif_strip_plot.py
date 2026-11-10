# usage: motif_strip_plot.py DISTANCE_FIRST_DIR OUT.png [motif|outlier]
# Input: results/distance_first/tables/ from the distance-first analysis (currently on origin/prachi, not yet on this branch).
import sys, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
D, OUT = sys.argv[1], sys.argv[2]; mode = sys.argv[3] if len(sys.argv) > 3 else 'motif'
c = pd.read_csv(f'{D}/tables/shape_outlier_context.csv', parse_dates=['date'])
c['day'] = c.date.dt.tz_localize(None).dt.normalize(); c['ym'] = c.day.dt.to_period('M')
V = [('ship_minutes_mean','Ship minutes per hour','higher = more ships'),('WSPD','Wind speed (m/s)','higher = stormier'),
     ('WVHT_44098','Wave height (m)','higher = stormier'),('PRES','Pressure (hPa)','lower = stormier')]
if mode == 'motif':
    m = pd.read_csv(f'{D}/tables/shape_motifs.csv').head(3)
    days = [(f'Pair {r.motif_rank}', w) for r in m.itertuples() for w in (r.source_window_id, r.neighbor_window_id)]
else:
    days = [(f'Outlier #{r.outlier_rank}', r.window_id) for r in c.nsmallest(10, 'outlier_rank').itertuples()]
col_of = lambda i: ('#d1495b' if i % 2 == 0 else '#2a6f97') if mode == 'motif' else '#d1495b'
n = len(days); fig, ax = plt.subplots(1, 4, figsize=(11, 0.55 * n + 1.4), sharey=True); rng = np.random.default_rng(1)
for a, (col, ttl, note) in zip(ax, V):
    for i, (_, wid) in enumerate(days):
        d = c[c.window_id == wid].iloc[0]; b = c[(c.deployment == d.deployment) & (c.ym == d.ym) & (c.window_id != wid)][col].dropna()
        a.scatter(b, i + rng.uniform(-.18, .18, len(b)), s=9, c='#b5bcc4', lw=0)
        a.plot([b.median()]*2, [i-.3, i+.3], c='#6b7580', lw=1.2)
        a.scatter(d[col], i, s=55, c=col_of(i), ec='k', lw=.6, zorder=3)
    a.set_title(f'{ttl}\n{note}', fontsize=8.5); a.spines[['top','right']].set_visible(False); a.tick_params(labelsize=7.5)
    a.set_yticks(range(n)); a.set_ylim(n - .4, -.6)
lab = []
for p, wid in days:
    d = c[c.window_id == wid].iloc[0]; k = ((c.deployment == d.deployment) & (c.ym == d.ym)).sum() - 1
    lab.append(f'{p}  {d.day:%Y-%m-%d}\n{d.deployment[-2:]}, baseline n={k}')
ax[0].set_yticklabels(lab, fontsize=7.5)
fig.text(.5, .01, 'Grey dots: other days in the same deployment and month. Grey bar: baseline median. Colored dot: the selected day.', ha='center', fontsize=8)
fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(OUT, dpi=170)
