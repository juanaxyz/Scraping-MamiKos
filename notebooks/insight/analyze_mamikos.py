"""
=============================================================================
ANALISIS KOST JIMBARAN - 39 INSIGHT + STATISTIK DESKRIPTIF
=============================================================================
Dataset: mamikos_all.csv (241 kost di Jimbaran, Badung)
Output : notebooks/insight/output/*.png
=============================================================================
"""

import os, re, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from scipy.stats import linregress, f_oneway, shapiro, ttest_ind
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error

warnings.filterwarnings('ignore')
sns.set_theme(style='whitegrid', font_scale=1.1)
PALETTE = sns.color_palette('Set2', 10)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)


def savefig(name):
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, name), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  [saved] {name}')


def section(title):
    print(f'\n{"="*70}')
    print(f'  {title}')
    print(f'{"="*70}')


def desc_stats(series, label=''):
    s = series.dropna()
    d = {
        'count': len(s), 'mean': s.mean(), 'median': s.median(),
        'std': s.std(), 'min': s.min(), 'Q1': s.quantile(0.25),
        'Q3': s.quantile(0.75), 'max': s.max(),
        'skewness': s.skew(), 'kurtosis': s.kurtosis(),
    }
    print(f'\n  Statistik Deskriptif{": "+label if label else ""}:')
    for k, v in d.items():
        if k == 'count':
            print(f'    {k:>10s} : {v}')
        else:
            print(f'    {k:>10s} : {v:,.2f}')
    return d


def parse_price(s):
    if pd.isna(s):
        return None
    s_clean = str(s).replace('.', '').replace('Rp', '').replace('/bulan', '').strip()
    nums = re.findall(r'\d+', s_clean)
    return int(nums[0]) if nums else None


def parse_size(s):
    if pd.isna(s):
        return np.nan, np.nan
    m = re.match(r'([\d.]+)\s*x\s*([\d.]+)', str(s))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)


def clean_subdistrict(x):
    if pd.isna(x):
        return x
    return str(x).replace('Kecamatan ', '')


# =============================================================================
# LOAD & CLEAN
# =============================================================================
print('\n' + '='*70)
print('  LOADING DATA')
print('='*70)

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'mamikos_all.csv')
df = pd.read_csv(CSV_PATH)
print(f'  Loaded {len(df)} rows x {len(df.columns)} columns')

df['price'] = df['harga_real_detail'].apply(parse_price)
df[['size_w', 'size_l']] = df['size'].apply(lambda x: pd.Series(parse_size(x)))
df['size_area'] = df['size_w'] * df['size_l']
df['price_per_sqm'] = df['price'] / df['size_area']
df['subdistrict'] = df['area_subdistrict'].apply(clean_subdistrict)
df['gender_label'] = df['gender'].map({0: 'Campur', 1: 'Putri', 2: 'Putri'})

# Convert string columns to numeric
for col in ['dist_to_nearest_supermarket_km', 'dist_to_nearest_terminal_km']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

bath_cols = [c for c in df.columns if c.startswith('fac_bath_')]
room_cols = [c for c in df.columns if c.startswith('fac_room_')]
share_cols = [c for c in df.columns if c.startswith('fac_share_')]
df['fac_bath_n'] = df[bath_cols].sum(axis=1)
df['fac_room_n'] = df[room_cols].sum(axis=1)
df['fac_share_n'] = df[share_cols].sum(axis=1)
df['fac_total_n'] = df['fac_bath_n'] + df['fac_room_n'] + df['fac_share_n']

df['price_tier'] = pd.cut(df['price'], bins=[0, 1500000, 2500000, 3500000, 5000000, float('inf')],
    labels=['<1.5jt', '1.5-2.5jt', '2.5-3.5jt', '3.5-5jt', '>5jt'])
df['size_cat'] = pd.cut(df['size_area'], bins=[0, 12, 16, 20, 30, float('inf')],
    labels=['S (<12m2)', 'M (12-16m2)', 'L (16-20m2)', 'XL (20-30m2)', 'XXL (>30m2)'])

df_valid = df.dropna(subset=['price'])
print(f'  Valid price records: {len(df_valid)}')


# =============================================================================
# INSIGHT 1: DISTRIBUSI HARGA BULANAN
# =============================================================================
section('1. DISTRIBUSI HARGA BULANAN')
d1 = desc_stats(df_valid['price'], 'Harga Bulanan (Rp)')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df_valid['price']/1e6, bins=30, color=PALETTE[0], edgecolor='white', alpha=0.8)
axes[0].axvline(d1['mean']/1e6, color='red', ls='--', lw=2, label=f'Mean: Rp {d1["mean"]/1e6:.2f}jt')
axes[0].axvline(d1['median']/1e6, color='blue', ls='--', lw=2, label=f'Median: Rp {d1["median"]/1e6:.2f}jt')
axes[0].set_xlabel('Harga Bulanan (Rp Juta)')
axes[0].set_ylabel('Frekuensi')
axes[0].set_title('Distribusi Harga Bulanan Kost Jimbaran')
axes[0].legend()
df_valid['price'].plot.box(ax=axes[1], vert=True, patch_artist=True,
    boxprops=dict(facecolor=PALETTE[0], alpha=0.6))
axes[1].set_ylabel('Harga (Rp)')
axes[1].set_title('Boxplot Harga Bulanan')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
savefig('01_price_distribution.png')


# =============================================================================
# INSIGHT 2: HARGA PER SUBDISTRICT
# =============================================================================
section('2. HARGA PER SUBDISTRICT')
g2 = df_valid.groupby('subdistrict')['price']
d2 = g2.agg(['count', 'mean', 'median', 'std', 'min', 'max'])
print(d2.to_string())

