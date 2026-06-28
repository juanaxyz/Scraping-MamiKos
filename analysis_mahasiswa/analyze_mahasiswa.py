"""
Analisis Mahasiswa: 20 Insight Praktis untuk Mencari Kos di Sekitar UNUD
=============================================================================
Dataset : data/mamikos_all.csv (241 kos di area Jimbaran & Sudirman)
Output  : analysis_mahasiswa/output/*.png (poster-ready)
=============================================================================
"""

import os, re, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import seaborn as sns
from scipy import stats
from scipy.stats import linregress

warnings.filterwarnings('ignore')
sns.set_theme(style='whitegrid', font_scale=1.1)
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#44BBA4', '#E94F37', '#393E41', '#3A6B35', '#E2C044']

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

def savefig(name):
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, name), dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  [saved] {name}')

def parse_price(s):
    if pd.isna(s): return None
    s_clean = str(s).replace('.','').replace('Rp','').replace('/bulan','').strip()
    nums = re.findall(r'\d+', s_clean)
    return int(nums[0]) if nums else None

def parse_size(s):
    if pd.isna(s): return np.nan, np.nan
    m = re.match(r'([\d.]+)\s*x\s*([\d.]+)', str(s))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)

def clean_subdistrict(x):
    if pd.isna(x): return x
    return str(x).replace('Kecamatan ', '')

def fmt_rp(val):
    if val >= 1e6:
        return f'Rp {val/1e6:.2f}jt'
    return f'Rp {val:,.0f}'

def add_stats_box(ax, text, xy=(0.02, 0.97), fontsize=9, color='white', alpha=0.9):
    props = dict(boxstyle='round,pad=0.5', facecolor=color, alpha=alpha, edgecolor='gray')
    ax.text(xy[0], xy[1], text, transform=ax.transAxes, fontsize=fontsize,
            verticalalignment='top', bbox=props, family='monospace')

# ============================================================================
# LOAD & CLEAN DATA
# ============================================================================
print('\n' + '='*70)
print('  LOADING DATA')
print('='*70)

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'mamikos_all.csv')
df = pd.read_csv(CSV)
print(f'  Loaded {len(df)} rows x {len(df.columns)} columns')

df['price'] = df['harga_real_detail'].apply(parse_price)
df[['size_w','size_l']] = df['size'].apply(lambda x: pd.Series(parse_size(x)))
df['size_area'] = df['size_w'] * df['size_l']
df['price_per_sqm'] = df['price'] / df['size_area']
df['subdistrict'] = df['area_subdistrict'].apply(clean_subdistrict)
df['gender_label'] = df['gender'].map({0: 'Campur', 1: 'Putri', 2: 'Putri'})

for col in ['dist_to_nearest_supermarket_km','dist_to_nearest_terminal_km']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

bath_cols = [c for c in df.columns if c.startswith('fac_bath_')]
room_cols = [c for c in df.columns if c.startswith('fac_room_')]
share_cols = [c for c in df.columns if c.startswith('fac_share_')]
df['fac_bath_n'] = df[bath_cols].sum(axis=1)
df['fac_room_n'] = df[room_cols].sum(axis=1)
df['fac_share_n'] = df[share_cols].sum(axis=1)
df['fac_total_n'] = df['fac_bath_n'] + df['fac_room_n'] + df['fac_share_n']

df_valid = df.dropna(subset=['price'])
print(f'  Valid price records: {len(df_valid)}')
print(f'  Jimbaran: {len(df[df["source_file"]=="jimbaran"])} | Sudirman: {len(df[df["source_file"]=="sudirman"])}')


# ============================================================================
# INSIGHT 1: GAMBARAN HARGA KOS BULANAN
# ============================================================================
print('\n' + '='*70)
print('  1. GAMBARAN HARGA KOS BULANAN DI SEKITAR UNUD')
print('='*70)

p = df_valid['price']
stats1 = {
    'Rata-rata': p.mean(), 'Median': p.median(), 'Std Dev': p.std(),
    'Minimum': p.min(), 'Q1 (25%)': p.quantile(0.25),
    'Q3 (75%)': p.quantile(0.75), 'Maximum': p.max(),
    'Total Kos': int(len(p)),
}

fig, ax = plt.subplots(figsize=(12, 7))
ax.hist(p/1e6, bins=25, color=COLORS[0], edgecolor='white', alpha=0.85)
ax.axvline(stats1['Rata-rata']/1e6, color='red', ls='--', lw=2.5, label='Rata-rata')
ax.axvline(stats1['Median']/1e6, color='blue', ls='--', lw=2.5, label='Median')
ax.axvline(stats1['Q1 (25%)']/1e6, color='green', ls=':', lw=2, alpha=0.7, label='Q1')
ax.axvline(stats1['Q3 (75%)']/1e6, color='green', ls=':', lw=2, alpha=0.7, label='Q3')
ax.set_xlabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Gambaran Harga Kos Bulanan di Sekitar UNUD', fontsize=15, fontweight='bold')
ax.legend(fontsize=11)

stats_text = (
    f'  Total Kos: {stats1["Total Kos"]}\n'
    f'  Rata-rata : {fmt_rp(stats1["Rata-rata"])}\n'
    f'  Median    : {fmt_rp(stats1["Median"])}\n'
    f'  Minimum   : {fmt_rp(stats1["Minimum"])}\n'
    f'  Maximum   : {fmt_rp(stats1["Maximum"])}\n'
    f'  Q1 (25%)  : {fmt_rp(stats1["Q1 (25%)"])}\n'
    f'  Q3 (75%)  : {fmt_rp(stats1["Q3 (75%)"])}\n'
    f'  Std Dev   : {fmt_rp(stats1["Std Dev"])}'
)
add_stats_box(ax, stats_text, xy=(0.62, 0.97), fontsize=10)
savefig('01_gambaran_harga.png')


# ============================================================================
# INSIGHT 2: BUDGET AMAN UNTUK MAHASISWA
# ============================================================================
print('  2. BUDGET AMAN UNTUK MAHASISWA')
print('='*70)