fig, ax = plt.subplots(figsize=(10, 5))
order = df_valid.groupby('subdistrict')['price'].median().sort_values(ascending=False).index
sns.boxplot(data=df_valid, x='subdistrict', y='price', order=order, palette='Set2', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
ax.set_xlabel('Subdistrict')
ax.set_ylabel('Harga Bulanan (Rp)')
ax.set_title('Distribusi Harga per Subdistrict')
plt.xticks(rotation=30, ha='right')
savefig('02_price_by_subdistrict.png')


# =============================================================================
# INSIGHT 3: HARGA PER GENDER
# =============================================================================
section('3. HARGA PER GENDER (Campur vs Putri)')
g3 = df_valid.groupby('gender_label')['price']
d3 = g3.agg(['count', 'mean', 'median', 'std', 'min', 'max'])
print(d3.to_string())

fig, ax = plt.subplots(figsize=(7, 5))
sns.boxplot(data=df_valid, x='gender_label', y='price', palette='Set2', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
ax.set_xlabel('Gender')
ax.set_ylabel('Harga Bulanan (Rp)')
ax.set_title('Distribusi Harga berdasarkan Gender')
savefig('03_price_by_gender.png')


# =============================================================================
# INSIGHT 4-10: HARGA VS JARAK (7 POI)
# =============================================================================
section('4-10. HARGA VS JARAK KE POI TERDEKAT')
dist_cols = [
    ('dist_to_nearest_university_km', 'Universitas'),
    ('dist_to_nearest_hospital_km', 'Rumah Sakit'),
    ('dist_to_nearest_clinic_km', 'Klinik'),
    ('dist_to_nearest_mall_km', 'Mall'),
    ('dist_to_nearest_supermarket_km', 'Supermarket'),
    ('dist_to_nearest_terminal_km', 'Terminal'),
    ('jarak_bandara_ngurah_rai_km', 'Bandara Ngurah Rai'),
]

fig, axes = plt.subplots(3, 3, figsize=(18, 15))
axes = axes.flatten()
corr_results = []
for i, (col, label) in enumerate(dist_cols):
    valid = df_valid[[col, 'price']].dropna()
    slope, intercept, r, p, se = linregress(valid[col], valid['price'])
    ax = axes[i]
    ax.scatter(valid[col], valid['price']/1e6, alpha=0.5, s=30, c=PALETTE[i % 8])
    x_line = np.linspace(valid[col].min(), valid[col].max(), 100)
    ax.plot(x_line, (slope * x_line + intercept)/1e6, 'r--', lw=2)
    ax.set_xlabel(f'Jarak ke {label} (km)')
    ax.set_ylabel('Harga (Rp Juta)')
    ax.set_title(f'Harga vs Jarak {label}\nR2={r**2:.4f}, r={r:.4f}, p={p:.2e}')
    corr_results.append({'POI': label, 'r': r, 'R2': r**2, 'slope': slope, 'p_value': p})
    print(f'  {label:20s}: r={r:+.4f}, R2={r**2:.4f}, p={p:.2e}, slope={slope:+,.0f} Rp/km')

for j in range(len(dist_cols), len(axes)):
    fig.delaxes(axes[j])
plt.suptitle('Korelasi Harga vs Jarak POI Terdekat', y=1.01, fontsize=14, fontweight='bold')
savefig('04_10_price_vs_distance.png')

corr_df = pd.DataFrame(corr_results)
print('\n' + corr_df.to_string(index=False))


# =============================================================================
# INSIGHT 11: HARGA VS UKURAN KAMAR
# =============================================================================
section('11. HARGA VS UKURAN KAMAR')
valid11 = df_valid[['size_area', 'price']].dropna()
d11_size = desc_stats(valid11['size_area'], 'Ukuran Kamar (m2)')
d11_ppsm = desc_stats(df_valid['price_per_sqm'].dropna(), 'Harga per m2')
slope11, int11, r11, p11, _ = linregress(valid11['size_area'], valid11['price'])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(valid11['size_area'], valid11['price']/1e6, alpha=0.5, s=30, c=PALETTE[0])
x11 = np.linspace(valid11['size_area'].min(), valid11['size_area'].max(), 100)
axes[0].plot(x11, (slope11*x11+int11)/1e6, 'r--', lw=2,
    label=f'y={slope11/1e3:.1f}k*x + {int11/1e6:.2f}jt\nR2={r11**2:.4f}')
axes[0].set_xlabel('Ukuran Kamar (m2)')
axes[0].set_ylabel('Harga (Rp Juta)')
axes[0].set_title('Harga vs Ukuran Kamar')
axes[0].legend()
df_valid['price_per_sqm'].plot.box(ax=axes[1], vert=True, patch_artist=True,
    boxprops=dict(facecolor=PALETTE[1], alpha=0.6))
axes[1].set_ylabel('Harga per m2 (Rp)')
axes[1].set_title('Distribusi Harga per m2')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e3:.0f}k'))
savefig('11_price_vs_size.png')


# =============================================================================
# INSIGHT 12: HARGA VS TAHUN BANGUNAN
# =============================================================================
section('12. HARGA VS TAHUN BANGUNAN')
valid12 = df_valid[['building_year', 'price']].dropna()
d12 = desc_stats(valid12['building_year'], 'Tahun Bangunan')
slope12, int12, r12, p12, _ = linregress(valid12['building_year'], valid12['price'])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(valid12['building_year'], valid12['price']/1e6, alpha=0.5, s=30, c=PALETTE[2])
x12 = np.linspace(valid12['building_year'].min(), valid12['building_year'].max(), 100)
axes[0].plot(x12, (slope12*x12+int12)/1e6, 'r--', lw=2,
    label=f'R2={r12**2:.4f}, r={r12:.4f}')
axes[0].set_xlabel('Tahun Bangunan')
axes[0].set_ylabel('Harga (Rp Juta)')
axes[0].set_title('Harga vs Tahun Bangunan')
axes[0].legend()
valid12['building_year'].value_counts().sort_index().plot.bar(ax=axes[1], color=PALETTE[2], alpha=0.7)
axes[1].set_xlabel('Tahun Bangunan')
axes[1].set_ylabel('Jumlah Kost')
axes[1].set_title('Distribusi Tahun Bangunan')
plt.xticks(rotation=45)
savefig('12_price_vs_building_year.png')


# =============================================================================
# INSIGHT 13: TOP 10 FASILITAS KAMAR
# =============================================================================
section('13. TOP 10 FASILITAS KAMAR')
room_sums = df[room_cols].sum().sort_values(ascending=False).head(10)
for col, cnt in room_sums.items():
    print(f'  {col:40s}: {cnt:3d} ({cnt/len(df)*100:5.1f}%)')

fig, ax = plt.subplots(figsize=(10, 6))
labels = [c.replace('fac_room_', '') for c in room_sums.index]
ax.barh(labels[::-1], room_sums.values[::-1], color=PALETTE[3], alpha=0.8)
ax.set_xlabel('Jumlah Kost')
ax.set_title('Top 10 Fasilitas Kamar yang Paling Umum')
for i, v in enumerate(room_sums.values[::-1]):
    ax.text(v + 1, i, f'{v} ({v/len(df)*100:.0f}%)', va='center', fontsize=9)
savefig('13_top_room_facilities.png')


# =============================================================================
# INSIGHT 14: TOP 10 FASILITAS BERBAGI
# =============================================================================
section('14. TOP 10 FASILITAS BERBAGI')
share_sums = df[share_cols].sum().sort_values(ascending=False).head(10)
for col, cnt in share_sums.items():
    print(f'  {col:40s}: {cnt:3d} ({cnt/len(df)*100:5.1f}%)')

fig, ax = plt.subplots(figsize=(10, 6))
labels = [c.replace('fac_share_', '') for c in share_sums.index]
ax.barh(labels[::-1], share_sums.values[::-1], color=PALETTE[4], alpha=0.8)
ax.set_xlabel('Jumlah Kost')
ax.set_title('Top 10 Fasilitas Berbagi yang Paling Umum')
for i, v in enumerate(share_sums.values[::-1]):
    ax.text(v + 1, i, f'{v} ({v/len(df)*100:.0f}%)', va='center', fontsize=9)
savefig('14_top_share_facilities.png')


# =============================================================================
# INSIGHT 15: TOP FASILITAS KAMAR MANDI
# =============================================================================
section('15. TOP FASILITAS KAMAR MANDI')
bath_sums = df[bath_cols].sum().sort_values(ascending=False).head(10)
for col, cnt in bath_sums.items():
    print(f'  {col:40s}: {cnt:3d} ({cnt/len(df)*100:5.1f}%)')

fig, ax = plt.subplots(figsize=(10, 5))
labels = [c.replace('fac_bath_', '') for c in bath_sums.index]
ax.barh(labels[::-1], bath_sums.values[::-1], color=PALETTE[5], alpha=0.8)
ax.set_xlabel('Jumlah Kost')
ax.set_title('Top Fasilitas Kamar Mandi')
for i, v in enumerate(bath_sums.values[::-1]):
    ax.text(v + 1, i, f'{v} ({v/len(df)*100:.0f}%)', va='center', fontsize=9)
savefig('15_top_bath_facilities.png')


# =============================================================================
# INSIGHT 16: JUMLAH FASILITAS VS HARGA
# =============================================================================
section('16. JUMLAH FASILITAS VS HARGA')
fac_types = [
    ('fac_bath_n', 'Fasilitas Kamar Mandi'),
    ('fac_room_n', 'Fasilitas Kamar'),
    ('fac_share_n', 'Fasilitas Berbagi'),
    ('fac_total_n', 'Total Fasilitas'),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
print('  Correlations:')
for idx, (col, label) in enumerate(fac_types):
    ax = axes[idx // 2][idx % 2]
    valid = df_valid[[col, 'price']].dropna()
    r = valid[col].corr(valid['price'])
    ax.scatter(valid[col], valid['price']/1e6, alpha=0.4, s=25, c=PALETTE[idx])
    ax.set_xlabel(f'Jumlah {label}')
    ax.set_ylabel('Harga (Rp Juta)')
    ax.set_title(f'{label} vs Harga (r={r:.4f})')
    print(f'    {label:25s}: r={r:+.4f}')
savefig('16_facility_count_vs_price.png')


# =============================================================================
# INSIGHT 17: DISTRIBUSI DP PERCENTAGE
# =============================================================================
section('17. DISTRIBUSI DP PERCENTAGE')
valid17 = df_valid['dp_percentage'].dropna()
d17 = desc_stats(valid17, 'DP Percentage')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(valid17, bins=20, color=PALETTE[6], edgecolor='white', alpha=0.8)
axes[0].axvline(d17['mean'], color='red', ls='--', label=f'Mean: {d17["mean"]:.1f}%')
axes[0].axvline(d17['median'], color='blue', ls='--', label=f'Median: {d17["median"]:.1f}%')
axes[0].set_xlabel('DP Percentage (%)')
axes[0].set_ylabel('Frekuensi')
axes[0].set_title('Distribusi DP Percentage')
axes[0].legend()
valid17.plot.box(ax=axes[1], vert=True, patch_artist=True,
    boxprops=dict(facecolor=PALETTE[6], alpha=0.6))
axes[1].set_ylabel('DP (%)')
axes[1].set_title('Boxplot DP Percentage')
savefig('17_dp_percentage.png')


# =============================================================================
# INSIGHT 18: ANALISIS RATING
# =============================================================================
section('18. ANALISIS RATING')
d18 = desc_stats(df_valid['rating'], 'Rating')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df_valid['rating'], bins=20, color=PALETTE[7], edgecolor='white', alpha=0.8)
axes[0].set_xlabel('Rating')
axes[0].set_ylabel('Frekuensi')
axes[0].set_title('Distribusi Rating')
axes[1].scatter(df_valid['rating'], df_valid['price']/1e6, alpha=0.4, s=25, c=PALETTE[7])
r18 = df_valid['rating'].corr(df_valid['price'])
axes[1].set_xlabel('Rating')
axes[1].set_ylabel('Harga (Rp Juta)')
axes[1].set_title(f'Rating vs Harga (r={r18:.4f})')
savefig('18_rating_analysis.png')


# =============================================================================
# INSIGHT 19: VIEW COUNT & LOVE COUNT VS HARGA
# =============================================================================
section('19. ANALISIS VIEW COUNT & LOVE COUNT')
d19v = desc_stats(df_valid['view_count'], 'View Count')
d19l = desc_stats(df_valid['love_count'], 'Love Count')
r19v = df_valid['view_count'].corr(df_valid['price'])
r19l = df_valid['love_count'].corr(df_valid['price'])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(df_valid['view_count'], df_valid['price']/1e6, alpha=0.4, s=25, c=PALETTE[0])
axes[0].set_xlabel('View Count')
axes[0].set_ylabel('Harga (Rp Juta)')
axes[0].set_title(f'View Count vs Harga (r={r19v:.4f})')
axes[1].scatter(df_valid['love_count'], df_valid['price']/1e6, alpha=0.4, s=25, c=PALETTE[1])
axes[1].set_xlabel('Love Count')
axes[1].set_ylabel('Harga (Rp Juta)')
axes[1].set_title(f'Love Count vs Harga (r={r19l:.4f})')
savefig('19_view_love_analysis.png')
print(f'  View Count vs Price: r={r19v:+.4f}')
print(f'  Love Count vs Price: r={r19l:+.4f}')


# =============================================================================
# INSIGHT 20: HARGA PER m2
# =============================================================================
section('20. HARGA PER m2 (PRICE PER SQM)')
d20 = desc_stats(df_valid['price_per_sqm'].dropna(), 'Harga per m2')
g20 = df_valid.groupby('subdistrict')['price_per_sqm'].agg(['mean', 'median', 'std', 'count'])
print('\nHarga per m2 per subdistrict:')
print(g20.to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df_valid['price_per_sqm'].dropna()/1e3, bins=30, color=PALETTE[2], edgecolor='white')
axes[0].axvline(d20['mean']/1e3, color='red', ls='--', label=f'Mean: {d20["mean"]/1e3:.0f}k Rp/m2')
axes[0].axvline(d20['median']/1e3, color='blue', ls='--', label=f'Median: {d20["median"]/1e3:.0f}k Rp/m2')
axes[0].set_xlabel('Harga per m2 (Rp Ribu)')
axes[0].set_ylabel('Frekuensi')
axes[0].set_title('Distribusi Harga per m2')
axes[0].legend()
order20 = df_valid.groupby('subdistrict')['price_per_sqm'].median().sort_values(ascending=False).index
sns.boxplot(data=df_valid, x='subdistrict', y='price_per_sqm', order=order20, palette='Set2', ax=axes[1])
axes[1].set_xlabel('Subdistrict')
axes[1].set_ylabel('Harga per m2 (Rp)')
axes[1].set_title('Harga per m2 per Subdistrict')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e3:.0f}k'))
plt.xticks(rotation=30, ha='right')
savefig('20_price_per_sqm.png')


# =============================================================================
# INSIGHT 21: DISTRIBUSI UKURAN KAMAR
# =============================================================================
section('21. DISTRIBUSI UKURAN KAMAR')
d21 = desc_stats(df_valid['size_area'].dropna(), 'Ukuran Kamar (m2)')
size_counts = df_valid['size_cat'].value_counts().sort_index()
print('\nDistribusi kategori ukuran:')
print(size_counts.to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df_valid['size_area'].dropna(), bins=30, color=PALETTE[3], edgecolor='white')
axes[0].axvline(d21['mean'], color='red', ls='--', label=f'Mean: {d21["mean"]:.1f} m2')
axes[0].axvline(d21['median'], color='blue', ls='--', label=f'Median: {d21["median"]:.1f} m2')
axes[0].set_xlabel('Ukuran Kamar (m2)')
axes[0].set_ylabel('Frekuensi')
axes[0].set_title('Distribusi Ukuran Kamar')
axes[0].legend()
size_counts.plot.bar(ax=axes[1], color=PALETTE[3], alpha=0.7)
axes[1].set_xlabel('Kategori Ukuran')
axes[1].set_ylabel('Jumlah Kost')
axes[1].set_title('Frekuensi per Kategori Ukuran')
plt.xticks(rotation=30)
savefig('21_size_distribution.png')


# =============================================================================
# INSIGHT 22: HEATMAP KORELASI
# =============================================================================
section('22. HEATMAP KORELASI')
numeric_cols = ['price', 'size_area', 'available_room', 'building_year',
    'dist_to_nearest_clinic_km', 'dist_to_nearest_hospital_km',
    'dist_to_nearest_mall_km', 'dist_to_nearest_supermarket_km',
    'dist_to_nearest_terminal_km', 'dist_to_nearest_university_km',
    'jarak_bandara_ngurah_rai_km', 'jarak_unud_jimbaran_km',
    'rating', 'review_count', 'love_count', 'view_count',
    'dp_percentage', 'fac_total_n', 'price_per_sqm']
corr_matrix = df_valid[numeric_cols].corr()

fig, ax = plt.subplots(figsize=(16, 14))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
    center=0, vmin=-1, vmax=1, square=True, linewidths=0.5, ax=ax,
    annot_kws={'size': 7})
ax.set_title('Heatmap Korelasi Variabel Numerik', fontsize=14, fontweight='bold')
savefig('22_correlation_heatmap.png')


# =============================================================================
# INSIGHT 23: KAMAR TERSEDIA VS HARGA
# =============================================================================
section('23. KAMAR TERSEDIA VS HARGA')
g23 = df_valid.groupby('available_room')['price'].agg(['count', 'mean', 'median', 'std'])
print(g23.to_string())

fig, ax = plt.subplots(figsize=(8, 5))
order23 = sorted(df_valid['available_room'].dropna().unique())
sns.boxplot(data=df_valid, x='available_room', y='price', order=order23, palette='Set2', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
ax.set_xlabel('Jumlah Kamar Tersedia')
ax.set_ylabel('Harga Bulanan (Rp)')
ax.set_title('Distribusi Harga berdasarkan Ketersediaan Kamar')
savefig('23_available_room_vs_price.png')


# =============================================================================
# INSIGHT 24: TOP 10 KOST TERMAHAL & TERMURAH
# =============================================================================
section('24. TOP 10 KOST TERMAHAL & TERMURAH')
top_exp = df_valid.nlargest(10, 'price')[['nama_kost', 'price', 'subdistrict', 'size', 'gender_label', 'fac_total_n']]
top_cheap = df_valid.nsmallest(10, 'price')[['nama_kost', 'price', 'subdistrict', 'size', 'gender_label', 'fac_total_n']]

print('\n  TOP 10 KOST TERMAHAL:')
for _, row in top_exp.iterrows():
    print(f'    {str(row["nama_kost"])[:45]:45s} | Rp {row["price"]:>10,.0f} | {row["size"]} | {row["subdistrict"]}')

print('\n  TOP 10 KOST TERMURAH:')
for _, row in top_cheap.iterrows():
    print(f'    {str(row["nama_kost"])[:45]:45s} | Rp {row["price"]:>10,.0f} | {row["size"]} | {row["subdistrict"]}')

fig, axes = plt.subplots(1, 2, figsize=(18, 6))
axes[0].barh(top_exp['nama_kost'].str[:35][::-1], top_exp['price'][::-1]/1e6, color='crimson', alpha=0.7)
axes[0].set_xlabel('Harga (Rp Juta)')
axes[0].set_title('Top 10 Kost Termahal')
for i, v in enumerate(top_exp['price'][::-1]/1e6):
    axes[0].text(v + 0.05, i, f'Rp {v:.2f}jt', va='center', fontsize=8)
axes[1].barh(top_cheap['nama_kost'].str[:35][::-1], top_cheap['price'][::-1]/1e6, color='forestgreen', alpha=0.7)
axes[1].set_xlabel('Harga (Rp Juta)')
axes[1].set_title('Top 10 Kost Termurah')
for i, v in enumerate(top_cheap['price'][::-1]/1e6):
    axes[1].text(v + 0.01, i, f'Rp {v:.2f}jt', va='center', fontsize=8)
savefig('24_top_cheapest_expensive.png')


# =============================================================================
# INSIGHT 25: CONFIDENCE INTERVAL 95% MEAN HARGA
# =============================================================================
section('25. CONFIDENCE INTERVAL 95% MEAN HARGA')
n25 = len(df_valid['price'])
mean25 = df_valid['price'].mean()
se25 = df_valid['price'].std() / np.sqrt(n25)
ci25 = stats.t.interval(0.95, df=n25-1, loc=mean25, scale=se25)

print(f'  n                     = {n25}')
print(f'  Mean                  = Rp {mean25:,.0f}')
print(f'  Std Dev               = Rp {df_valid["price"].std():,.0f}')
print(f'  Standard Error        = Rp {se25:,.0f}')
print(f'  95% CI Lower Bound    = Rp {ci25[0]:,.0f}')
print(f'  95% CI Upper Bound    = Rp {ci25[1]:,.0f}')
print(f'  Interpretasi: Dengan keyakinan 95%, rata-rata harga kost')
print(f'  Jimbaran berada di antara Rp {ci25[0]/1e6:.2f}jt - Rp {ci25[1]/1e6:.2f}jt')


# =============================================================================
# INSIGHT 26: UJI NORMALITAS HARGA
# =============================================================================
section('26. UJI NORMALITAS HARGA')
stat26, p26 = shapiro(df_valid['price'])
print(f'  Shapiro-Wilk Statistic = {stat26:.6f}')
print(f'  p-value                = {p26:.6e}')
is_normal = 'Yes (p > 0.05)' if p26 > 0.05 else 'No (p < 0.05)'
print(f'  Normal Distribution    : {is_normal}')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df_valid['price']/1e6, bins=30, density=True, color=PALETTE[0], alpha=0.7, edgecolor='white')
x_range = np.linspace(df_valid['price'].min(), df_valid['price'].max(), 100)
axes[0].plot(x_range/1e6, stats.norm.pdf(x_range, mean25, df_valid['price'].std())/1e6, 'r-', lw=2, label='Normal curve')
axes[0].set_xlabel('Harga (Rp Juta)')
axes[0].set_ylabel('Density')
axes[0].set_title(f'Overlay Normal Curve\nShapiro-Wilk p={p26:.2e}')
axes[0].legend()
stats.probplot(df_valid['price'], dist='norm', plot=axes[1])
axes[1].set_title('Q-Q Plot Harga')
axes[1].get_lines()[0].set_markersize(3)
savefig('26_normality_test.png')