budgets = [1_000_000, 1_500_000, 2_000_000, 2_500_000, 3_000_000, 4_000_000, 5_000_000, 10_000_000]
budget_counts = [ (p <= b).sum() for b in budgets ]
budget_pcts  = [ c/len(p)*100 for c in budget_counts ]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.bar(range(len(budgets)), budget_counts, color=[COLORS[0] if v<50 else COLORS[2] if v<80 else COLORS[4] for v in budget_pcts],
              edgecolor='white', width=0.65)

for i, (c, pc) in enumerate(zip(budget_counts, budget_pcts)):
    ax.text(i, c + 4, f'{c} kos\n({pc:.1f}%)', ha='center', fontsize=10, fontweight='bold')

ax.set_xticks(range(len(budgets)))
ax.set_xticklabels([fmt_rp(b) for b in budgets], rotation=25, ha='right')
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_xlabel('Budget Maksimal', fontsize=13)
ax.set_title('Seberapa Jauh Budget Kamar Bisa Mendapatkan Kos?', fontsize=14, fontweight='bold')
ax.set_ylim(0, max(budget_counts) + 25)

cat_text = (
    f'  Budget <= Rp 1,5jt →  {budget_counts[1]:3d} kos ({budget_pcts[1]:.1f}%)\n'
    f'  Budget <= Rp 2,0jt →  {budget_counts[2]:3d} kos ({budget_pcts[2]:.1f}%)\n'
    f'  Budget <= Rp 2,5jt →  {budget_counts[3]:3d} kos ({budget_pcts[3]:.1f}%)  ← AMAN\n'
    f'  Budget <= Rp 3,0jt →  {budget_counts[4]:3d} kos ({budget_pcts[4]:.1f}%)\n'
    f'  Budget <= Rp 5,0jt →  {budget_counts[6]:3d} kos ({budget_pcts[6]:.1f}%)'
)
add_stats_box(ax, cat_text, fontsize=10)
savefig('02_budget_aman.png')


# ============================================================================
# INSIGHT 3: RENTANG HARGA YANG MASUK AKAL
# ============================================================================
print('  3. RENTANG HARGA YANG MASUK AKAL')
print('='*70)

q1, med, q3 = p.quantile(0.25), p.median(), p.quantile(0.75)
iqr = q3 - q1
lower_fence = max(p.min(), q1 - 1.5*iqr)
upper_fence = min(p.max(), q3 + 1.5*iqr)
in_range = ((p >= lower_fence) & (p <= upper_fence)).sum()

fig, ax = plt.subplots(figsize=(12, 7))
bp = ax.boxplot(p/1e6, vert=True, patch_artist=True, widths=0.35,
                boxprops=dict(facecolor=COLORS[0], alpha=0.7),
                medianprops=dict(color='red', lw=2.5),
                whiskerprops=dict(lw=2),
                capprops=dict(lw=2))

violin_parts = ax.violinplot(p/1e6, positions=[1], showmedians=False, showextrema=False, widths=0.6)
for vp in violin_parts['bodies']:
    vp.set_facecolor(COLORS[0])
    vp.set_alpha(0.2)

ax.set_xticks([])
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Rentang Harga Kos yang Wajar untuk Mahasiswa', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))

range_text = (
    f'  50% kos di rentang:   {fmt_rp(q1)} - {fmt_rp(q3)}\n'
    f'  Median harga kos:     {fmt_rp(med)}\n'
    f'  Rata-rata harga:      {fmt_rp(p.mean())}\n\n'
    f'  IQR (Q3-Q1):          {fmt_rp(iqr)}\n'
    f'  Batas wajar bawah:    {fmt_rp(lower_fence)}\n'
    f'  Batas wajar atas:     {fmt_rp(upper_fence)}\n\n'
    f'  Kos dalam rentang wajar: {in_range} dari {len(p)} ({in_range/len(p)*100:.1f}%)'
)
add_stats_box(ax, range_text, xy=(0.55, 0.97), fontsize=10)
savefig('03_rentang_wajar.png')


# ============================================================================
# INSIGHT 4: KATEGORI MAHAL / PREMIUM
# ============================================================================
print('  4. KATEGORI MAHAL / PREMIUM')
print('='*70)

bins = [0, 1_500_000, 2_500_000, 3_500_000, 5_000_000, float('inf')]
labels_bin = ['Murah\n(<Rp1,5jt)', 'Terjangkau\n(Rp1,5-2,5jt)', 'Standar\n(Rp2,5-3,5jt)', 'Mahal\n(Rp3,5-5jt)', 'Premium\n(>Rp5jt)']
p_cat = pd.cut(p, bins=bins, labels=labels_bin)
cat_counts = p_cat.value_counts()

fig, ax = plt.subplots(figsize=(12, 7))
wedges, texts, autotexts = ax.pie(
    cat_counts.values, labels=cat_counts.index, autopct='%1.1f%%',
    colors=[COLORS[0], COLORS[1], COLORS[5], COLORS[2], COLORS[3]],
    startangle=90, pctdistance=0.78,
    textprops=dict(fontsize=11))
for t in autotexts:
    t.set_fontweight('bold')
    t.set_fontsize(12)

ax.set_title('Kategori Harga Kos: Murah hingga Premium', fontsize=14, fontweight='bold')

ann_text = (
    f'  Murah (<Rp1,5jt)      : {cat_counts[labels_bin[0]]} kos ({cat_counts[labels_bin[0]]/len(p)*100:.1f}%)\n'
    f'  Terjangkau (Rp1,5-2,5jt): {cat_counts[labels_bin[1]]} kos ({cat_counts[labels_bin[1]]/len(p)*100:.1f}%)\n'
    f'  Standar (Rp2,5-3,5jt)  : {cat_counts[labels_bin[2]]} kos ({cat_counts[labels_bin[2]]/len(p)*100:.1f}%)\n'
    f'  Mahal (Rp3,5-5jt)      : {cat_counts[labels_bin[3]]} kos ({cat_counts[labels_bin[3]]/len(p)*100:.1f}%)\n'
    f'  Premium (>Rp5jt)       : {cat_counts[labels_bin[4]]} kos ({cat_counts[labels_bin[4]]/len(p)*100:.1f}%)\n\n'
    f'  Sebanyak {(cat_counts[labels_bin[0]]+cat_counts[labels_bin[1]])/len(p)*100:.1f}% kos\n'
    f'  masuk kategori terjangkau!'
)
add_stats_box(ax, ann_text, xy=(0.02, 0.97), fontsize=10)
savefig('04_kategori_harga.png')