# =============================================================================
# INSIGHT 27: DISTRIBUSI LOG-NORMAL HARGA
# =============================================================================
section('27. DISTRIBUSI LOG-NORMAL HARGA')
log_price = np.log(df_valid['price'])
stat27, p27 = shapiro(log_price)
print(f'  Log-Harga Mean         = {log_price.mean():.4f}')
print(f'  Log-Harga Std          = {log_price.std():.4f}')
print(f'  Shapiro-Wilk (log)     = {stat27:.6f}')
print(f'  p-value (log)          = {p27:.6e}')
better = 'Better' if p27 > p26 else 'Not better'
print(f'  Log-Normal Fit         : {better} than normal')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(log_price, bins=30, density=True, color=PALETTE[1], alpha=0.7, edgecolor='white')
x_ln = np.linspace(log_price.min(), log_price.max(), 100)
axes[0].plot(x_ln, stats.norm.pdf(x_ln, log_price.mean(), log_price.std()), 'r-', lw=2)
axes[0].set_xlabel('ln(Harga)')
axes[0].set_ylabel('Density')
axes[0].set_title(f'Distribusi Log-Harga\nShapiro-Wilk p={p27:.2e}')
stats.probplot(log_price, dist='norm', plot=axes[1])
axes[1].set_title('Q-Q Plot Log-Harga')
axes[1].get_lines()[0].set_markersize(3)
savefig('27_log_normal_test.png')


# =============================================================================
# INSIGHT 28: T-TEST CAMPUR vs PUTRI
# =============================================================================
section('28. UJI BEDA HARGA: CAMPUR vs PUTRI (Welch t-test)')
campur28 = df_valid[df_valid['gender_label'] == 'Campur']['price']
putri28 = df_valid[df_valid['gender_label'] == 'Putri']['price']

print(f'  Campur: n={len(campur28)}, mean=Rp {campur28.mean():,.0f}, std=Rp {campur28.std():,.0f}')
print(f'  Putri : n={len(putri28)}, mean=Rp {putri28.mean():,.0f}, std=Rp {putri28.std():,.0f}')
print(f'  Selisih Mean          = Rp {campur28.mean() - putri28.mean():,.0f}')

t28, p28 = ttest_ind(campur28, putri28, equal_var=False)
print(f'  t-statistic           = {t28:.4f}')
print(f'  p-value               = {p28:.6e}')
sig = 'Yes' if p28 < 0.05 else 'No'
print(f'  Significant at alpha=0.05: {sig}')