# ============================================================================
# INSIGHT 5: PERBANDINGAN JIMBARAN VS SUDIRMAN
# ============================================================================
print('  5. PERBANDINGAN JIMBARAN VS SUDIRMAN')
print('='*70)

df_jim = df_valid[df_valid['source_file']=='jimbaran']
df_sud = df_valid[df_valid['source_file']=='sudirman']

fig, ax = plt.subplots(figsize=(10, 7))

x_pos = [0, 1]
means = [df_jim['price'].mean(), df_sud['price'].mean() if len(df_sud)>0 else 0]
meds  = [df_jim['price'].median(), df_sud['price'].median() if len(df_sud)>0 else 0]
stds  = [df_jim['price'].std(), df_sud['price'].std() if len(df_sud)>0 else 0]
counts = [len(df_jim), len(df_sud)]

bars = ax.bar(x_pos, [m/1e6 for m in means], yerr=[s/1e6 for s in stds],
              color=[COLORS[0], COLORS[1]], width=0.5, capsize=8, alpha=0.85,
              edgecolor='black', linewidth=0.5)

for i, (m, med, c) in enumerate(zip(means, meds, counts)):
    ax.text(i, m/1e6 + 0.2, f'{fmt_rp(m)}\nMedian: {fmt_rp(med)}\nn={c}', ha='center', fontsize=10, fontweight='bold')

ax.set_xticks(x_pos)
ax.set_xticklabels(['Jimbaran\n(Kuta Selatan)', 'Sudirman\n(Denpasar Selatan)'], fontsize=12)
ax.set_ylabel('Rata-rata Harga (Juta Rp)', fontsize=13)
ax.set_title('Perbandingan Harga Kos: Jimbaran vs Sudirman', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))

note = (
    f'  DATA SUDIRMAN SANGAT TERBATAS!\n'
    f'  Jimbaran: {counts[0]} kos\n'
    f'  Sudirman: {counts[1]} kos (hanya 1 record)\n\n'
    f'  Harga rata-rata Jimbaran: {fmt_rp(means[0])}\n'
    f'  Harga rata-rata Sudirman: {fmt_rp(means[1])}\n\n'
    f'  Perbandingan tidak representatif\n'
    f'  karena data Sudirman tidak cukup.'
)
add_stats_box(ax, note, xy=(0.55, 0.97), fontsize=9, alpha=0.95)
savefig('05_jimbaran_vs_sudirman.png')


# ============================================================================
# INSIGHT 6: HARGA PER KECAMATAN
# ============================================================================
print('  6. HARGA PER KECAMATAN')
print('='*70)

g6 = df_valid.groupby('subdistrict')['price']
d6 = g6.agg(['count','mean','median','std','min','max']).round(0)
print(d6.to_string())

fig, ax = plt.subplots(figsize=(12, 7))
order = g6.median().sort_values(ascending=True).index
data_plot = [df_valid[df_valid['subdistrict']==s]['price'].values/1e6 for s in order]
bp = ax.boxplot(data_plot, labels=[f'{s}\n(n={g6.count()[s]})' for s in order],
                patch_artist=True, widths=0.5,
                boxprops=dict(facecolor=COLORS[0], alpha=0.7),
                medianprops=dict(color='red', lw=2.5))

means_pos = [g6.mean()[s]/1e6 for s in order]
ax.scatter(range(1, len(order)+1), means_pos, color='blue', marker='D', s=60, zorder=5, label='Rata-rata')
for i, m in enumerate(means_pos):
    ax.text(i+1+0.25, m, f'{fmt_rp(g6.mean()[order[i]])}', fontsize=8, color='blue', va='center')

ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_xlabel('Kecamatan', fontsize=13)
ax.set_title('Perbandingan Harga Kos per Kecamatan', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))
ax.legend(fontsize=11)
plt.xticks(fontsize=10, rotation=15)
savefig('06_harga_per_kecamatan.png')


# ============================================================================
# INSIGHT 7: CAMPUR VS PUTRI VS PUTRA
# ============================================================================
print('  7. PERBEDAAN HARGA BERDASARKAN GENDER')
print('='*70)

gender_ttest_p = None
g7 = df_valid.groupby('gender_label')['price']
d7 = g7.agg(['count','mean','median','std','min','max']).round(0)
print(d7.to_string())

fig, ax = plt.subplots(figsize=(10, 7))
labels_gender = ['Campur', 'Putri']
data_gender = [df_valid[df_valid['gender_label']=='Campur']['price'].values/1e6,
               df_valid[df_valid['gender_label']=='Putri']['price'].values/1e6]
bp = ax.boxplot(data_gender, labels=labels_gender, patch_artist=True, widths=0.4,
                medianprops=dict(color='red', lw=2.5))
for patch, color in zip(bp['boxes'], [COLORS[0], COLORS[1]]):
    patch.set_facecolor(color)

means_g = [g7.mean().get('Campur', 0)/1e6, g7.mean().get('Putri', 0)/1e6]
ax.scatter([1, 2], means_g, color='blue', marker='D', s=80, zorder=5, label='Rata-rata')

for i, lbl in enumerate(labels_gender):
    c = g7.count().get(lbl, 0)
    m = g7.mean().get(lbl, 0)
    md = g7.median().get(lbl, 0)
    ax.text(i+1, means_g[i] + 0.25, f'n={c}\nMean: {fmt_rp(m)}\nMedian: {fmt_rp(md)}',
            ha='center', fontsize=10, fontweight='bold')

ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Perbandingan Harga: Kos Campur vs Putri', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))