fig, ax = plt.subplots(figsize=(7, 5))
sns.boxplot(data=df_valid, x='gender_label', y='price', palette='Set2', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
ax.set_xlabel('Gender')
ax.set_ylabel('Harga (Rp)')
ax.set_title(f'Perbandingan Harga Campur vs Putri\nt={t28:.2f}, p={p28:.2e}')
savefig('28_ttest_gender.png')


# =============================================================================
# INSIGHT 29: REGRESI LINEAR HARGA ~ UKURAN KAMAR
# =============================================================================
section('29. REGRESI LINEAR: HARGA ~ UKURAN KAMAR')
valid29 = df_valid[['size_area', 'price']].dropna()
X29 = valid29['size_area'].values.reshape(-1, 1)
y29 = valid29['price'].values

slope29, int29, r29, p29, se29 = linregress(valid29['size_area'], valid29['price'])
r2_29 = r29 ** 2
y_pred29 = slope29 * valid29['size_area'].values + int29
rmse29 = np.sqrt(mean_squared_error(y29, y_pred29))

print(f'  Regression Equation: Price = {slope29:,.0f} * Size + {int29:,.0f}')
print(f'  Slope (b1)         = {slope29:,.0f} Rp/m2')
print(f'  Intercept (b0)     = {int29:,.0f} Rp')
print(f'  R                   = {r29:.4f}')
print(f'  R2                  = {r2_29:.4f}')
print(f'  RMSE                = Rp {rmse29:,.0f}')
print(f'  p-value             = {p29:.4e}')
print(f'  Interpretasi: Setiap penambahan 1 m2 ukuran kamar')
print(f'  berkorelasi dengan kenaikan harga sebesar Rp {slope29:,.0f}')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(valid29['size_area'], valid29['price']/1e6, alpha=0.4, s=30, c=PALETTE[0])
x29 = np.linspace(valid29['size_area'].min(), valid29['size_area'].max(), 100)
axes[0].plot(x29, (slope29*x29+int29)/1e6, 'r--', lw=2,
    label=f'Price = {slope29/1e3:.1f}k*Size + {int29/1e6:.2f}jt\nR2={r2_29:.4f}')
axes[0].set_xlabel('Ukuran Kamar (m2)')
axes[0].set_ylabel('Harga (Rp Juta)')
axes[0].set_title('Regresi: Harga vs Ukuran Kamar')
axes[0].legend()
residuals29 = y29 - y_pred29
axes[1].scatter(y_pred29/1e6, residuals29/1e6, alpha=0.4, s=30, c=PALETTE[2])
axes[1].axhline(0, color='red', ls='--', lw=1)
axes[1].set_xlabel('Prediksi Harga (Rp Juta)')
axes[1].set_ylabel('Residual (Rp Juta)')
axes[1].set_title('Residual Plot')
savefig('29_regression_price_size.png')


# =============================================================================
# INSIGHT 30: EXPECTED PRICE PER m2
# =============================================================================
section('30. EXPECTED PRICE PER m2')
d30 = desc_stats(df_valid['price_per_sqm'].dropna(), 'Harga per m2')
g30 = df_valid.groupby('subdistrict')['price_per_sqm'].agg(['mean', 'median', 'std', 'count'])
print('\nExpected price per m2 per subdistrict:')
print(g30.to_string())

fig, ax = plt.subplots(figsize=(10, 5))
order30 = df_valid.groupby('subdistrict')['price_per_sqm'].median().sort_values(ascending=False).index
sns.boxplot(data=df_valid, x='subdistrict', y='price_per_sqm', order=order30, palette='Set2', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e3:.0f}k'))
ax.set_xlabel('Subdistrict')
ax.set_ylabel('Harga per m2 (Rp)')
ax.set_title(f'Expected Price per m2 per Subdistrict\nMean: Rp {d30["mean"]/1e3:.0f}k, Median: Rp {d30["median"]/1e3:.0f}k')
plt.xticks(rotation=30, ha='right')
savefig('30_expected_price_per_sqm.png')


# =============================================================================
# INSIGHT 31: REGRESI LINEAR HARGA ~ JARAK UNIVERSITAS
# =============================================================================
section('31. REGRESI LINEAR: HARGA ~ JARAK UNIVERSITAS')
valid31 = df_valid[['dist_to_nearest_university_km', 'price']].dropna()
slope31, int31, r31, p31, _ = linregress(valid31['dist_to_nearest_university_km'], valid31['price'])
r2_31 = r31 ** 2

print(f'  Regression Equation: Price = {slope31:,.0f} * Jarak_Univ + {int31:,.0f}')
print(f'  R2 = {r2_31:.4f}, p = {p31:.4e}')
print(f'  Interpretasi: Jarak ke universitas TIDAK kuat memprediksi harga (R2 rendah)')

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(valid31['dist_to_nearest_university_km'], valid31['price']/1e6, alpha=0.4, s=30, c=PALETTE[4])
x31 = np.linspace(valid31['dist_to_nearest_university_km'].min(), valid31['dist_to_nearest_university_km'].max(), 100)
ax.plot(x31, (slope31*x31+int31)/1e6, 'r--', lw=2, label=f'R2={r2_31:.4f}, p={p31:.2e}')
ax.set_xlabel('Jarak ke Universitas (km)')
ax.set_ylabel('Harga (Rp Juta)')
ax.set_title('Regresi: Harga vs Jarak Universitas')
ax.legend()
savefig('31_regression_price_university.png')


# =============================================================================
# INSIGHT 32: MULTIPLE REGRESSION
# =============================================================================
section('32. MULTIPLE REGRESSION: PREDIKSI HARGA DARI BEBERAPA FITUR')
features32 = ['size_area', 'dist_to_nearest_university_km', 'dist_to_nearest_hospital_km',
    'dist_to_nearest_mall_km', 'jarak_bandara_ngurah_rai_km',
    'building_year', 'available_room', 'fac_total_n', 'dp_percentage']

df32 = df_valid[features32 + ['price']].dropna()
print(f'  Records for model: {len(df32)}')

X32 = df32[features32].values
y32 = df32['price'].values

scaler32 = StandardScaler()
X32_scaled = scaler32.fit_transform(X32)

model32 = LinearRegression()
model32.fit(X32_scaled, y32)
y_pred32 = model32.predict(X32_scaled)
r2_32 = r2_score(y32, y_pred32)
adj_r2_32 = 1 - (1 - r2_32) * (len(y32) - 1) / (len(y32) - X32.shape[1] - 1)
rmse32 = np.sqrt(mean_squared_error(y32, y_pred32))
mape32 = np.mean(np.abs((y32 - y_pred32) / y32)) * 100

print(f'\n  Model Performance:')
print(f'    R2              = {r2_32:.4f}')
print(f'    Adjusted R2     = {adj_r2_32:.4f}')
print(f'    RMSE            = Rp {rmse32:,.0f}')
print(f'    MAPE            = {mape32:.1f}%')

importance = pd.Series(model32.coef_, index=features32).sort_values(key=abs, ascending=False)
print(f'\n  Feature Importance (Standardized Coefficients):')
for feat, coef in importance.items():
    direction = '+' if coef > 0 else '-'
    print(f'    {feat:40s}: {direction}{abs(coef):>12,.0f} (std units)')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(y32/1e6, y_pred32/1e6, alpha=0.4, s=30, c=PALETTE[0])
axes[0].plot([y32.min()/1e6, y32.max()/1e6], [y32.min()/1e6, y32.max()/1e6], 'r--', lw=2)
axes[0].set_xlabel('Harga Aktual (Rp Juta)')
axes[0].set_ylabel('Harga Prediksi (Rp Juta)')
axes[0].set_title(f'Actual vs Predicted\nR2={r2_32:.4f}, MAPE={mape32:.1f}%')
importance.plot.barh(ax=axes[1], color=[PALETTE[0] if v > 0 else PALETTE[2] for v in importance.values])
axes[1].set_xlabel('Standardized Coefficient')
axes[1].set_title('Feature Importance')
axes[1].axvline(0, color='black', ls='-', lw=0.5)
savefig('32_multiple_regression.png')


# =============================================================================
# INSIGHT 33: ANOVA PER SUBDISTRICT
# =============================================================================
section('33. ANOVA: HARGA PER SUBDISTRICT')
groups33 = [group['price'].values for name, group in df_valid.groupby('subdistrict') if len(group) >= 2]
f_stat33, p_anova33 = f_oneway(*groups33)

print(f'  Groups (subdistricts with n>=2): {len(groups33)}')
for name, group in df_valid.groupby('subdistrict'):
    if len(group) >= 2:
        print(f'    {name:25s}: n={len(group):3d}, mean=Rp {group["price"].mean():>12,.0f}, std=Rp {group["price"].std():>10,.0f}')
print(f'\n  F-statistic        = {f_stat33:.4f}')
print(f'  p-value            = {p_anova33:.6e}')
sig33 = 'Yes' if p_anova33 < 0.05 else 'No'
print(f'  Significant at 0.05: {sig33}')

fig, ax = plt.subplots(figsize=(10, 5))
order33 = df_valid.groupby('subdistrict')['price'].median().sort_values(ascending=False).index
sns.boxplot(data=df_valid, x='subdistrict', y='price', order=order33, palette='Set2', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
ax.set_xlabel('Subdistrict')
ax.set_ylabel('Harga (Rp)')
ax.set_title(f'ANOVA: Harga per Subdistrict\nF={f_stat33:.2f}, p={p_anova33:.2e}')
plt.xticks(rotation=30, ha='right')
savefig('33_anova_subdistrict.png')


# =============================================================================
# INSIGHT 34: RUMUS PREDIKSI HARGA
# =============================================================================
section('34. RUMUS PREDIKSI HARGA (Multiple Regression)')
model34 = LinearRegression()
X34 = df32[features32].values
model34.fit(X34, y32)
y_pred34 = model34.predict(X34)
r2_34 = r2_score(y32, y_pred34)

print(f'  Rumus Prediksi Harga:')
print(f'  Price = {model34.intercept_:,.0f}')
for feat, coef in sorted(zip(features32, model34.coef_), key=lambda x: abs(x[1]), reverse=True):
    sign = '+' if coef > 0 else '-'
    print(f'    {sign} {abs(coef):>12,.0f} x {feat}')

print(f'\n  R2 model: {r2_34:.4f}')
print(f'\n  Contoh prediksi:')
sample34 = df32.iloc[0]
sample34_features = sample34[features32].values.reshape(1, -1)
pred34 = model34.predict(sample34_features)[0]
print(f'    Input: Size={sample34["size_area"]:.0f}m2, Jarak Univ={sample34["dist_to_nearest_university_km"]:.2f}km')
print(f'    Prediksi: Rp {pred34:,.0f}')
print(f'    Aktual  : Rp {sample34["price"]:,.0f}')

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(y32/1e6, y_pred34/1e6, alpha=0.4, s=30, c=PALETTE[3])
ax.plot([0, y32.max()/1e6], [0, y32.max()/1e6], 'r--', lw=2, label='Perfect prediction')
ax.set_xlabel('Harga Aktual (Rp Juta)')
ax.set_ylabel('Harga Prediksi (Rp Juta)')
ax.set_title(f'Prediksi vs Aktual (Unscaled Model)\nR2={r2_34:.4f}')
ax.legend()
savefig('34_prediction_formula.png')


# =============================================================================
# INSIGHT 35: WHAT-IF ANALYSIS
# =============================================================================
section('35. WHAT-IF ANALYSIS: EFEK PERUBAHAN VARIABEL')
baseline35 = df32[features32].median()
print('  Baseline (median):')
for f in features32:
    print(f'    {f:40s}: {baseline35[f]:.2f}')
base_pred = model34.predict(baseline35.values.reshape(1, -1))[0]
print(f'    {"Predicted Price":40s}: Rp {base_pred:,.0f}')
print()

print('  Efek perubahan 1 unit:')
whatif_results = []
for feat in features32:
    modified = baseline35.copy()
    if 'dist' in feat or 'jarak' in feat:
        modified[feat] -= 1
        label = f'{feat} berkurang 1km'
    elif feat == 'size_area':
        modified[feat] += 1
        label = f'{feat} bertambah 1m2'
    elif feat == 'building_year':
        modified[feat] += 1
        label = f'{feat} +1 tahun'
    elif feat == 'fac_total_n':
        modified[feat] += 1
        label = f'{feat} +1 fasilitas'
    else:
        modified[feat] += 1
        label = f'{feat} +1'

    new_pred = model34.predict(modified.values.reshape(1, -1))[0]
    diff = new_pred - base_pred
    whatif_results.append({'Variabel': label, 'Delta_Harga': diff})
    sign = '+' if diff > 0 else ''
    print(f'    {label:50s}: {sign}Rp {diff:,.0f}')

fig, ax = plt.subplots(figsize=(10, 6))
wdf = pd.DataFrame(whatif_results)
colors = [PALETTE[0] if v > 0 else PALETTE[2] for v in wdf['Delta_Harga']]
ax.barh(wdf['Variabel'][::-1], wdf['Delta_Harga'][::-1]/1e3, color=colors[::-1], alpha=0.7)
ax.set_xlabel('Perubahan Harga (Rp Ribu)')
ax.set_title('What-if Analysis: Efek Perubahan 1 Unit Variabel terhadap Harga')
ax.axvline(0, color='black', ls='-', lw=0.5)
for i, v in enumerate(wdf['Delta_Harga'][::-1]/1e3):
    sign = '+' if v >= 0 else ''
    ax.text(v + (5 if v >= 0 else -5), i, f'{sign}{v:.0f}k', va='center', fontsize=8,
        ha='left' if v >= 0 else 'right')
savefig('35_whatif_analysis.png')


# =============================================================================
# INSIGHT 36: PREDIKSI HARGA PER KATEGORI UKURAN
# =============================================================================
section('36. PREDIKSI HARGA BERDASARKAN KATEGORI UKURAN')
g36 = df_valid.groupby('size_cat', observed=True)['price'].agg(['count', 'mean', 'median', 'std', 'min', 'max'])
print(g36.to_string())

fig, ax = plt.subplots(figsize=(10, 5))
order36 = ['S (<12m2)', 'M (12-16m2)', 'L (16-20m2)', 'XL (20-30m2)', 'XXL (>30m2)']
sns.boxplot(data=df_valid, x='size_cat', y='price', order=order36, palette='coolwarm', ax=ax)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}jt'))
ax.set_xlabel('Kategori Ukuran')
ax.set_ylabel('Harga (Rp)')
ax.set_title('Prediksi Harga per Kategori Ukuran Kamar')
savefig('36_price_by_size_category.png')


# =============================================================================
# INSIGHT 37: KLASIFIKASI HARGA
# =============================================================================
section('37. KLASIFIKASI HARGA: PREDIKSI TIPE BERDASARKAN FITUR')
df37 = df_valid[features32 + ['price']].dropna()
median_price37 = df37['price'].median()
df37['is_expensive'] = (df37['price'] >= median_price37).astype(int)

model37 = LinearRegression()
X37 = df37[features32].values
y37_price = df37['price'].values
model37.fit(X37, y37_price)
predicted_prices37 = model37.predict(X37)
df37['predicted_class'] = (predicted_prices37 >= median_price37).astype(int)
accuracy37 = (df37['predicted_class'] == df37['is_expensive']).mean()

print(f'  Total records      : {len(df37)}')
print(f'  Median price       : Rp {median_price37:,.0f}')
print(f'  Class 0 (<=median) : {(df37["is_expensive"]==0).sum()}')
print(f'  Class 1 (>median)  : {(df37["is_expensive"]==1).sum()}')
print(f'  Accuracy           : {accuracy37:.1%}')

from sklearn.metrics import confusion_matrix
cm37 = confusion_matrix(df37['is_expensive'], df37['predicted_class'])
print(f'\n  Confusion Matrix:')
print(f'    TN={cm37[0,0]:3d}  FP={cm37[0,1]:3d}')
print(f'    FN={cm37[1,0]:3d}  TP={cm37[1,1]:3d}')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.heatmap(cm37, annot=True, fmt='d', cmap='Blues', ax=axes[0],
    xticklabels=['<= Median', '> Median'], yticklabels=['<= Median', '> Median'])
axes[0].set_xlabel('Predicted')
axes[0].set_ylabel('Actual')
axes[0].set_title(f'Confusion Matrix\nAccuracy: {accuracy37:.1%}')

importance37 = pd.Series(model37.coef_, index=features32).sort_values(key=abs, ascending=False)
importance37.plot.barh(ax=axes[1], color=[PALETTE[0] if v > 0 else PALETTE[2] for v in importance37.values])
axes[1].set_xlabel('Coefficient')
axes[1].set_title('Feature Coefficients for Price Classification')
axes[1].axvline(0, color='black', ls='-', lw=0.5)
savefig('37_price_classification.png')


# =============================================================================
# INSIGHT 38: MONTE CARLO SIMULATION
# =============================================================================
section('38. MONTE CARLO SIMULATION HARGA')
mu38 = df_valid['price'].mean()
sigma38 = df_valid['price'].std()
n_sim = 10000
np.random.seed(42)
sim_prices = np.random.normal(mu38, sigma38, n_sim)
sim_prices = sim_prices[sim_prices > 0]

ci_50 = np.percentile(sim_prices, [25, 75])
ci_90 = np.percentile(sim_prices, [5, 95])
ci_95 = np.percentile(sim_prices, [2.5, 97.5])

print(f'  Simulation Parameters:')
print(f'    Distribution: Normal(mu=Rp {mu38:,.0f}, sigma=Rp {sigma38:,.0f})')
print(f'    N simulations: {n_sim:,}')
print(f'\n  Simulation Results:')
print(f'    Mean simulated price    : Rp {sim_prices.mean():,.0f}')
print(f'    50% CI                  : Rp {ci_50[0]:,.0f} - Rp {ci_50[1]:,.0f}')
print(f'    90% CI                  : Rp {ci_90[0]:,.0f} - Rp {ci_90[1]:,.0f}')
print(f'    95% CI                  : Rp {ci_95[0]:,.0f} - Rp {ci_95[1]:,.0f}')
p_low = (sim_prices < 1500000).mean()
p_high = (sim_prices > 5000000).mean()
print(f'    P(price < 1.5jt)        : {p_low:.1%}')
print(f'    P(price > 5jt)          : {p_high:.1%}')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(sim_prices/1e6, bins=50, density=True, color=PALETTE[4], alpha=0.7, edgecolor='white')
axes[0].axvline(ci_95[0]/1e6, color='red', ls='--', lw=2, label=f'95% CI: {ci_95[0]/1e6:.2f}-{ci_95[1]/1e6:.2f}jt')
axes[0].axvline(ci_95[1]/1e6, color='red', ls='--', lw=2)
axes[0].axvline(ci_90[0]/1e6, color='orange', ls='--', lw=1.5, label=f'90% CI: {ci_90[0]/1e6:.2f}-{ci_90[1]/1e6:.2f}jt')
axes[0].axvline(ci_90[1]/1e6, color='orange', ls='--', lw=1.5)
axes[0].set_xlabel('Harga Simulasi (Rp Juta)')
axes[0].set_ylabel('Density')
axes[0].set_title('Monte Carlo Simulation Distribusi Harga')
axes[0].legend(fontsize=8)

sorted_sim = np.sort(sim_prices)
cdf = np.arange(1, len(sorted_sim)+1) / len(sorted_sim)
axes[1].plot(sorted_sim/1e6, cdf, color=PALETTE[5], lw=2)
axes[1].axhline(0.5, color='gray', ls=':', lw=1)
axes[1].axhline(0.05, color='red', ls='--', lw=1, label='5th percentile')
axes[1].axhline(0.95, color='red', ls='--', lw=1, label='95th percentile')
axes[1].set_xlabel('Harga (Rp Juta)')
axes[1].set_ylabel('Cumulative Probability')
axes[1].set_title('CDF Simulasi Harga')
axes[1].legend()
savefig('38_monte_carlo_simulation.png')


# =============================================================================
# INSIGHT 39: RESIDUAL ANALYSIS
# =============================================================================
section('39. RESIDUAL ANALYSIS (Multiple Regression)')
residuals39 = y32 - y_pred32

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0][0].scatter(y_pred32/1e6, residuals39/1e6, alpha=0.4, s=25, c=PALETTE[0])
axes[0][0].axhline(0, color='red', ls='--', lw=1)
axes[0][0].set_xlabel('Prediksi Harga (Rp Juta)')
axes[0][0].set_ylabel('Residual (Rp Juta)')
axes[0][0].set_title('Residual vs Predicted')