# T-test
campur = df_valid[df_valid['gender_label']=='Campur']['price'].dropna()
putri = df_valid[df_valid['gender_label']=='Putri']['price'].dropna()
if len(campur) > 0 and len(putri) > 0:
    t_stat7, gender_ttest_p = stats.ttest_ind(campur, putri, equal_var=False)
    sig_text = f'  Uji t-test: t={t_stat7:.2f}, p={gender_ttest_p:.2e}\n'
    sig_text += f'  {"SIGNIFIKAN (p<0.05)" if gender_ttest_p<0.05 else "TIDAK SIGNIFIKAN (p>0.05)"}'
    add_stats_box(ax, sig_text, xy=(0.55, 0.97), fontsize=10)
savefig('07_perbedaan_gender.png')


# ============================================================================
# INSIGHT 8: PELUANG BUDGET ≤ RP 2,5 JUTA
# ============================================================================
print('  8. PELUANG BUDGET ≤ RP 2,5 JUTA')
print('='*70)

budget_target = 2_500_000
within_budget = (p <= budget_target).sum()
pct_within = within_budget / len(p) * 100
above_budget = len(p) - within_budget

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.bar(['≤ Rp 2,5 Juta\n(Budget Aman)', '> Rp 2,5 Juta\n(Mahal)'],
              [within_budget, above_budget],
              color=[COLORS[5], COLORS[3]], width=0.5, edgecolor='black')

for bar, val in zip(bars, [within_budget, above_budget]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
            f'{val} kos', ha='center', fontsize=13, fontweight='bold')

ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title(f'Peluang Mendapat Kos dengan Budget ≤ Rp 2,5 Juta', fontsize=14, fontweight='bold')
ax.set_ylim(0, max(within_budget, above_budget) + 25)

prob_text = (
    f'  Dari {len(p)} total kos:\n\n'
    f'  ✅ {within_budget} kos ({pct_within:.1f}%)\n'
    f'     masuk budget Rp 2,5jt\n\n'
    f'  ❌ {above_budget} kos ({100-pct_within:.1f}%)\n'
    f'     di atas budget Rp 2,5jt\n\n'
    f'  ➜ Peluang: {pct_within:.0f}%\n'
    f'  ➜ Artinya, 1 dari 2 kos\n'
    f'     bisa kamu dapatkan!'
)
add_stats_box(ax, prob_text, xy=(0.55, 0.97), fontsize=11)
savefig('08_peluang_budget_25jt.png')


# ============================================================================
# INSIGHT 9: KOS DI BAWAH RP 2 JUTA
# ============================================================================
print('  9. KOS DI BAWAH RP 2 JUTA')
print('='*70)

budget_2jt = 2_000_000
under_2jt = (p <= budget_2jt).sum()
pct_2jt = under_2jt / len(p) * 100
df_under_2jt = df_valid[df_valid['price'] <= budget_2jt]
avg_price_under = df_under_2jt['price'].mean()
med_price_under = df_under_2jt['price'].median()

fig, ax = plt.subplots(figsize=(10, 7))
colors_bar = [COLORS[5] if x < budget_2jt else COLORS[3] for x in sorted(p)]
ax.bar(range(len(p)), np.array(sorted(p))/1e6, color=colors_bar, width=0.8, alpha=0.7)
ax.axhline(budget_2jt/1e6, color='red', ls='--', lw=2.5, label=f'Batas Rp 2jt')
ax.fill_between(range(len(p)), 0, budget_2jt/1e6, alpha=0.08, color=COLORS[5])
ax.set_xlabel('Kos (diurutkan dari termurah)', fontsize=12)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title(f'Masih Adakah Kos di Bawah Rp 2 Juta?', fontsize=14, fontweight='bold')
ax.legend(fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))

text_9 = (
    f'  ✅ {under_2jt} dari {len(p)} kos ({pct_2jt:.1f}%)\n'
    f'     masih di bawah Rp 2jt!\n\n'
    f'  Rata-rata harga: {fmt_rp(avg_price_under)}\n'
    f'  Median harga  : {fmt_rp(med_price_under)}\n'
    f'  Termurah      : {fmt_rp(df_under_2jt["price"].min())}\n'
    f'  Termahal masih: {fmt_rp(df_under_2jt["price"].max())}\n\n'
    f'  ➜ Masih ada {pct_2jt:.0f}% kos\n'
    f'     ramah di kantong!'
)
add_stats_box(ax, text_9, xy=(0.55, 0.97), fontsize=10)
savefig('09_kos_bawah_2jt.png')


# ============================================================================
# INSIGHT 10: KOS TERMAHAL DAN TERMURAH
# ============================================================================
print('  10. KOS TERMAHAL DAN TERMURAH')
print('='*70)

top5_cheap = df_valid.nsmallest(5, 'price')[['nama_kost','price','subdistrict','size_area']]
top5_expensive = df_valid.nlargest(5, 'price')[['nama_kost','price','subdistrict','size_area']]
print('  5 TERMURAH:')
print(top5_cheap.to_string())
print('  5 TERMAHAL:')
print(top5_expensive.to_string())

fig, axes = plt.subplots(1, 2, figsize=(15, 7))

# Termurah
ax1 = axes[0]
names_cheap = [n[:25]+'..' if len(str(n))>25 else n for n in top5_cheap['nama_kost'].values]
ax1.barh(range(5), top5_cheap['price'].values/1e6, color=COLORS[5], edgecolor='black', height=0.6)
for i, (_, row) in enumerate(top5_cheap.iterrows()):
    ax1.text(row['price']/1e6 + 0.03, i, fmt_rp(row['price']), va='center', fontsize=9, fontweight='bold')
ax1.set_yticks(range(5))
ax1.set_yticklabels(names_cheap, fontsize=8)
ax1.set_xlabel('Harga (Juta Rp)')
ax1.set_title('5 Kos TERMURAH', fontsize=13, fontweight='bold', color=COLORS[5])
ax1.invert_yaxis()
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f}jt'))

# Termahal
ax2 = axes[1]
names_exp = [n[:25]+'..' if len(str(n))>25 else n for n in top5_expensive['nama_kost'].values]
ax2.barh(range(5), top5_expensive['price'].values/1e6, color=COLORS[3], edgecolor='black', height=0.6)
for i, (_, row) in enumerate(top5_expensive.iterrows()):
    ax2.text(row['price']/1e6 + 0.3, i, fmt_rp(row['price']), va='center', fontsize=9, fontweight='bold')