axes[0][1].hist(residuals39/1e6, bins=30, color=PALETTE[1], alpha=0.7, edgecolor='white', density=True)
x_res = np.linspace(residuals39.min(), residuals39.max(), 100)
axes[0][1].plot(x_res/1e6, stats.norm.pdf(x_res, residuals39.mean(), residuals39.std())/1e6, 'r-', lw=2)
axes[0][1].set_xlabel('Residual (Rp Juta)')
axes[0][1].set_ylabel('Density')
res_skew = pd.Series(residuals39).skew()
res_kurt = pd.Series(residuals39).kurtosis()
axes[0][1].set_title(f'Distribusi Residual\nSkew={res_skew:.3f}, Kurt={res_kurt:.3f}')

stats.probplot(residuals39, dist='norm', plot=axes[1][0])
axes[1][0].set_title('Q-Q Plot Residual')
axes[1][0].get_lines()[0].set_markersize(3)

axes[1][1].scatter(df32['size_area'], residuals39/1e6, alpha=0.4, s=25, c=PALETTE[3])
axes[1][1].axhline(0, color='red', ls='--', lw=1)
axes[1][1].set_xlabel('Ukuran Kamar (m2)')
axes[1][1].set_ylabel('Residual (Rp Juta)')
axes[1][1].set_title('Residual vs Ukuran Kamar')

plt.suptitle('Residual Analysis Multiple Regression Model', y=1.01, fontsize=14, fontweight='bold')
savefig('39_residual_analysis.png')

print(f'  Residual Statistics:')
print(f'    Mean     : Rp {residuals39.mean():,.0f} (should be ~0)')
print(f'    Std      : Rp {residuals39.std():,.0f}')
print(f'    Min      : Rp {residuals39.min():,.0f}')
print(f'    Max      : Rp {residuals39.max():,.0f}')
print(f'    Skewness : {res_skew:.4f}')
print(f'    Kurtosis : {res_kurt:.4f}')

stat_res, p_res = shapiro(residuals39[:min(500, len(residuals39))])
print(f'    Shapiro-Wilk: stat={stat_res:.4f}, p={p_res:.4e}')


# =============================================================================
# INSIGHT 40: PROYEKSI HARGA MASA DEPAN (2, 5, 10, 15 TAHUN)
# =============================================================================
section('40. PROYEKSI HARGA MASA DEPAN (2, 5, 10, 15 TAHUN)')

# --- 40a. Building Year Trend Regression ---
valid40 = df_valid[['building_year', 'price']].dropna()
slope40, int40, r40, p40, se40 = linregress(valid40['building_year'], valid40['price'])
r2_40 = r40 ** 2

print(f'  === Metode A: Building Year Trend ===')
print(f'  Regression: Price = {slope40:,.0f} x Year + ({int40:,.0f})')
print(f'  R = {r40:.4f}, R2 = {r2_40:.4f}, p = {p40:.2e}')
print(f'  Interpretasi: Setiap tahun baru, harga naik Rp {slope40:,.0f} (trend building_year)')

# --- 40b. Parameter proyeksi ---
current_year = 2026
current_price_mean = df_valid['price'].mean()
current_price_median = df_valid['price'].median()
future_years = [2028, 2031, 2036, 2041]
inflation_rates = [0.03, 0.04, 0.05]  # Pesimis, Sentral, Optimis
inflation_labels = ['Pesimis (3%)', 'Sentral (4%)', 'Optimis (5%)']
inflation_colors = [PALETTE[2], PALETTE[0], PALETTE[4]]

print(f'\n  === Parameter Proyeksi ===')
print(f'  Harga rata-rata saat ini : Rp {current_price_mean:,.0f}')
print(f'  Harga median saat ini    : Rp {current_price_median:,.0f}')
print(f'  Tahun referensi          : {current_year}')
print(f'  Tahun target             : {future_years}')
print(f'  Skenario inflasi         : 3%, 4%, 5% per tahun')

# --- 40c. Hitung proyeksi untuk setiap tahun ---
print(f'\n  === Tabel Proyeksi Harga Masa Depan ===')
print(f'  {"Tahun":<8} {"+Tahun":<8} {"Pesimis (3%)":<18} {"Sentral (4%)":<18} {"Optimis (5%)":<18} {"CI 95%":<25}')
print(f'  {"-"*95}')

# Store projections for plotting
proj_data = {}
proj_data[current_year] = {
    'pesimis': current_price_mean,
    'sentral': current_price_mean,
    'optimis': current_price_mean,
    'ci_lower': current_price_mean - 1.96 * se40,
    'ci_upper': current_price_mean + 1.96 * se40,
}

for target_year in future_years:
    years_ahead = target_year - current_year

    # Building year trend prediction
    trend_pred = slope40 * target_year + int40

    # Inflation projections from current mean
    pesimis = current_price_mean * ((1 + 0.03) ** years_ahead)
    sentral = current_price_mean * ((1 + 0.04) ** years_ahead)
    optimis = current_price_mean * ((1 + 0.05) ** years_ahead)

    # Combined: weighted average (60% inflation + 40% building_year trend)
    combined_pesimis = 0.6 * pesimis + 0.4 * trend_pred
    combined_sentral = 0.6 * sentral + 0.4 * trend_pred
    combined_optimis = 0.6 * optimis + 0.4 * trend_pred

    # CI widens with time (uncertainty increases)
    ci_width = 1.96 * se40 * np.sqrt(1 + years_ahead * 0.15)
    ci_lower = combined_sentral - ci_width
    ci_upper = combined_sentral + ci_width

    proj_data[target_year] = {
        'pesimis': combined_pesimis,
        'sentral': combined_sentral,
        'optimis': combined_optimis,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'trend_only': trend_pred,
        'inflasi_only': sentral,
    }

    # Percentage change from current
    pct_change = (combined_sentral / current_price_mean - 1) * 100

    print(f'  {target_year:<8} {f"+{years_ahead}":<8} '
          f'Rp {combined_pesimis/1e6:>6.2f}jt      '
          f'Rp {combined_sentral/1e6:>6.2f}jt      '
          f'Rp {combined_optimis/1e6:>6.2f}jt      '
          f'Rp {ci_lower/1e6:.2f}jt - {ci_upper/1e6:.2f}jt')