ax2.set_yticks(range(5))
ax2.set_yticklabels(names_exp, fontsize=8)
ax2.set_xlabel('Harga (Juta Rp)')
ax2.set_title('5 Kos TERMAHAL', fontsize=13, fontweight='bold', color=COLORS[3])
ax2.invert_yaxis()
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f}jt'))

fig.suptitle('Kos Paling Murah vs Paling Mahal di Sekitar UNUD', fontsize=14, fontweight='bold', y=1.02)
savefig('10_termahal_termurah.png')


# ============================================================================
# INSIGHT 11: PENGARUH UKURAN KAMAR TERHADAP HARGA
# ============================================================================
print('  11. PENGARUH UKURAN KAMAR TERHADAP HARGA')
print('='*70)

valid_size = df_valid.dropna(subset=['size_area', 'price'])
slope, intercept, r_val, p_val, se = linregress(valid_size['size_area'], valid_size['price'])

fig, ax = plt.subplots(figsize=(12, 7))
sc = ax.scatter(valid_size['size_area'], valid_size['price']/1e6,
                c=valid_size['price']/1e6, cmap='viridis', alpha=0.6, s=50, edgecolor='black', linewidth=0.3)
x_line = np.linspace(valid_size['size_area'].min(), valid_size['size_area'].max(), 100)
ax.plot(x_line, (slope*x_line + intercept)/1e6, color='red', lw=2.5, label=f'Regresi: Harga = {slope:.0f} × Luas + {intercept:,.0f}')
cbar = plt.colorbar(sc, ax=ax, label='Harga (Juta Rp)')
ax.set_xlabel('Luas Kamar (m²)', fontsize=13)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Apakah Ukuran Kamar Mempengaruhi Harga Kos?', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))

r2 = r_val**2
corr_text = (
    f'  Korelasi Pearson: r = {r_val:.3f}\n'
    f'  R² = {r2:.3f} ({r2*100:.1f}% variasi harga dijelaskan luas)\n'
    f'  p-value: {p_val:.4f} {"(SIGNIFIKAN)" if p_val<0.05 else "(TIDAK)"}\n\n'
    f'  Setiap +1 m² → harga naik ~Rp {slope:,.0f}\n'
    f'  Luas rata-rata: {valid_size["size_area"].mean():.1f} m²\n'
    f'  Harga rata-rata: {fmt_rp(valid_size["price"].mean())}\n\n'
    f'  ➜ Ukuran kamar berpengaruh,\n'
    f'     tapi bukan satu-satunya faktor'
)
add_stats_box(ax, corr_text, xy=(0.55, 0.97), fontsize=10)
savefig('11_pengaruh_ukuran.png')


# ============================================================================
# INSIGHT 12: PREDIKSI HARGA BERDASARKAN LUAS KAMAR
# ============================================================================
print('  12. PREDIKSI HARGA BERDASARKAN LUAS KAMAR')
print('='*70)

fig, ax = plt.subplots(figsize=(12, 7))
ax.axis('off')

formula = (
    f'RUMUS PREDIKSI HARGA KOS\n'
    f'{"="*50}\n\n'
    f'  Harga = {intercept:,.0f} + {slope:.0f} × Luas Kamar (m²)\n\n'
    f'{"="*50}\n\n'
    f'CONTOH PERHITUNGAN:\n\n'
    f'  Luas 12 m² → Rp {intercept + slope*12:,.0f} ({fmt_rp(intercept + slope*12)})\n'
    f'  Luas 15 m² → Rp {intercept + slope*15:,.0f} ({fmt_rp(intercept + slope*15)})\n'
    f'  Luas 18 m² → Rp {intercept + slope*18:,.0f} ({fmt_rp(intercept + slope*18)})\n'
    f'  Luas 20 m² → Rp {intercept + slope*20:,.0f} ({fmt_rp(intercept + slope*20)})\n'
    f'  Luas 25 m² → Rp {intercept + slope*25:,.0f} ({fmt_rp(intercept + slope*25)})\n\n'
    f'{"="*50}\n\n'
    f'STATISTIK:\n'
    f'  R² = {r2:.3f} ({r2*100:.1f}% akurasi)\n'
    f'  Rata-rata luas: {valid_size["size_area"].mean():.1f} m²\n'
    f'  Rata-rata harga: {fmt_rp(valid_size["price"].mean())}\n'
    f'  Kisaran harga: {fmt_rp(valid_size["price"].min())} - {fmt_rp(valid_size["price"].max())}\n\n'
    f'{"="*50}\n\n'
    f'⚠️ INGAT: Prediksi ini hanya perkiraan.\n'
    f'   Harga aktual bisa berbeda karena\n'
    f'   faktor fasilitas, lokasi, dan lainnya!'
)
ax.text(0.5, 0.5, formula, transform=ax.transAxes, fontsize=13, fontfamily='monospace',
        ha='center', va='center', linespacing=1.5)
ax.set_title('Prediksi Harga Kos Berdasarkan Luas Kamar', fontsize=14, fontweight='bold', pad=20)
savefig('12_prediksi_luas.png')


# ============================================================================
# INSIGHT 13: FASILITAS KAMAR TERBANYAK
# ============================================================================
print('  13. FASILITAS KAMAR TERBANYAK')
print('='*70)

fac_room_sums = df_valid[room_cols].sum().sort_values(ascending=False)
top_room = fac_room_sums.head(10)
fac_pct = top_room / len(df_valid) * 100

labels_room = [c.replace('fac_room_','').replace('_',' ').title() for c in top_room.index]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(range(len(top_room)), fac_pct.values, color=COLORS[0], edgecolor='black', height=0.6)
for i, (val, pct) in enumerate(zip(top_room.values, fac_pct.values)):
    ax.text(pct + 0.5, i, f'{int(val)} kos ({pct:.1f}%)', va='center', fontsize=10, fontweight='bold')