# --- 40d. Statistik Deskriptif Proyeksi ---
print(f'\n  === Statistik Deskriptif Proyeksi ===')
all_sentral = [proj_data[y]['sentral'] for y in future_years]
all_pesimis = [proj_data[y]['pesimis'] for y in future_years]
all_optimis = [proj_data[y]['optimis'] for y in future_years]

d40_sentral = desc_stats(pd.Series(all_sentral), 'Proyeksi Sentral (4% inflasi)')
d40_pesimis = desc_stats(pd.Series(all_pesimis), 'Proyeksi Pesimis (3% inflasi)')
d40_optimis = desc_stats(pd.Series(all_optimis), 'Proyeksi Optimis (5% inflasi)')

# --- 40e. Visualisasi ---
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Plot 1: Line chart proyeksi
ax1 = axes[0]
years_plot = [current_year] + future_years

# Plot CI band first (behind lines)
ci_lowers = [proj_data[y]['ci_lower'] for y in years_plot]
ci_uppers = [proj_data[y]['ci_upper'] for y in years_plot]
ax1.fill_between(years_plot, [x/1e6 for x in ci_lowers], [x/1e6 for x in ci_uppers],
    alpha=0.2, color='gray', label='95% CI')

# Plot 3 scenarios
for i, (label, color) in enumerate(zip(inflation_labels, inflation_colors)):
    y_vals = [proj_data[y]['pesimis' if i == 0 else 'sentral' if i == 1 else 'optimis'] for y in years_plot]
    ax1.plot(years_plot, [y/1e6 for y in y_vals], marker='o', lw=2.5, color=color, label=label)
    for y, v in zip(years_plot, y_vals):
        ax1.annotate(f'{v/1e6:.2f}jt', (y, v/1e6), textcoords="offset points",
            xytext=(0, 10), ha='center', fontsize=7, color=color)

# Mark current price
ax1.scatter([current_year], [current_price_mean/1e6], s=100, color='black', zorder=5)
ax1.annotate(f'Sekarang\nRp {current_price_mean/1e6:.2f}jt', (current_year, current_price_mean/1e6),
    textcoords="offset points", xytext=(0, 20), ha='center', fontsize=9, fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='black'))

ax1.set_xlabel('Tahun', fontsize=11)
ax1.set_ylabel('Harga Rata-rata (Rp Juta)', fontsize=11)
ax1.set_title('Proyeksi Harga Kost Jimbaran\n(Gabungan Building Year Trend + Inflasi)', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left', fontsize=9)
ax1.set_xticks(years_plot)
ax1.grid(True, alpha=0.3)

# Plot 2: Bar chart perbandingan metode
ax2 = axes[1]
x_pos = np.arange(len(future_years))
bar_width = 0.25

trend_vals = [proj_data[y]['trend_only']/1e6 for y in future_years]
inflasi_vals = [proj_data[y]['inflasi_only']/1e6 for y in future_years]
combined_vals = [proj_data[y]['sentral']/1e6 for y in future_years]

bars1 = ax2.bar(x_pos - bar_width, trend_vals, bar_width, label='Building Year Trend', color=PALETTE[1], alpha=0.8)
bars2 = ax2.bar(x_pos, inflasi_vals, bar_width, label='Inflasi (4%)', color=PALETTE[0], alpha=0.8)
bars3 = ax2.bar(x_pos + bar_width, combined_vals, bar_width, label='Gabungan (60% Inflasi + 40% Trend)', color=PALETTE[3], alpha=0.8)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{height:.2f}jt', xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=7)

ax2.set_xlabel('Tahun Target', fontsize=11)
ax2.set_ylabel('Harga Prediksi (Rp Juta)', fontsize=11)
ax2.set_title('Perbandingan 3 Metode Proyeksi', fontsize=12, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels([f'{y}\n(+{y-current_year}th)' for y in future_years])
ax2.legend(fontsize=8)
ax2.grid(axis='y', alpha=0.3)

plt.suptitle('INSIGHT 40: PROYEKSI HARGA KOST JIMBARAN MASA DEPAN', y=1.02, fontsize=14, fontweight='bold')
savefig('40_future_price_projection.png')

# --- 40f. Ringkasan Persentase Kenaikan ---
print(f'\n  === Ringkasan Persentase Kenaikan dari Harga Saat Ini ===')
print(f'  {"Tahun":<8} {"+Tahun":<8} {"Pesimis":<15} {"Sentral":<15} {"Optimis":<15}')
print(f'  {"-"*65}')
for y in future_years:
    yrs = y - current_year
    pct_p = (proj_data[y]['pesimis'] / current_price_mean - 1) * 100
    pct_s = (proj_data[y]['sentral'] / current_price_mean - 1) * 100
    pct_o = (proj_data[y]['optimis'] / current_price_mean - 1) * 100
    print(f'  {y:<8} {f"+{yrs}":<8} {f"+{pct_p:.1f}%":<15} {f"+{pct_s:.1f}%":<15} {f"+{pct_o:.1f}%":<15}')

print(f'\n  === Interpretasi ===')
print(f'  Dalam 15 tahun ke depan (2041), harga kost Jimbaran diproyeksikan:')
print(f'    - Pesimis (3% inflasi) : Rp {proj_data[2041]["pesimis"]/1e6:.2f}jt (+{(proj_data[2041]["pesimis"]/current_price_mean-1)*100:.0f}%)')
print(f'    - Sentral (4% inflasi) : Rp {proj_data[2041]["sentral"]/1e6:.2f}jt (+{(proj_data[2041]["sentral"]/current_price_mean-1)*100:.0f}%)')
print(f'    - Optimis (5% inflasi) : Rp {proj_data[2041]["optimis"]/1e6:.2f}jt (+{(proj_data[2041]["optimis"]/current_price_mean-1)*100:.0f}%)')
print(f'  Catatan: Proyeksi menggunakan gabungan building_year trend (40%)')
print(f'  dan inflasi historis Indonesia (60%). CI melebar seiring waktu.')


# =============================================================================
# RINGKASAN AKHIR
# =============================================================================
section('RINGKASAN AKHIR - 40 INSIGHT SELESAI')
print(f'''
  Dataset: {len(df)} kost dari Jimbaran, Badung
  Total Insight: 40

  Bagian A - Insight Dasar (1-24):
    1.  Distribusi harga bulanan
    2.  Harga per subdistrict
    3.  Harga per gender (Campur vs Putri)
    4-10. Harga vs jarak POI (7 POI terdekat)
    11. Harga vs ukuran kamar
    12. Harga vs tahun bangunan
    13. Top fasilitas kamar
    14. Top fasilitas berbagi
    15. Top fasilitas kamar mandi
    16. Jumlah fasilitas vs harga
    17. Distribusi DP percentage
    18. Analisis rating
    19. View count & love count vs harga
    20. Harga per m2
    21. Distribusi ukuran kamar
    22. Heatmap korelasi
    23. Kamar tersedia vs harga
    24. Top 10 termahal & termurah

  Bagian B - Inferensial / Forecasting (25-39):
    25. Confidence Interval 95% mean harga
    26. Uji normalitas (Shapiro-Wilk)
    27. Distribusi log-normal
    28. T-test Campur vs Putri
    29. Regresi linear: Harga ~ Ukuran
    30. Expected price per m2
    31. Regresi linear: Harga ~ Jarak universitas
    32. Multiple regression (9 fitur)
    33. ANOVA per subdistrict
    34. Rumus prediksi harga
    35. What-if analysis
    36. Prediksi harga per kategori ukuran
    37. Klasifikasi harga (Murah/Eksklusif)
    38. Monte Carlo simulation
    39. Residual analysis

  Bagian C - Proyeksi Masa Depan (40):
    40. Proyeksi harga 2, 5, 10, 15 tahun ke depan
        (Gabungan Building Year Trend + Inflasi 3-5%)

  Output tersimpan di: notebooks/insight/output/
''')

print('  DONE! Semua 40 insight + visualisasi telah dihasilkan.')