ax.set_yticks(range(len(top_room)))
ax.set_yticklabels(labels_room, fontsize=11)
ax.set_xlabel('Persentase Kos yang Menyediakan', fontsize=13)
ax.set_title('10 Fasilitas Kamar Paling Sering Tersedia', fontsize=14, fontweight='bold')
ax.invert_yaxis()
for spine in ['top','right']:
    ax.spines[spine].set_visible(False)
savefig('13_fasilitas_kamar.png')


# ============================================================================
# INSIGHT 14: FASILITAS UMUM TERBANYAK
# ============================================================================
print('  14. FASILITAS UMUM TERBANYAK')
print('='*70)

fac_share_sums = df_valid[share_cols].sum().sort_values(ascending=False)
top_share = fac_share_sums.head(10)
share_pct = top_share / len(df_valid) * 100

labels_share = [c.replace('fac_share_','').replace('_',' ').title() for c in top_share.index]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(range(len(top_share)), share_pct.values, color=COLORS[5], edgecolor='black', height=0.6)
for i, (val, pct) in enumerate(zip(top_share.values, share_pct.values)):
    ax.text(pct + 0.5, i, f'{int(val)} kos ({pct:.1f}%)', va='center', fontsize=10, fontweight='bold')
ax.set_yticks(range(len(top_share)))
ax.set_yticklabels(labels_share, fontsize=11)
ax.set_xlabel('Persentase Kos yang Menyediakan', fontsize=13)
ax.set_title('10 Fasilitas Umum Paling Sering Ditawarkan', fontsize=14, fontweight='bold')
ax.invert_yaxis()
for spine in ['top','right']:
    ax.spines[spine].set_visible(False)
savefig('14_fasilitas_umum.png')


# ============================================================================
# INSIGHT 15: FASILITAS KAMAR MANDI TERBANYAK
# ============================================================================
print('  15. FASILITAS KAMAR MANDI TERBANYAK')
print('='*70)

fac_bath_sums = df_valid[bath_cols].sum().sort_values(ascending=False)
top_bath = fac_bath_sums.head(10)
bath_pct = top_bath / len(df_valid) * 100

labels_bath = [c.replace('fac_bath_','').replace('_',' ').title() for c in top_bath.index]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(range(len(top_bath)), bath_pct.values, color=COLORS[1], edgecolor='black', height=0.6)
for i, (val, pct) in enumerate(zip(top_bath.values, bath_pct.values)):
    ax.text(pct + 0.5, i, f'{int(val)} kos ({pct:.1f}%)', va='center', fontsize=10, fontweight='bold')
ax.set_yticks(range(len(top_bath)))
ax.set_yticklabels(labels_bath, fontsize=11)
ax.set_xlabel('Persentase Kos yang Menyediakan', fontsize=13)
ax.set_title('Fasilitas Kamar Mandi Paling Umum Ditemukan', fontsize=14, fontweight='bold')
ax.invert_yaxis()
for spine in ['top','right']:
    ax.spines[spine].set_visible(False)
savefig('15_fasilitas_mandi.png')


# ============================================================================
# INSIGHT 16: JUMLAH FASILITAS VS HARGA
# ============================================================================
print('  16. JUMLAH FASILITAS VS HARGA')
print('='*70)

valid_fac = df_valid.dropna(subset=['fac_total_n','price'])
slope_f, intercept_f, r_f, p_f, se_f = linregress(valid_fac['fac_total_n'], valid_fac['price'])

fig, ax = plt.subplots(figsize=(12, 7))
ax.scatter(valid_fac['fac_total_n'], valid_fac['price']/1e6,
           c=valid_fac['price']/1e6, cmap='plasma', alpha=0.6, s=50, edgecolor='black', linewidth=0.3)
x_line_f = np.linspace(valid_fac['fac_total_n'].min(), valid_fac['fac_total_n'].max(), 100)
ax.plot(x_line_f, (slope_f*x_line_f + intercept_f)/1e6, color='red', lw=2.5)
cbar = plt.colorbar(plt.cm.ScalarMappable(cmap='plasma'), ax=ax, label='Harga (Juta Rp)')

# Grouped averages
fac_groups = valid_fac.groupby('fac_total_n')['price'].mean()
ax.scatter(fac_groups.index, fac_groups.values/1e6, color='white', marker='o', s=80, edgecolor='red', lw=2, zorder=5, label='Rata-rata')

ax.set_xlabel('Jumlah Fasilitas', fontsize=13)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Apakah Semakin Banyak Fasilitas Membuat Harga Lebih Mahal?', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))
ax.legend(fontsize=11)

fac_text = (
    f'  Korelasi: r = {r_f:.3f} ({"positif" if r_f>0 else "negatif"})\n'
    f'  p-value: {p_f:.4f} {"(SIGNIFIKAN)" if p_f<0.05 else "(TIDAK)"}\n\n'
    f'  Rata-rata fasilitas: {valid_fac["fac_total_n"].mean():.1f} item\n'
    f'  Rata-rata harga: {fmt_rp(valid_fac["price"].mean())}\n\n'
    f'  ➜ Setiap +1 fasilitas\n'
    f'    harga naik ~Rp {slope_f:,.0f}'
)
add_stats_box(ax, fac_text, xy=(0.55, 0.97), fontsize=10)
savefig('16_fasilitas_vs_harga.png')


# ============================================================================
# INSIGHT 17: PERKIRAAN DP AWAL
# ============================================================================
print('  17. PERKIRAAN DP AWAL')
print('='*70)

dp = df_valid['dp_percentage'].dropna()

fig, ax = plt.subplots(figsize=(12, 7))
ax.hist(dp, bins=15, color=COLORS[0], edgecolor='white', alpha=0.85)
ax.axvline(dp.mean(), color='red', ls='--', lw=2.5, label=f'Rata-rata: {dp.mean():.1f}%')
ax.axvline(dp.median(), color='blue', ls='--', lw=2.5, label=f'Median: {dp.median():.1f}%')
ax.set_xlabel('DP (%)', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Berapa DP Awal yang Perlu Disiapkan Mahasiswa?', fontsize=14, fontweight='bold')
ax.legend(fontsize=12)

dp_text = (
    f'  Rata-rata DP: {dp.mean():.1f}%\n'
    f'  Median DP:   {dp.median():.1f}%\n'
    f'  DP terendah: {dp.min():.0f}%\n'
    f'  DP tertinggi: {dp.max():.0f}%\n\n'
    f'  Contoh DP untuk kos Rp 2,5jt:\n'
    f'  DP 30% (median) → Rp {0.3*2500000:,.0f}\n'
    f'  DP 50% (tertinggi) → Rp {0.5*2500000:,.0f}\n\n'
    f'  ➜ Siapkan Rp 500rb - Rp 1,25jt\n'
    f'     untuk DP awal kos!'
)
add_stats_box(ax, dp_text, xy=(0.55, 0.97), fontsize=10)
savefig('17_perkiraan_dp.png')


# ============================================================================
# INSIGHT 18: KONDISI RATING KOS
# ============================================================================
print('  18. KONDISI RATING KOS')
print('='*70)

rating = df_valid['rating'].dropna()
rating_counts = rating.value_counts().sort_index()

fig, ax = plt.subplots(figsize=(12, 7))
if len(rating_counts) > 0:
    colors_rating = [COLORS[3] if r < 3 else COLORS[2] if r < 4 else COLORS[5] for r in rating_counts.index]
    bars = ax.bar([str(round(r,1)) for r in rating_counts.index], rating_counts.values,
                  color=colors_rating, edgecolor='black', width=0.6)
    for bar, val in zip(bars, rating_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{int(val)}', ha='center', fontsize=12, fontweight='bold')

ax.set_xlabel('Rating', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Bagaimana Kondisi Rating Kos di Sekitar UNUD?', fontsize=14, fontweight='bold')

rating_text = (
    f'  Total kos dengan rating: {len(rating)}\n'
    f'  Rata-rata rating: {rating.mean():.2f} / 5.0\n'
    f'  Median rating:    {rating.median():.2f} / 5.0\n'
    f'  Rating terendah:  {rating.min():.1f}\n'
    f'  Rating tertinggi: {rating.max():.1f}\n\n'
    f'  ➜ Rata-rata rating {rating.mean():.2f}/5.0,\n'
    f'     kualitas kos cukup baik!'
)
add_stats_box(ax, rating_text, xy=(0.55, 0.97), fontsize=10)
savefig('18_kondisi_rating.png')


# ============================================================================
# INSIGHT 19: KOS BANYAK DILIHAT VS HARGA TINGGI
# ============================================================================
print('  19. KOS BANYAK DILIHAT VS HARGA TINGGI')
print('='*70)

valid_view = df_valid.dropna(subset=['view_count','price'])
slope_v, intercept_v, r_v, p_v, se_v = linregress(valid_view['view_count'], valid_view['price'])

fig, ax = plt.subplots(figsize=(12, 7))
sc = ax.scatter(valid_view['view_count'], valid_view['price']/1e6,
                c=valid_view['price']/1e6, cmap='coolwarm', alpha=0.6, s=50, edgecolor='black', linewidth=0.3)
x_line_v = np.linspace(valid_view['view_count'].min(), valid_view['view_count'].max(), 100)
ax.plot(x_line_v, (slope_v*x_line_v + intercept_v)/1e6, color='red', lw=2.5,
        label=f'Regresi (r={r_v:.3f})')
cbar = plt.colorbar(sc, ax=ax, label='Harga (Juta Rp)')
ax.set_xlabel('Jumlah Dilihat', fontsize=13)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Apakah Kos yang Banyak Dilihat Selalu Mahal?', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} jt'))

view_text = (
    f'  Korelasi: r = {r_v:.3f}\n'
    f'  R² = {r_v**2:.3f} (hubungan {"positif" if r_v>0 else "negatif"})\n'
    f'  p-value: {p_v:.4f} {"(SIGNIFIKAN)" if p_v<0.05 else "(TIDAK)"}\n\n'
    f'  Rata-rata dilihat: {valid_view["view_count"].mean():.0f}x\n'
    f'  Paling banyak dilihat: {int(valid_view["view_count"].max()):,}x\n\n'
    f'  ➜ Kos {"mahal" if r_v>0 else "murah"} cenderung\n'
    f'     lebih {"banyak" if r_v>0 else "sedikit"} dilihat'
)
add_stats_box(ax, view_text, xy=(0.55, 0.97), fontsize=10)
savefig('19_dilihat_vs_harga.png')


# ============================================================================
# INSIGHT 20: KOS WORTH IT (HARGA PER M²)
# ============================================================================
print('  20. KOS WORTH IT BERDASARKAN HARGA PER M²')
print('='*70)

valid_worth = df_valid.dropna(subset=['price_per_sqm','price','size_area','nama_kost'])
avg_pps = valid_worth['price_per_sqm'].mean()
med_pps = valid_worth['price_per_sqm'].median()

valid_worth = valid_worth[valid_worth['size_area'] >= 9]
valid_worth = valid_worth[valid_worth['price'] >= 500000]
valid_worth = valid_worth.copy()
valid_worth['worth_score'] = valid_worth['size_area'] / (valid_worth['price'] / 1e6)
top_worth = valid_worth.nlargest(10, 'worth_score')[['nama_kost','price','size_area','price_per_sqm','worth_score','subdistrict']]

print('  10 KOS TER-WORTH IT:')
print(top_worth.to_string())

fig, ax = plt.subplots(figsize=(14, 8))
names_worth = [n[:30]+'..' if len(str(n))>30 else n for n in top_worth['nama_kost'].values]
colors_worth = plt.cm.Greens(np.linspace(0.4, 0.9, 10))

bars = ax.barh(range(10), top_worth['worth_score'].values, color=colors_worth, edgecolor='black', height=0.6)
for i, (_, row) in enumerate(top_worth.iterrows()):
    label = f'{fmt_rp(row["price"])} | {row["size_area"]:.0f}m² | Rp {row["price_per_sqm"]:,.0f}/m²'
    ax.text(row['worth_score'] + 0.1, i, label, va='center', fontsize=9, fontweight='bold')

ax.set_yticks(range(10))
ax.set_yticklabels(names_worth, fontsize=9)
ax.set_xlabel('Worth Score (semakin besar = semakin worth it)', fontsize=12)
ax.set_title('10 Kos Ter-Worth It: Harga per Meter Persegi Terbaik', fontsize=14, fontweight='bold')
ax.invert_yaxis()

worth_text = (
    f'  Rata-rata harga/m²: {fmt_rp(avg_pps)}\n'
    f'  Median harga/m²:    {fmt_rp(med_pps)}\n\n'
    f'  Worth Score = Luas (m²) / Harga (jt)\n'
    f'  Makin besar = makin worth it\n\n'
    f'  ➜ Kos paling worth it:\n'
    f'    {top_worth.iloc[0]["nama_kost"][:25]}\n'
    f'    Harga: {fmt_rp(top_worth.iloc[0]["price"])}\n'
    f'    Luas: {top_worth.iloc[0]["size_area"]:.0f} m²\n'
    f'    Rp {top_worth.iloc[0]["price_per_sqm"]:,.0f}/m²'
)
add_stats_box(ax, worth_text, xy=(0.55, 0.97), fontsize=10)
savefig('20_worth_it_harga_m2.png')


# ============================================================================
# RINGKASAN SEMUA ANGKA (Poster-ready table)
# ============================================================================
print('\n' + '='*70)
print('  RINGKASAN UNTUK POSTER')
print('='*70)

summary = f'''
{"="*60}
  20 INSIGHT KOS UNTUK MAHASISWA - RINGKASAN ANGKA
{"="*60}

1. GAMBARAN HARGA BULANAN
   Rata-rata: {fmt_rp(p.mean())}  |  Median: {fmt_rp(p.median())}
   Termurah: {fmt_rp(p.min())}  |  Termahal: {fmt_rp(p.max())}
   Q1 (25%): {fmt_rp(p.quantile(0.25))}  |  Q3 (75%): {fmt_rp(p.quantile(0.75))}

2. BUDGET AMAN MAHASISWA
   ≤ Rp 1,5jt: {budget_counts[1]} kos ({budget_pcts[1]:.1f}%)
   ≤ Rp 2,0jt: {budget_counts[2]} kos ({budget_pcts[2]:.1f}%)
   ≤ Rp 2,5jt: {budget_counts[3]} kos ({budget_pcts[3]:.1f}%) ★ AMAN
   ≤ Rp 3,0jt: {budget_counts[4]} kos ({budget_pcts[4]:.1f}%)

3. RENTANG HARGA WAJAR (IQR)
   {fmt_rp(q1)} - {fmt_rp(q3)} (50% kos di rentang ini)

4. KATEGORI HARGA
   Murah (<Rp1,5jt): {cat_counts[labels_bin[0]]} kos ({cat_counts[labels_bin[0]]/len(p)*100:.1f}%)
   Terjangkau: {cat_counts[labels_bin[1]]} kos ({cat_counts[labels_bin[1]]/len(p)*100:.1f}%)
   Standar: {cat_counts[labels_bin[2]]} kos ({cat_counts[labels_bin[2]]/len(p)*100:.1f}%)
   Mahal: {cat_counts[labels_bin[3]]} kos ({cat_counts[labels_bin[3]]/len(p)*100:.1f}%)
   Premium: {cat_counts[labels_bin[4]]} kos ({cat_counts[labels_bin[4]]/len(p)*100:.1f}%)

5. JIMBARAN VS SUDIRMAN
   Jimbaran: {counts[0]} kos, rata-rata {fmt_rp(means[0])}
   Sudirman: {counts[1]} kos, rata-rata {fmt_rp(means[1])}

6. HARGA PER KECAMATAN (rata-rata)
   {chr(10).join(f"   {s}: {fmt_rp(g6.mean()[s])}" for s in g6.mean().sort_values(ascending=False).index)}

7. GENDER
   Campur: {g7.count().get('Campur',0)} kos, rata-rata {fmt_rp(g7.mean().get('Campur',0))}
   Putri: {g7.count().get('Putri',0)} kos, rata-rata {fmt_rp(g7.mean().get('Putri',0))}
   t-test: p={gender_ttest_p:.2e} {"(SIGNIFIKAN)" if gender_ttest_p is not None and gender_ttest_p<0.05 else "(TIDAK)"}

8. PELUANG BUDGET ≤ Rp 2,5jt
   {pct_within:.1f}% kos masuk budget (1 dari 2 kos)

9. KOS DI BAWAH Rp 2jt
   {pct_2jt:.1f}% kos ({under_2jt} dari {len(p)})

10. TERMURAH: {fmt_rp(df_valid["price"].min())}  |  TERMAHAL: {fmt_rp(df_valid["price"].max())}
    Rasio termahal/termurah: {df_valid["price"].max()/df_valid["price"].min():.1f}x

11. UKURAN vs HARGA: r = {r_val:.3f} {"(berpengaruh)" if p_val<0.05 else "(tidak)"}

12. RUMUS: Harga = {intercept:,.0f} + {slope:.0f} × Luas (m²)

13-15. FASILITAS TERPOPULER:
    Kamar: {labels_room[0]} ({fac_pct.values[0]:.1f}%)
    Umum: {labels_share[0]} ({share_pct.values[0]:.1f}%)
    Mandi: {labels_bath[0]} ({bath_pct.values[0]:.1f}%)

16. FASILITAS vs HARGA: r = {r_f:.3f}

17. DP: rata-rata {dp.mean():.1f}%, median {dp.median():.1f}%

18. RATING: rata-rata {rating.mean():.2f}/5.0

19. DILIHAT vs HARGA: r = {r_v:.3f}

20. HARGA/M² TERBAIK: {top_worth.iloc[0]["nama_kost"][:30]}
    Rp {top_worth.iloc[0]["price_per_sqm"]:,.0f}/m² | {top_worth.iloc[0]["size_area"]:.0f}m²
'''
print(summary)

with open(os.path.join(OUT, 'ringkasan_poster.txt'), 'w') as f:
    f.write(summary)

print(f'\n  Semua grafik tersimpan di: {OUT}/')
print(f'  Ringkasan angka: {OUT}/ringkasan_poster.txt')
print(f'\n{"="*70}')
print(f'  SELESAI!')
print(f'='*70)
