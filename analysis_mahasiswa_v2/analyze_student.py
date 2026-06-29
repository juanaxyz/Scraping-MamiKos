"""
ANALISIS MAHASISWA V2 - 35 Insight Praktis + Prediksi + Ekspektasi
====================================================================
Perspektif mahasiswa rantau mencari kos di sekitar UNUD Jimbaran.
Source: data/mamikos_all.csv → preprocessed → data/processed/mamikos_clean.csv
Output : analysis_mahasiswa_v2/output/*.png
====================================================================
"""

import os, warnings, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
from scipy import stats
from scipy.stats import linregress, pearsonr

warnings.filterwarnings('ignore')
sns.set_theme(style='whitegrid', font_scale=1.1)
C = ['#2E86AB','#A23B72','#F18F01','#C73E1D','#3B1F2B','#44BBA4','#E94F37','#393E41','#3A6B35','#E2C044']

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

def sf(name):
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, name), dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  [OK] {name}')

def fr(v):
    if pd.isna(v) or v is None: return 'N/A'
    if v >= 1e6: return f'Rp {v/1e6:.2f}jt'
    return f'Rp {v:,.0f}'

def ab(ax, text, xy=(0.55,0.97), fs=9, alpha=0.92):
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=alpha, edgecolor='#555')
    ax.text(xy[0], xy[1], text, transform=ax.transAxes, fontsize=fs,
            verticalalignment='top', fontfamily='monospace', bbox=props)

print('\n' + '='*70)
print('  LOADING DATA')
print('='*70)
CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'mamikos_clean.csv')
dv = pd.read_csv(CSV)
print(f'  Loaded {len(dv)} rows x {len(dv.columns)} cols')
print(f'  Valid: {len(dv)} kos')

def _sort_tier(x):
    if x.startswith('<'): return 0
    if x.startswith('>'): return 999
    return float(x.split('Rp')[1].split('-')[0].replace('jt','').replace(',', '.'))

tier_lbls = sorted(dv['tier'].dropna().unique(), key=_sort_tier)

bc = [c for c in dv.columns if c.startswith('fac_bath_')]
rc = [c for c in dv.columns if c.startswith('fac_room_')]
sc = [c for c in dv.columns if c.startswith('fac_share_')]

# ====================================================================
# TEMA 1: BUDGET BASICS (1-5)
# ====================================================================
print('\n' + '='*70)
print('  TEMA 1: DASAR BUDGET')
print('='*70)

p = dv['price']

# --- 1. GAMBARAN HARGA ---
print('\n  1. BERAPA HARGA KOS SEKITAR UNUD?')
d1 = {'count':len(p),'mean':p.mean(),'median':p.median(),'std':p.std(),'min':p.min(),'max':p.max(),
      'Q1':p.quantile(0.25),'Q3':p.quantile(0.75),'skew':p.skew()}
fig,ax = plt.subplots(figsize=(12,7))
ax.hist(p/1e6, bins=25, color=C[0], edgecolor='white', alpha=0.85)
for v,ls,cl,lb in [(d1['mean'],'--','red','Mean'),(d1['median'],'--','blue','Median'),
                    (d1['Q1'],':','green','Q1'),(d1['Q3'],':','green','Q3')]:
    ax.axvline(v/1e6, color=cl, ls=ls, lw=2, alpha=0.8)
ax.set_xlabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Berapa Harga Kos di Sekitar UNUD?', fontsize=15, fontweight='bold')
ab(ax, f'Total: {d1["count"]} kos\nRata-rata: {fr(d1["mean"])}\nMedian: {fr(d1["median"])}\nTermurah: {fr(d1["min"])}\nTermahal: {fr(d1["max"])}\nQ1: {fr(d1["Q1"])}\nQ3: {fr(d1["Q3"])}')
sf('01_gambaran_harga.png')

# --- 2. BUDGET KUMULATIF (percentile-based) ---
print('  2. BUDGET RP X DAPET BERAPA PILIHAN?')
pcts = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.75, 0.9]
budgets = [p.quantile(q) for q in pcts]
bcnt = [(p<=b).sum() for b in budgets]
bpct = [c/len(p)*100 for c in bcnt]
fig,ax = plt.subplots(figsize=(12,7))
colors = [C[5] if v<50 else C[2] if v<80 else C[4] for v in bpct]
bars = ax.bar(range(len(budgets)), bcnt, color=colors, edgecolor='white', width=0.65)
for i,(c,pc) in enumerate(zip(bcnt,bpct)):
    ax.text(i, c+4, f'{c} kos\n({pc:.1f}%)', ha='center', fontsize=10, fontweight='bold')
ax.set_xticks(range(len(budgets)))
ax.set_xticklabels([fr(b) for b in budgets], rotation=25, ha='right')
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Budget Berapa yang Paling Realistis?', fontsize=14, fontweight='bold')
ax.set_ylim(0, max(bcnt)+30)
ab(ax, f'≤{fr(budgets[1])}: {bcnt[1]} kos ({bpct[1]:.1f}%)\n≤{fr(budgets[2])}: {bcnt[2]} kos ({bpct[2]:.1f}%)\n≤{fr(budgets[3])}: {bcnt[3]} kos ({bpct[3]:.1f}%) ⭐\n≤{fr(budgets[4])}: {bcnt[4]} kos ({bpct[4]:.1f}%)\n≤{fr(budgets[6])}: {bcnt[6]} kos ({bpct[6]:.1f}%)')
sf('02_budget_kumulatif.png')

# --- 3. ESTIMASI BIAYA BULAN PERTAMA ---
print('  3. ESTIMASI TOTAL BIAYA BULAN PERTAMA')
fm = dv['first_month']
print(f'  Rata-rata: {fr(fm.mean())} | Median: {fr(fm.median())}')

fig,ax = plt.subplots(figsize=(12,7))
ax.hist(fm/1e6, bins=25, color=C[1], edgecolor='white', alpha=0.85)
ax.axvline(fm.mean()/1e6, color='red', ls='--', lw=2.5, label=f'Rata-rata: {fr(fm.mean())}')
ax.axvline(fm.median()/1e6, color='blue', ls='--', lw=2.5, label=f'Median: {fr(fm.median())}')
ax.set_xlabel('Total Bulan Pertama (Juta Rp)', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Estimasi Biaya Bulan Pertama (Sewa + DP)', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ab(ax, f'Rata-rata: {fr(fm.mean())}\nMedian: {fr(fm.median())}\nTermurah: {fr(fm.min())}\nTermahal: {fr(fm.max())}\n\nContoh kos Rp 2,5jt:\nDP 30% → Rp 750rb\nTotal: Rp 3,25jt')
sf('03_estimasi_bulan_pertama.png')

# --- 4. DISTRIBUSI DP ---
print('  4. BERAPA DP YANG HARUS DISIAPKAN?')
dp = dv['dp_percentage'].dropna()
fig,ax = plt.subplots(figsize=(12,7))
ax.hist(dp, bins=10, color=C[0], edgecolor='white', alpha=0.85)
ax.axvline(dp.mean(), color='red', ls='--', lw=2.5, label=f'Rata-rata: {dp.mean():.1f}%')
ax.axvline(dp.median(), color='blue', ls='--', lw=2.5, label=f'Median: {dp.median():.1f}%')
ax.set_xlabel('DP (%)', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Berapa DP yang Harus Disiapkan?', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ab(ax, f'Kos dengan info DP: {len(dp)}/{len(dv)}\nRata-rata DP: {dp.mean():.1f}%\nMedian DP: {dp.median():.1f}%\nDP Minimal: {dp.min():.0f}%\nDP Maksimal: {dp.max():.0f}%\n\nEstimasi awal:\nKos Rp 2,5jt → Rp 750rb\nKos Rp 3,0jt → Rp 900rb')
sf('04_distribusi_dp.png')

# --- 5. TERMURAH VS TERMAHAL ---
print('  5. KOS TERMURAH VS TERMAHAL')
cheap5 = dv.nsmallest(5,'price')[['nama_kost','price','sub','size_area','jarak_unud_jimbaran_km']]
expen5 = dv.nlargest(5,'price')[['nama_kost','price','sub','size_area','jarak_unud_jimbaran_km']]
fig,axes = plt.subplots(1,2,figsize=(16,7))
ax1 = axes[0]
nms = [n[:30]+'..' if len(str(n))>30 else n for n in cheap5['nama_kost'].values]
ax1.barh(range(5), cheap5['price'].values/1e6, color=C[5], edgecolor='black', height=0.6)
for i,(_,r) in enumerate(cheap5.iterrows()):
    ax1.text(r['price']/1e6+0.03, i, fr(r['price']), va='center', fontsize=9, fontweight='bold')
ax1.set_yticks(range(5)); ax1.set_yticklabels(nms, fontsize=8)
ax1.set_xlabel('Harga (Juta Rp)'); ax1.set_title('5 KOS TERMURAH', fontsize=13, fontweight='bold', color=C[5])
ax1.invert_yaxis()
ax2 = axes[0]
nms2 = [n[:30]+'..' if len(str(n))>30 else n for n in expen5['nama_kost'].values]
ax2 = axes[1]
ax2.barh(range(5), expen5['price'].values/1e6, color=C[3], edgecolor='black', height=0.6)
for i,(_,r) in enumerate(expen5.iterrows()):
    ax2.text(r['price']/1e6+0.3, i, fr(r['price']), va='center', fontsize=9, fontweight='bold')
ax2.set_yticks(range(5)); ax2.set_yticklabels(nms2, fontsize=8)
ax2.set_xlabel('Harga (Juta Rp)'); ax2.set_title('5 KOS TERMAHAL', fontsize=13, fontweight='bold', color=C[3])
ax2.invert_yaxis()
fig.suptitle('Termurah vs Termahal', fontsize=14, fontweight='bold', y=1.02)
sf('05_termurah_termahal.png')

# ====================================================================
# TEMA 2: JARAK & LOKASI (6-10)
# ====================================================================
print('\n' + '='*70)
print('  TEMA 2: JARAK & LOKASI')
print('='*70)

# --- 6. HARGA PER ZONA JARAK ---
print('  6. HARGA PER ZONA JARAK DARI UNUD')
z_stats = dv.groupby('zone', observed=True)['price'].agg(['count','mean','median','min','max'])
print(z_stats.to_string())
fig,ax = plt.subplots(figsize=(12,7))
z_data = [dv[dv['zone']==z]['price'].values/1e6 for z in ['<1km','1-2km','2-3km','3-5km','>5km']]
bp = ax.boxplot(z_data, labels=['<1km\n(n=34)','1-2km\n(n=102)','2-3km\n(n=54)','3-5km\n(n=31)','>5km\n(n=20)'],
                patch_artist=True, widths=0.5, medianprops=dict(color='red',lw=2.5))
for patch,color in zip(bp['boxes'],[C[0],C[1],C[5],C[2],C[4]]):
    patch.set_facecolor(color)
means_z = [dv[dv['zone']==z]['price'].mean()/1e6 for z in ['<1km','1-2km','2-3km','3-5km','>5km']]
ax.scatter(range(1,6), means_z, color='blue', marker='D', s=80, zorder=5, label='Rata-rata')
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Harga per Zona Jarak dari Kampus UNUD', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ab(ax, f'<1km: Rp{z_stats.loc["<1km","mean"]/1e6:.2f}jt (n={z_stats.loc["<1km","count"]:.0f})\n1-2km: Rp{z_stats.loc["1-2km","mean"]/1e6:.2f}jt (n={z_stats.loc["1-2km","count"]:.0f})\n2-3km: Rp{z_stats.loc["2-3km","mean"]/1e6:.2f}jt (n={z_stats.loc["2-3km","count"]:.0f})\n3-5km: Rp{z_stats.loc["3-5km","mean"]/1e6:.2f}jt (n={z_stats.loc["3-5km","count"]:.0f})\n>5km: Rp{z_stats.loc[">5km","mean"]/1e6:.2f}jt (n={z_stats.loc[">5km","count"]:.0f})', xy=(0.55,0.88), fs=9)
sf('06_harga_per_zona.png')

# --- 7. HEMAT DENGAN JALAN JAUH ---
print('  7. ESTIMASI HEMAT DENGAN JALAN JAUH')
near = dv[dv['zone']=='<1km']['price']
far = dv[dv['zone']=='>5km']['price']
diff = near.mean() - far.mean()
fig,ax = plt.subplots(figsize=(10,7))
x = ['<1km dari Kampus\n(34 kos)', '>5km dari Kampus\n(20 kos)']
y = [near.mean()/1e6, far.mean()/1e6]
err = [near.std()/1e6, far.std()/1e6]
bars = ax.bar(x, y, yerr=err, color=[C[0],C[4]], capsize=10, width=0.4, edgecolor='black')
for bar,val in zip(bars,y):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.15, f'Rp {val:.2f}jt', ha='center', fontsize=13, fontweight='bold')
ax.set_ylabel('Rata-rata Harga (Juta Rp)', fontsize=13)
ax.set_title('Bisa Hemat Berapa dengan Tinggal Lebih Jauh?', fontsize=14, fontweight='bold')
ab(ax, f'Selisih rata-rata: {fr(diff)}\n\nRelatif dekat:\nRata-rata Rp {near.mean()/1e6:.2f}jt\n\nRelatif jauh:\nRata-rata Rp {far.mean()/1e6:.2f}jt\n\n💡 Hemat Rp {diff/1e6:.2f}jt/bulan\n= Rp {(diff*12)/1e6:.2f}jt/tahun!', xy=(0.55,0.92), fs=10)
sf('07_hemat_jalan_jauh.png')

# --- 8. EKSPEKTASI JARAK BERDASARKAN BUDGET ---
print('  8. EKSPEKTASI JARAK BERDASARKAN BUDGET')
tier_dist = dv.groupby('tier', observed=True)['jarak_unud_jimbaran_km'].agg(['mean','median','std','count'])
print(tier_dist.to_string())
fig,ax = plt.subplots(figsize=(12,7))
t_data = [dv[dv['tier']==t]['jarak_unud_jimbaran_km'].values for t in tier_lbls]
bp = ax.boxplot(t_data, labels=tier_lbls, patch_artist=True, widths=0.5, medianprops=dict(color='red',lw=2.5))
cols_t = [C[5],C[0],C[1],C[2],C[3]]
for patch,c in zip(bp['boxes'],cols_t):
    patch.set_facecolor(c)
for i,t in enumerate(tier_lbls):
    m = dv[dv['tier']==t]['jarak_unud_jimbaran_km'].mean()
    ax.text(i+1, m+0.15, f'{m:.2f}km', ha='center', fontsize=9, fontweight='bold', color='blue')
ax.set_xlabel('Tier Harga', fontsize=13)
ax.set_ylabel('Jarak dari UNUD (km)', fontsize=13)
ax.set_title('Ekspektasi Jarak dari Kampus Berdasarkan Budget', fontsize=14, fontweight='bold')
ab(ax, chr(10).join([f'{t}: rata-rata jarak {tier_dist.loc[t,"mean"]:.2f}km (n={tier_dist.loc[t,"count"]:.0f})' for t in tier_lbls]), xy=(0.55,0.92), fs=9)
sf('08_ekspektasi_jarak.png')

# --- 9. REKOMENDASI KOS DEKAT KAMPUS ---
print('  9. REKOMENDASI KOS DEKAT KAMPUS MURAH')
near_cheap = dv[(dv['jarak_unud_jimbaran_km']<=1)].nsmallest(8,'price')
print(near_cheap[['nama_kost','price','size_area','jarak_unud_jimbaran_km','sub']].to_string())
fig,ax = plt.subplots(figsize=(12,7))
nms9 = [n[:30]+'..' if len(str(n))>30 else n for n in near_cheap['nama_kost'].values]
bars = ax.barh(range(len(near_cheap)), near_cheap['price'].values/1e6, color=C[5], edgecolor='black', height=0.6)
for i,(_,r) in enumerate(near_cheap.iterrows()):
    ax.text(r['price']/1e6+0.03, i, f'{fr(r["price"])} | {r["size_area"]:.0f}m² | {r["jarak_unud_jimbaran_km"]:.2f}km',
            va='center', fontsize=9, fontweight='bold')
ax.set_yticks(range(len(near_cheap))); ax.set_yticklabels(nms9, fontsize=8)
ax.set_xlabel('Harga (Juta Rp)', fontsize=13)
ax.set_title(f'{len(near_cheap)} Kos Dekat Kampus (≤1km) dengan Harga Terjangkau', fontsize=14, fontweight='bold')
ax.invert_yaxis()
ab(ax, f'Ada {len(dv[dv["jarak_unud_jimbaran_km"]<=1])} kos dalam 1km\n{len(near_cheap)} termurah:\nMulai Rp {near_cheap["price"].min():,.0f} - Rp {near_cheap["price"].max():,.0f}', xy=(0.02,0.97), fs=10)
sf('09_rekomendasi_dekat_kampus.png')

# --- 10. HARGA PER KECAMATAN ---
print('  10. HARGA PER KECAMATAN')
g10 = dv.groupby('sub')['price'].agg(['count','mean','median','std','min','max']).round(0)
print(g10.to_string())
fig,ax = plt.subplots(figsize=(12,7))
order = sorted(dv['sub'].unique())
data10 = [dv[dv['sub']==s]['price'].values/1e6 for s in order]
bp = ax.boxplot(data10, labels=[f'{s}\n(n={dv[dv["sub"]==s]["price"].count()})' for s in order],
                patch_artist=True, widths=0.5, medianprops=dict(color='red',lw=2.5))
for patch,c in zip(bp['boxes'],[C[0],C[2],C[1],C[4],C[5]]):
    patch.set_facecolor(c)
means10 = [dv[dv['sub']==s]['price'].mean()/1e6 for s in order]
ax.scatter(range(1,len(order)+1), means10, color='blue', marker='D', s=80, zorder=5)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Perbandingan Harga per Kecamatan', fontsize=14, fontweight='bold')
sf('10_harga_per_kecamatan.png')

# ====================================================================
# TEMA 3: EKSPEKTASI FASILITAS (11-17)
# ====================================================================
print('\n' + '='*70)
print('  TEMA 3: EKSPEKTASI FASILITAS')
print('='*70)

# --- 11. FASILITAS PALING UMUM ---
print('  11. FASILITAS PALING UMUM')
room_t = dv[rc].sum().sort_values(ascending=False).head(10)
share_t = dv[sc].sum().sort_values(ascending=False).head(10)
bath_t = dv[bc].sum().sort_values(ascending=False).head(10)
fig,axes = plt.subplots(1,3,figsize=(18,7))
for ax_i, (data, color, title) in zip(axes,
    [(room_t,C[0],'Fasilitas Kamar'),(share_t,C[5],'Fasilitas Umum'),(bath_t,C[1],'Fasilitas Kamar Mandi')]):
    pct = data/len(dv)*100
    labels = [c.replace('fac_room_','').replace('fac_share_','').replace('fac_bath_','').replace('_',' ').title() for c in data.index]
    bars = ax_i.barh(range(len(data)), pct.values, color=color, edgecolor='black', height=0.6)
    for i,(v,pc) in enumerate(zip(data.values,pct.values)):
        ax_i.text(pc+0.5, i, f'{int(v)} ({pc:.1f}%)', va='center', fontsize=8)
    ax_i.set_yticks(range(len(data))); ax_i.set_yticklabels(labels, fontsize=9)
    ax_i.set_xlim(0, 105); ax_i.set_xlabel('% Kos')
    ax_i.set_title(title, fontsize=12, fontweight='bold')
    ax_i.invert_yaxis()
fig.suptitle('Fasilitas Paling Umum di Kos Sekitar UNUD', fontsize=14, fontweight='bold', y=1.02)
sf('11_fasilitas_paling_umum.png')

# --- 12. TABEL EKSPEKTASI FASILITAS PER TIER ---
print('  12. EKSPEKTASI FASILITAS PER TIER HARGA')
tier_fac = {}
for t in tier_lbls:
    d = dv[dv['tier']==t]
    n = len(d)
    tier_fac[t] = {'count':n}
    for fac in ['fac_room_AC','fac_share_WiFi','fac_bath_K. Mandi Dalam','fac_room_Kasur','fac_bath_Shower','fac_share_CCTV','fac_share_Dapur','fac_bath_Air panas']:
        if fac in dv.columns:
            tier_fac[t][fac] = f'{d[fac].sum()} ({d[fac].sum()/n*100:.0f}%)'
tf_df = pd.DataFrame(tier_fac).T
print(tf_df.to_string())

fig,ax = plt.subplots(figsize=(14,9))
ax.axis('off')
table_data = []
headers = ['Tier Harga', 'n', 'AC', 'WiFi', 'KM Dalam', 'Air Panas', 'CCTV', 'Dapur']
for t in tier_lbls:
    d = dv[dv['tier']==t]
    n = len(d)
    row = [t, str(n)]
    for fac in ['fac_room_AC','fac_share_WiFi','fac_bath_K. Mandi Dalam','fac_bath_Air panas','fac_share_CCTV','fac_share_Dapur']:
        if fac in dv.columns:
            row.append(f'{d[fac].sum()/n*100:.0f}%')
    table_data.append(row)
table = ax.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
table.auto_set_font_size(False); table.set_fontsize(11)
table.scale(1.2, 1.8)
for j in range(len(headers)):
    table[0,j].set_facecolor(C[0]); table[0,j].set_text_props(color='white', fontweight='bold')
for i in range(len(tier_lbls)):
    for j in range(len(headers)):
        if table_data[i][j].endswith('%'):
            val = int(table_data[i][j].replace('%',''))
            if val >= 90: table[i+1,j].set_facecolor('#b7e4c7')
            elif val >= 50: table[i+1,j].set_facecolor('#ffe5b4')
            else: table[i+1,j].set_facecolor('#ffcccc')
ax.set_title('Ekspektasi Fasilitas: Apa yang Dijamin di Tiap Tier Harga?', fontsize=14, fontweight='bold', pad=20)
sf('12_ekspektasi_fasilitas_tier.png')

# --- 13. LUAS KAMAR EKSPEKTASI ---
print('  13. EKSPEKTASI LUAS KAMAR PER TIER')
tier_size = dv.groupby('tier', observed=True)['size_area'].agg(['mean','median','count'])
print(tier_size.to_string())
fig,ax = plt.subplots(figsize=(12,7))
t_size = [dv[dv['tier']==t]['size_area'].values for t in tier_lbls]
bp = ax.boxplot(t_size, labels=tier_lbls, patch_artist=True, widths=0.5, medianprops=dict(color='red',lw=2.5))
for patch,c in zip(bp['boxes'],[C[5],C[0],C[1],C[2],C[3]]):
    patch.set_facecolor(c)
for i,t in enumerate(tier_lbls):
    m = dv[dv['tier']==t]['size_area'].mean()
    ax.text(i+1, m+1, f'{m:.1f}m²', ha='center', fontsize=9, fontweight='bold', color='blue')
ylabel = 'Luas Kamar (m²)'
ax.set_ylabel(ylabel, fontsize=13)
ax.set_xlabel('Tier Harga', fontsize=13)
ax.set_title('Berapa Luas Kamar yang Bisa Kamu Ekspektasikan?', fontsize=14, fontweight='bold')
ab(ax, chr(10).join([f'{t}: rata-rata {tier_size.loc[t,"mean"]:.1f}m²' for t in tier_lbls]) + '\n\n💡 Naik 1 tier = ~+5m²', xy=(0.55,0.92), fs=10)
sf('13_ekspektasi_luas_kamar.png')

# --- 14. AC WORTH IT? ---
print('  14. APAKAH AC SEBANDING DENGAN HARGA?')
has_ac = dv[dv['fac_room_AC']>0]['price'] if 'fac_room_AC' in dv.columns else pd.Series(dtype=float)
no_ac = dv[dv['fac_room_AC']==0]['price'] if 'fac_room_AC' in dv.columns else pd.Series(dtype=float)
ac_diff = has_ac.mean() - no_ac.mean()
fig,ax = plt.subplots(figsize=(10,7))
ax.bar(['Tanpa AC', 'Dengan AC'], [no_ac.mean()/1e6, has_ac.mean()/1e6],
       yerr=[no_ac.std()/1e6, has_ac.std()/1e6], color=[C[3],C[0]], capsize=10, width=0.4, edgecolor='black')
for i,val in enumerate([no_ac.mean()/1e6, has_ac.mean()/1e6]):
    ax.text(i, val+0.15, f'{fr([no_ac.mean(),has_ac.mean()][i])}', ha='center', fontsize=12, fontweight='bold')
ax.set_ylabel('Rata-rata Harga (Juta Rp)', fontsize=13)
ax.set_title('AC vs Tanpa AC: Sebanding dengan Selisih Harganya?', fontsize=14, fontweight='bold')
ab(ax, f'Kos Tanpa AC: {fr(no_ac.mean())} (n={len(no_ac)})\nKos Dengan AC: {fr(has_ac.mean())} (n={len(has_ac)})\n\nSelisih: {fr(ac_diff)}\n\n💡 AC bikin harga naik\nRp {ac_diff:,.0f} rata-rata!\n\nApakah sebanding?\nTergantung cuaca dan\ntoleransi panas kamu 😅', xy=(0.55,0.92), fs=10)
sf('14_ac_worth_it.png')

# --- 15. KM DALAM WORTH IT? ---
print('  15. KM DALAM VS LUAR')
if 'fac_bath_K. Mandi Dalam' in dv.columns:
    km_in = dv[dv['fac_bath_K. Mandi Dalam']>0]['price']
    km_out = dv[dv['fac_bath_K. Mandi Dalam']==0]['price']
    km_diff = km_in.mean() - km_out.mean()
    fig,ax = plt.subplots(figsize=(10,7))
    ax.bar(['KM Luar (Bersama)', 'KM Dalam (Private)'], [km_out.mean()/1e6, km_in.mean()/1e6],
           yerr=[km_out.std()/1e6, km_in.std()/1e6], color=[C[3],C[5]], capsize=10, width=0.4, edgecolor='black')
    for i,val in enumerate([km_out.mean()/1e6, km_in.mean()/1e6]):
        ax.text(i, val+0.15, f'{fr([km_out.mean(),km_in.mean()][i])}', ha='center', fontsize=12, fontweight='bold')
    ax.set_ylabel('Rata-rata Harga (Juta Rp)', fontsize=13)
    ax.set_title('Kamar Mandi Dalam vs Luar: Worth It Nambah?', fontsize=14, fontweight='bold')
    ab(ax, f'KM Luar (bersama): {fr(km_out.mean())}\nKM Dalam (private): {fr(km_in.mean())}\n\nSelisih: {fr(km_diff)}\n\n91.7% kos punya KM Dalam\nWajar jadi standar!\n\n💡 Tambah Rp {km_diff:,.0f}\nuntuk privasi & kenyamanan', xy=(0.55,0.92), fs=10)
    sf('15_km_dalam_worth_it.png')

# --- 16. HEATMAP FASILITAS PER TIER ---
print('  16. SEBARAN FASILITAS PER TIER')
fac_display = ['fac_room_AC','fac_room_Kasur','fac_room_Lemari / Storage','fac_share_WiFi',
               'fac_share_CCTV','fac_share_Dapur','fac_bath_K. Mandi Dalam','fac_bath_Shower','fac_bath_Air panas','fac_bath_Air panas']
fac_available = [f for f in ['fac_room_AC','fac_room_Kasur','fac_room_Lemari / Storage','fac_share_WiFi','fac_share_CCTV',
                             'fac_share_Dapur','fac_bath_K. Mandi Dalam','fac_bath_Shower','fac_bath_Air panas'] if f in dv.columns]
if len(fac_available) > 0:
    hm_data = dv.groupby('tier', observed=True)[fac_available].mean().multiply(100).round(1)
    hm_labels = [f.replace('fac_room_','').replace('fac_share_','').replace('fac_bath_','').replace('_',' ').title() for f in fac_available]
    fig,ax = plt.subplots(figsize=(12,8))
    sns.heatmap(hm_data, annot=True, fmt='.0f', cmap='YlGnBu', ax=ax, cbar_kws={'label':'% Kos'}, 
                xticklabels=hm_labels, linewidths=1, linecolor='white')
    ax.set_title('Persentase Fasilitas per Tier Harga (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tier Harga'); ax.set_xlabel('Fasilitas')
    plt.xticks(rotation=30, ha='right')
    sf('16_heatmap_fasilitas_tier.png')

# --- 17. JUMLAH FASILITAS VS HARGA ---
print('  17. JUMLAH FASILITAS VS HARGA')
slope_f,inter_f,r_f,p_f,_ = linregress(dv['ft'], dv['price'])
fig,ax = plt.subplots(figsize=(12,7))
ax.scatter(dv['ft'], dv['price']/1e6, c=dv['price']/1e6, cmap='plasma', alpha=0.6, s=50, edgecolor='black', lw=0.3)
xl = np.linspace(dv['ft'].min(), dv['ft'].max(), 100)
ax.plot(xl, (slope_f*xl+inter_f)/1e6, color='red', lw=2.5)
fg = dv.groupby('ft')['price'].mean()
ax.scatter(fg.index, fg.values/1e6, color='white', marker='o', s=80, edgecolor='red', lw=2, zorder=5)
ax.set_xlabel('Jumlah Fasilitas', fontsize=13)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Apakah Lebih Banyak Fasilitas = Lebih Mahal?', fontsize=14, fontweight='bold')
ab(ax, f'Korelasi: r = {r_f:.3f}\np = {p_f:.4f} ({"signifikan" if p_f<0.05 else "tidak"})\n\nRata-rata fasilitas: {dv["ft"].mean():.1f}\nRata-rata harga: {fr(dv["price"].mean())}\n\n💡 Setiap +1 fasilitas\nharga naik Rp {slope_f:,.0f}', xy=(0.55,0.92), fs=10)
sf('17_jumlah_fasilitas_vs_harga.png')

# ====================================================================
# TEMA 4: PREDIKSI & ESTIMASI (18-25)
# ====================================================================
print('\n' + '='*70)
print('  TEMA 4: PREDIKSI & ESTIMASI')
print('='*70)

# --- 18. PREDIKSI HARGA DARI LUAS ---
print('  18. PREDIKSI HARGA DARI LUAS KAMAR')
vs = dv.dropna(subset=['size_area','price'])
sl,inter,r_val,p_val,_ = linregress(vs['size_area'], vs['price'])
fig,ax = plt.subplots(figsize=(12,7))
ax.scatter(vs['size_area'], vs['price']/1e6, c=vs['price']/1e6, cmap='viridis', alpha=0.6, s=50, edgecolor='black', lw=0.3)
xl = np.linspace(vs['size_area'].min(), vs['size_area'].max(), 100)
ax.plot(xl, (sl*xl+inter)/1e6, color='red', lw=2.5, label=f'Harga = {inter:,.0f} + {sl:.0f} × Luas')
cbar = plt.colorbar(plt.cm.ScalarMappable(cmap='viridis'), ax=ax, label='Harga (Juta Rp)')
ax.set_xlabel('Luas Kamar (m²)', fontsize=13)
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Prediksi Harga Berdasarkan Luas Kamar', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ab(ax, f'Rumus:\nHarga = {inter:,.0f} + {sl:.0f} × Luas(m²)\n\nR² = {r_val**2:.3f}\nKorelasi: r = {r_val:.3f}\n\nContoh:\n12m² → {fr(inter+sl*12)}\n15m² → {fr(inter+sl*15)}\n20m² → {fr(inter+sl*20)}\n25m² → {fr(inter+sl*25)}\n\n⚠️ Prediksi kasar, akurasi {r_val**2*100:.0f}%', xy=(0.55,0.92), fs=9)
sf('18_prediksi_harga_luas.png')

# --- 19. REGRESI BERGANDA ---
print('  19. PREDIKSI MULTI-FAKTOR')
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
features = ['size_area','jarak_unud_jimbaran_km','building_year','ft']
ml_df = dv[features + ['price']].dropna()
if len(ml_df) > 5:
    X = ml_df[features]
    y = ml_df['price']
    lr = LinearRegression()
    lr.fit(X, y)
    y_pred = lr.predict(X)
    r2_multi = r2_score(y, y_pred)
    coefs = dict(zip(features, lr.coef_))
    print(f'  R² multi: {r2_multi:.3f}')
    print(f'  Coefs: {coefs}')
    fig,ax = plt.subplots(figsize=(12,7))
    ax.scatter(y/1e6, y_pred/1e6, alpha=0.6, color=C[0], s=50, edgecolor='black', lw=0.3)
    ax.plot([0,12], [0,12], color='red', ls='--', lw=2, label='Prediksi = Aktual')
    ax.set_xlabel('Harga Aktual (Juta Rp)', fontsize=13)
    ax.set_ylabel('Harga Prediksi (Juta Rp)', fontsize=13)
    ax.set_title('Prediksi Harga Multi-Faktor (Regresi Berganda)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ab(ax, f'Faktor: Size + Jarak + Tahun + Fasilitas\nR² = {r2_multi:.3f}\n\nKoefisien:\nLuas: +Rp {coefs["size_area"]:,.0f}/m²\nJarak: -Rp {abs(coefs["jarak_unud_jimbaran_km"]):,.0f}/km\nTahun: +Rp {coefs["building_year"]:,.0f}/tahun\nFasilitas: +Rp {coefs["ft"]:,.0f}/item\n\nAkurasi: {r2_multi*100:.0f}%', xy=(0.55,0.92), fs=9)
    sf('19_prediksi_multifaktor.png')

# --- 20. HARGA PER M2 YANG WAJAR (P33/P66-based) ---
print('  20. EKSPEKTASI HARGA PER M² YANG WAJAR')
tier_pps = dv.groupby('tier', observed=True)['pps'].agg(['mean','median','std','count'])
print(tier_pps.to_string())
fig,ax = plt.subplots(figsize=(12,7))
t_pps = [dv[dv['tier']==t]['pps'].dropna().values for t in tier_lbls]
bp = ax.boxplot(t_pps, labels=tier_lbls, patch_artist=True, widths=0.5, medianprops=dict(color='red',lw=2.5))
for patch,c in zip(bp['boxes'],[C[5],C[0],C[1],C[2],C[3]]):
    patch.set_facecolor(c)
for i,t in enumerate(tier_lbls):
    m = dv[dv['tier']==t]['pps'].mean()
    ax.text(i+1, m+5000, f'Rp {m:,.0f}/m²', ha='center', fontsize=9, fontweight='bold', color='blue')
ax.set_xlabel('Tier Harga', fontsize=13)
ax.set_ylabel('Harga per m² (Rp)', fontsize=13)
ax.set_title('Berapa Harga per m² yang Wajar di Setiap Tier?', fontsize=14, fontweight='bold')
pps_p33 = dv['pps'].quantile(0.33)
pps_p66 = dv['pps'].quantile(0.66)
ab(ax, f'Rata-rata Rp {dv["pps"].mean():,.0f}/m²\nMedian Rp {dv["pps"].median():,.0f}/m²\n\n💡 Threshold wajar:\n<Rp {pps_p33/1000:,.0f}rb/m² = MURAH\nRp {pps_p33/1000:,.0f}-{pps_p66/1000:,.0f}rb/m² = STANDAR\n>Rp {pps_p66/1000:,.0f}rb/m² = MAHAL\n\nCek kos idamanmu!', xy=(0.55,0.92), fs=10)
sf('20_harga_per_m2_wajar.png')

# --- 21. SIMULASI NAIK BUDGET ---
print('  21. SIMULASI NAIK BUDGET RP 500RB')
tiers_compare = [tier_lbls[1], tier_lbls[2]]  # Q20-Q40 vs Q40-Q60
t1 = dv[dv['tier']==tiers_compare[0]]
t2 = dv[dv['tier']==tiers_compare[1]]
comp_data = {
    'Metric': ['Rata-rata Luas','Rata-rata Jarak','Rata-rata Fasilitas','AC%','WiFi%','KM Dalam%'],
    tiers_compare[0]: [f'{t1["size_area"].mean():.1f}m²',f'{t1["jarak_unud_jimbaran_km"].mean():.2f}km',f'{t1["ft"].mean():.1f}',
                       f'{t1["fac_room_AC"].mean()*100:.0f}%' if 'fac_room_AC' in dv.columns else '-',
                       f'{t1["fac_share_WiFi"].mean()*100:.0f}%' if 'fac_share_WiFi' in dv.columns else '-',
                       f'{t1["fac_bath_K. Mandi Dalam"].mean()*100:.0f}%' if 'fac_bath_K. Mandi Dalam' in dv.columns else '-'],
    tiers_compare[1]: [f'{t2["size_area"].mean():.1f}m²',f'{t2["jarak_unud_jimbaran_km"].mean():.2f}km',f'{t2["ft"].mean():.1f}',
                       f'{t2["fac_room_AC"].mean()*100:.0f}%' if 'fac_room_AC' in dv.columns else '-',
                       f'{t2["fac_share_WiFi"].mean()*100:.0f}%' if 'fac_share_WiFi' in dv.columns else '-',
                       f'{t2["fac_bath_K. Mandi Dalam"].mean()*100:.0f}%' if 'fac_bath_K. Mandi Dalam' in dv.columns else '-'],
}
fig,ax = plt.subplots(figsize=(12,7))
ax.axis('off')
table_data = [[k, v1, v2] for k,v1,v2 in zip(comp_data['Metric'], comp_data[tiers_compare[0]], comp_data[tiers_compare[1]])]
table = ax.table(cellText=table_data, colLabels=['Aspek', tiers_compare[0], tiers_compare[1]],
                 loc='center', cellLoc='center')
table.auto_set_font_size(False); table.set_fontsize(11)
table.scale(1.5, 2)
for j in range(3):
    table[0,j].set_facecolor(C[0]); table[0,j].set_text_props(color='white', fontweight='bold')
ax.set_title(f'Simulasi: Naik Budget Rp 500rb, Apa yang Berubah?\n{tiers_compare[0]} → {tiers_compare[1]}', fontsize=14, fontweight='bold', pad=20)
sf('21_simulasi_naik_budget.png')

# --- 22. KAPAN HARGA TERMASUK MAHAL ---
print('  22. KAPAN HARGA TERMASUK MAHAL?')
tier_counts = dv['tier'].value_counts()
fig,ax = plt.subplots(figsize=(12,7))
wedges,texts,autotexts = ax.pie(
    [tier_counts.get(t,0) for t in tier_lbls],
    labels=[f'{t}\n({tier_counts.get(t,0)} kos)' for t in tier_lbls],
    autopct='%1.1f%%', startangle=90,
    colors=[C[5],C[0],C[1],C[2],C[3]],
    pctdistance=0.75, textprops=dict(fontsize=10))
for t in autotexts: t.set_fontweight('bold'); t.set_fontsize(11)
ax.set_title('Distribusi Kategori Harga: Murah hingga Premium', fontsize=14, fontweight='bold')
labels_map = {'<': 'Murah', '>': 'Premium'}
tier_nice = []
for t in tier_lbls:
    prefix = 'Murah' if t[0] == '<' else 'Premium' if t[0] == '>' else 'Terjangkau' if t == tier_lbls[1] else 'Standar' if t == tier_lbls[2] else 'Mahal'
    tier_nice.append(f'{prefix} ({t}):\n{tier_counts.get(t,0)} kos ({tier_counts.get(t,0)/len(dv)*100:.1f}%)')
ab(ax, '\n\n'.join(tier_nice), xy=(0.02,0.97), fs=9)
sf('22_kategori_mahal_premium.png')

# --- 23. TAHUN BANGUNAN VS HARGA ---
print('  23. ESTIMASI TAHUN BANGUNAN VS HARGA')
by_df = dv.dropna(subset=['building_year','price'])
if len(by_df) > 5:
    sl_by,inter_by,r_by,p_by,_ = linregress(by_df['building_year'], by_df['price'])
    fig,ax = plt.subplots(figsize=(12,7))
    ax.scatter(by_df['building_year'], by_df['price']/1e6, alpha=0.6, color=C[1], s=50, edgecolor='black', lw=0.3)
    xl = np.linspace(by_df['building_year'].min(), by_df['building_year'].max(), 100)
    ax.plot(xl, (sl_by*xl+inter_by)/1e6, color='red', lw=2.5)
    ax.set_xlabel('Tahun Bangunan', fontsize=13)
    ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
    ax.set_title('Apakah Kos Baru Lebih Mahal?', fontsize=14, fontweight='bold')
    ab(ax, f'Korelasi: r = {r_by:.3f}\np = {p_by:.4f} ({"signifikan" if p_by<0.05 else "tidak"})\nR² = {r_by**2:.3f}\n\nRata-rata tahun: {by_df["building_year"].mean():.0f}\n\n💡 Kos baru cenderung\n{"lebih mahal" if sl_by>0 else "lebih murah"} Rp {abs(sl_by):,.0f}/tahun', xy=(0.55,0.92), fs=10)
    sf('23_tahun_bangunan_vs_harga.png')

# --- 24. AVAILABLE ROOM ---
print('  24. DISTRIBUSI AVAILABLE ROOM')
avail = dv['available_room'].dropna()
fig,ax = plt.subplots(figsize=(12,7))
ax.hist(avail, bins=range(0,int(avail.max())+2), color=C[0], edgecolor='white', alpha=0.85)
ax.set_xlabel('Jumlah Kamar Tersedia', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Berapa Banyak Kamar Kosong yang Tersedia?', fontsize=14, fontweight='bold')
ab(ax, f'Total kamar kosong: {int(avail.sum())}\nRata-rata: {avail.mean():.1f}/kos\nMedian: {avail.median():.0f}/kos\n\nKos tanpa kamar kosong:\n{(avail==0).sum()} kos\n\n💡 Ada {int(avail.sum())} kamar\nsiap huni sekarang!', xy=(0.55,0.92), fs=10)
sf('24_available_room.png')

# --- 25. VIEWS & LOVES vs HARGA ---
print('  25. EKSPEKTASI POPULARITAS PER HARGA')
tier_vl = dv.groupby('tier', observed=True)[['view_count','love_count']].mean()
print(tier_vl.to_string())
fig,ax1 = plt.subplots(figsize=(12,7))
x_pos = range(len(tier_lbls))
ax1.bar(x_pos, tier_vl['view_count'].values/1000, color=C[0], alpha=0.8, label='Rata-rata Dilihat (ribuan)', width=0.4)
ax2 = ax1.twinx()
ax2.plot(x_pos, tier_vl['love_count'].values, color=C[3], marker='o', lw=2.5, markersize=8, label='Rata-rata Disukai')
ax1.set_xticks(x_pos); ax1.set_xticklabels(tier_lbls, fontsize=9)
ax1.set_ylabel('Rata-rata Dilihat (ribuan)', fontsize=12, color=C[0])
ax2.set_ylabel('Rata-rata Disukai', fontsize=12, color=C[3])
ax1.set_title('Ekspektasi Popularitas: Views & Loves per Tier Harga', fontsize=14, fontweight='bold')
lines1,labels1 = ax1.get_legend_handles_labels()
lines2,labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labels1+labels2, loc='upper right', fontsize=11)
sf('25_popularitas_per_tier.png')

# ====================================================================
# TEMA 5: SIMULASI & KEPUTUSAN (26-35)
# ====================================================================
print('\n' + '='*70)
print('  TEMA 5: SIMULASI & KEPUTUSAN')
print('='*70)

# --- 26. SIMULASI FILTER (median + Q3-based) ---
print('  26. SIMULASI CARI KOS IDEAL')
budget_sim = dv['price'].median()
max_dist = dv['jarak_unud_jimbaran_km'].quantile(0.75)
pref_fac = ['fac_room_AC','fac_share_WiFi','fac_bath_K. Mandi Dalam']
avail_fac = [f for f in pref_fac if f in dv.columns]
filtered = dv[(dv['price']<=budget_sim) & (dv['jarak_unud_jimbaran_km']<=max_dist)].copy()
for f in avail_fac:
    filtered = filtered[filtered[f]>0]
fig,ax = plt.subplots(figsize=(12,7))
n_total = len(dv)
steps = [f'Total Kos\n{n_total}', f'Budget ≤{fr(budget_sim)}\n{(dv["price"]<=budget_sim).sum()} kos',
         f'Jarak ≤{max_dist}km\n{((dv["price"]<=budget_sim)&(dv["jarak_unud_jimbaran_km"]<=max_dist)).sum()} kos',
         f'+AC+WiFi+KM Dalam\n{len(filtered)} kos']
vals = [len(dv), (dv['price']<=budget_sim).sum(), ((dv["price"]<=budget_sim)&(dv["jarak_unud_jimbaran_km"]<=max_dist)).sum(), len(filtered)]
colors_f = [C[0],C[5],C[1],C[2]]
bars = ax.bar(range(4), vals, color=colors_f, edgecolor='black', width=0.5)
for i,val in enumerate(vals):
    ax.text(i, val+5, f'{val} kos\n({val/n_total*100:.1f}%)', ha='center', fontsize=11, fontweight='bold')
ax.set_xticks(range(4)); ax.set_xticklabels(steps, fontsize=9)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title(f'Simulasi Filter: Cari Kos Ideal dengan Budget {fr(budget_sim)}', fontsize=14, fontweight='bold')
ax.set_ylim(0, 270)
ab(ax, f'Dari {n_total} kos,\nhanya {len(filtered)} yang\ncocok dengan kriteriamu!\n\nBudget: {fr(budget_sim)}\nJarak: ≤{max_dist}km\nFasilitas: AC+WiFi+KM Dalam\n\n💡 Kamu punya\n{len(filtered)} pilihan!', xy=(0.55,0.92), fs=10)
sf('26_simulasi_filter.png')

# --- 27. WAKTU TERBAIK CARI KOS ---
print('  27. KAPAN WAKTU TERBAIK CARI KOS?')
avail_counts = dv['available_room'].dropna()
fig,ax = plt.subplots(figsize=(12,7))
ax.hist(avail_counts, bins=range(0,int(avail_counts.max())+2), color=C[5], edgecolor='white', alpha=0.85)
ax.axvline(avail_counts.mean(), color='red', ls='--', lw=2.5, label=f'Rata-rata: {avail_counts.mean():.1f}')
ax.set_xlabel('Kamar Tersedia', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Kapan Waktu Terbaik Cari Kos?', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ab(ax, f'{int(avail_counts.sum())} kamar kosong\n{int((avail_counts>0).sum())} kos punya kamar\n\nRata-rata {avail_counts.mean():.1f} kamar/kos\n\n💡 Makin banyak available\n= makin gampang nego\n= makin cepat masuk\n\nCari pas akhir bulan\nbiasanya banyak kosong!', xy=(0.55,0.92), fs=10)
sf('27_waktu_terbaik_cari_kos.png')

# --- 28. PREDIKSI KENAIKAN -- using inflation proxy ---
print('  28. PREDIKSI KENAIKAN HARGA 1 TAHUN')
inflation = 0.05
future_price = dv['price'] * (1 + inflation)
fig,ax = plt.subplots(figsize=(12,7))
ax.hist(dv['price']/1e6, bins=25, alpha=0.6, color=C[0], edgecolor='white', label=f'Sekarang (rata-rata {fr(dv["price"].mean())})')
ax.hist(future_price/1e6, bins=25, alpha=0.4, color=C[3], edgecolor='white', label=f'Tahun depan (estimasi {fr(future_price.mean())})')
ax.axvline(dv['price'].mean()/1e6, color=C[0], ls='--', lw=2)
ax.axvline(future_price.mean()/1e6, color=C[3], ls='--', lw=2)
ax.set_xlabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_ylabel('Jumlah Kos', fontsize=13)
ax.set_title('Prediksi Kenaikan Harga 1 Tahun ke Depan', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ab(ax, f'Estimasi inflasi: 5%/tahun\n\nSekarang:\nRata-rata {fr(dv["price"].mean())}\n\nTahun depan:\nRata-rata {fr(future_price.mean())}\n\nBatas aman skrg: Rp 2,5jt\nBatas aman nanti: Rp 2,63jt\n\n💡 Lebih cepat cari kos\nlebih hemat!', xy=(0.55,0.92), fs=10)
sf('28_prediksi_kenaikan_harga.png')

# --- 29. KLASIFIKASI TIER ---
print('  29. KAMU TIER MANA?')
fig,ax = plt.subplots(figsize=(14,10))
ax.axis('off')
cls_data = [
    ['Input / Kriteria', 'Tier 1: Hemat', 'Tier 2: Standar', 'Tier 3: Nyaman', 'Tier 4: Premium'],
    ['Budget', '<Rp 1,5jt', 'Rp 1,5-2,5jt', 'Rp 2,5-3,5jt', '>Rp 3,5jt'],
    ['Luas Ekspektasi', '~13,5m²', '~14,5m²', '~18,8m²', '~30m²+'],
    ['Jarak dari Kampus', '2,2km', '2,7km', '2,0km', '2,1km'],
    ['Fasilitas Dijamin', 'Kasur+Lemari', '+AC+WiFi', '+CCTV+Dapur', '+Air Panas'],
    ['Target Mahasiswa', 'Budget ketat', 'Mahasiswa umum', 'Mapan/kelas atas', 'Sangat mapan'],
    ['Contoh Kos', 'Kost Ray (Rp830rb)', 'Kost Mandala 2 (Rp1,8jt)', 'Kost MD Living (Rp2,6jt)', 'Kost Uma Katani (Rp8jt)'],
]
table = ax.table(cellText=cls_data, loc='center', cellLoc='center', colWidths=[0.2,0.2,0.2,0.2,0.2])
table.auto_set_font_size(False); table.set_fontsize(10)
table.scale(1.3, 2)
for j in range(5):
    table[0,j].set_facecolor(C[0]); table[0,j].set_text_props(color='white', fontweight='bold')
colors_tier = [C[5],C[0],C[1],C[2],C[3]]
for i in range(1,len(cls_data)):
    for j in range(1,5):
        table[i,j].set_facecolor(colors_tier[j-1])
        table[i,j].set_alpha(0.15)
ax.set_title('Klasifikasi: Kamu Cocok di Tier Mana?', fontsize=14, fontweight='bold', pad=20)
sf('29_klasifikasi_tier.png')

# --- 30. FAIRNESS SCORE ---
print('  30. ESTIMASI FAIRNESS SCORE')
vs_fair = dv.dropna(subset=['price','size_area','jarak_unud_jimbaran_km']).copy()
if len(vs_fair) > 10:
    avg_pps = vs_fair['pps'].mean()
    avg_dist = vs_fair['jarak_unud_jimbaran_km'].mean()
    vs_fair['fair_score'] = 100 - (
        abs(vs_fair['pps']-avg_pps)/avg_pps * 50 +
        abs(vs_fair['jarak_unud_jimbaran_km']-avg_dist)/avg_dist * 50
    ).clip(0, 100)
    top_fair = vs_fair.nlargest(10, 'fair_score')[['nama_kost','price','size_area','jarak_unud_jimbaran_km','pps','fair_score']]
    print('  10 Kos Paling Fair:')
    print(top_fair.to_string())
    fig,ax = plt.subplots(figsize=(14,8))
    nms30 = [n[:35]+'..' if len(str(n))>35 else n for n in top_fair['nama_kost'].values]
    colors_fair = plt.cm.Greens(np.linspace(0.3,0.9,10))
    bars = ax.barh(range(10), top_fair['fair_score'].values, color=colors_fair, edgecolor='black', height=0.6)
    for i,(_,r) in enumerate(top_fair.iterrows()):
        ax.text(r['fair_score']+1, i, f'{fr(r["price"])} | {r["size_area"]:.0f}m² | {r["jarak_unud_jimbaran_km"]:.1f}km',
                va='center', fontsize=9, fontweight='bold')
    ax.set_yticks(range(10)); ax.set_yticklabels(nms30, fontsize=8)
    ax.set_xlabel('Fairness Score (semakin tinggi = semakin worth it)', fontsize=12)
    ax.set_title('10 Kos Paling Fair: Harga vs Luas vs Jarak', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    ab(ax, f'Fairness Score = 100 - (penalty)\n\nHarga/m² rata-rata:\nRp {avg_pps:,.0f}\nJarak rata-rata:\n{avg_dist:.2f}km\n\n⚠️ Makin tinggi score\n= makin worth it', xy=(0.55,0.92), fs=9)
    sf('30_fairness_score.png')

# --- 31. RATING VS HARGA ---
print('  31. PREDIKSI RATING BERDASARKAN HARGA')
rating_df = dv.dropna(subset=['rating','price'])
if len(rating_df) > 5:
    sl_r,inter_r,r_r,p_r,_ = linregress(rating_df['price'], rating_df['rating'])
    fig,ax = plt.subplots(figsize=(12,7))
    ax.scatter(rating_df['price']/1e6, rating_df['rating'], alpha=0.6, color=C[1], s=50, edgecolor='black', lw=0.3)
    xl = np.linspace(rating_df['price'].min(), rating_df['price'].max(), 100)
    ax.plot(xl/1e6, sl_r*xl+inter_r, color='red', lw=2.5)
    ax.set_xlabel('Harga (Juta Rp)', fontsize=13)
    ax.set_ylabel('Rating', fontsize=13)
    ax.set_title('Apakah Kos Mahal Punya Rating Lebih Baik?', fontsize=14, fontweight='bold')
    ab(ax, f'Korelasi: r = {r_r:.3f}\np = {p_r:.4f} ({"signifikan" if p_r<0.05 else "tidak"})\n\nRata-rata rating: {rating_df["rating"].mean():.2f}\nRating tertinggi: {rating_df["rating"].max():.1f}\n\n⚠️ Hanya {len(rating_df)} kos\npunya rating!\n\n💡 Harga TIDAK menjamin\nrating bagus!', xy=(0.55,0.92), fs=10)
    sf('31_rating_vs_harga.png')

# --- 32. CAMPUR VS PUTRI ---
print('  32. KOS CAMPUR VS PUTRI')
g32 = dv.groupby('gen')['price']
campur = dv[dv['gen']=='Campur']['price'].dropna()
putri = dv[dv['gen']=='Putri']['price'].dropna()
fig,ax = plt.subplots(figsize=(10,7))
data32 = [campur.values/1e6, putri.values/1e6]
bp = ax.boxplot(data32, labels=['Campur','Putri'], patch_artist=True, widths=0.4, medianprops=dict(color='red',lw=2.5))
for patch,c in zip(bp['boxes'],[C[0],C[1]]):
    patch.set_facecolor(c)
means32 = [campur.mean()/1e6, putri.mean()/1e6]
ax.scatter([1,2], means32, color='blue', marker='D', s=80, zorder=5)
for i,(lbl,m) in enumerate(zip(['Campur','Putri'],[campur.mean(),putri.mean()])):
    ax.text(i+1, means32[i]+0.2, f'n={len(dv[dv["gen"]==lbl])}\n{fr(m)}', ha='center', fontsize=10, fontweight='bold')
ax.set_ylabel('Harga Bulanan (Juta Rp)', fontsize=13)
ax.set_title('Perbandingan Harga: Kos Campur vs Putri', fontsize=14, fontweight='bold')
if len(campur)>0 and len(putri)>0:
    _,p32 = stats.ttest_ind(campur, putri, equal_var=False)
    ab(ax, f'Selisih: {fr(campur.mean()-putri.mean())}\nt-test p = {p32:.2e}\n{"⚠️ SIGNIFIKAN!" if p32<0.05 else "Tidak signifikan"}\n\nKos Putri rata-rata\nRp {(campur.mean()-putri.mean())/1e6:.2f}jt lebih murah!', xy=(0.55,0.92), fs=10)
sf('32_campur_vs_putri.png')

# --- 33. OVERPRICED VS UNDERPRICED ---
print('  33. ESTIMASI OVERPRICED & UNDERPRICED')
if 'size_area' in dv.columns:
    vs33 = dv.dropna(subset=['size_area','price','jarak_unud_jimbaran_km','ft'])
    if len(vs33) > 10:
        X33 = vs33[['size_area','jarak_unud_jimbaran_km','ft']].fillna(0)
        y33 = vs33['price']
        lr33 = LinearRegression()
        lr33.fit(X33, y33)
        vs33['pred_price'] = lr33.predict(X33)
        vs33['residual'] = vs33['price'] - vs33['pred_price']
        q1_r = vs33['residual'].quantile(0.25)
        q3_r = vs33['residual'].quantile(0.75)
        iqr_r = q3_r - q1_r
        upper_fence = q3_r + 1.5 * iqr_r
        lower_fence = q1_r - 1.5 * iqr_r
        over = vs33[vs33['residual'] > upper_fence].nlargest(10, 'residual')[['nama_kost','price','pred_price','residual','size_area']]
        under = vs33[vs33['residual'] < lower_fence].nsmallest(10, 'residual')[['nama_kost','price','pred_price','residual','size_area']]
        print(f'  IQR fence: Q1={fr(q1_r)} | Q3={fr(q3_r)} | IQR={fr(iqr_r)}')
        print(f'  Overpriced threshold: >{fr(upper_fence)}')
        print(f'  Underpriced threshold: <{fr(lower_fence)}')
        print(f'  Overpriced kos: {len(over)} | Underpriced kos: {len(under)}')
        print('OVERPRICED (IQR outlier):')
        print(over.to_string() if len(over) > 0 else '  (none)')
        print('UNDERPRICED (IQR outlier):')
        print(under.to_string() if len(under) > 0 else '  (none)')
        fig,axes33 = plt.subplots(1,2,figsize=(16,7))
        ax33a = axes33[0]
        nms_o = [n[:30]+'..' if len(str(n))>30 else n for n in over['nama_kost'].values]
        ax33a.barh(range(len(over)), over['residual'].values/1e6, color=C[3], edgecolor='black', height=0.6)
        for i,(_,r) in enumerate(over.iterrows()):
            ax33a.text(r['residual']/1e6+0.03, i, f'{fr(r["price"])} (kelebihan {fr(r["residual"])})', va='center', fontsize=9)
        ax33a.set_yticks(range(len(over))); ax33a.set_yticklabels(nms_o, fontsize=8)
        ax33a.set_xlabel('Kelebihan Harga (Juta Rp)'); ax33a.set_title(f'{len(over)} OVERPRICED (IQR outlier)', fontsize=13, fontweight='bold', color=C[3])
        ax33a.invert_yaxis()
        ax33b = axes33[1]
        nms_u = [n[:30]+'..' if len(str(n))>30 else n for n in under['nama_kost'].values]
        ax33b.barh(range(len(under)), abs(under['residual'].values)/1e6, color=C[5], edgecolor='black', height=0.6)
        for i,(_,r) in enumerate(under.iterrows()):
            ax33b.text(abs(r['residual'])/1e6+0.03, i, f'{fr(r["price"])} (hemat {fr(abs(r["residual"]))})', va='center', fontsize=9)
        ax33b.set_yticks(range(len(under))); ax33b.set_yticklabels(nms_u, fontsize=8)
        ax33b.set_xlabel('Kekurangan Harga (Juta Rp)'); ax33b.set_title(f'{len(under)} UNDERPRICED (IQR outlier)', fontsize=13, fontweight='bold', color=C[5])
        ax33b.invert_yaxis()
        fig.suptitle('Estimasi: Kos Overpriced vs Underpriced', fontsize=14, fontweight='bold', y=1.02)
        sf('33_overpriced_underpriced.png')

# --- 34. LOVE/VIEW RATIO ---
print('  34. PREDIKSI BERAPA LAMA KOS TERISI')
dv34 = dv.dropna(subset=['love_count','view_count','price'])
dv34['love_ratio'] = dv34['love_count'] / (dv34['view_count']/1000)
fig,ax = plt.subplots(figsize=(12,7))
sc = ax.scatter(dv34['price']/1e6, dv34['love_ratio'], c=dv34['love_ratio'], cmap='RdYlGn', s=60, edgecolor='black', lw=0.3)
cbar = plt.colorbar(sc, ax=ax, label='Love Ratio')
ax.set_xlabel('Harga (Juta Rp)', fontsize=13)
ax.set_ylabel('Love Count per 1.000 Views', fontsize=13)
ax.set_title('Prediksi Popularitas: Rasio Love vs View', fontsize=14, fontweight='bold')
lr_p75 = dv34['love_ratio'].quantile(0.75)
ab(ax, f'Rasio love/view tinggi\n= kos menarik & cepat terisi\n\n💡 Pilih kos dengan\nlove/view > {lr_p75:.0f} (P75)\nuntuk jaminan kualitas!', xy=(0.55,0.92), fs=10)
sf('34_love_view_ratio.png')

# --- 35. WHAT-IF DASHBOARD (median-based) ---
print('  35. WHAT-IF: SIMULASI BUDGET')
budget_sim2 = dv['price'].median()
sim_df = dv[dv['price']<=budget_sim2]
fig,ax = plt.subplots(figsize=(14,10))
ax.axis('off')
stats35 = [
    ['Total Kos dalam Budget', f'{len(sim_df)} kos'],
    ['Persentase dari Total', f'{len(sim_df)/len(dv)*100:.1f}%'],
    ['Rata-rata Harga', fr(sim_df['price'].mean())],
    ['Rata-rata Luas Kamar', f'{sim_df["size_area"].mean():.1f} m²'],
    ['Rata-rata Jarak dari Kampus', f'{sim_df["jarak_unud_jimbaran_km"].mean():.2f} km'],
    ['Rata-rata Jumlah Fasilitas', f'{sim_df["ft"].mean():.1f} item'],
    ['Kos dengan AC', f'{(sim_df["fac_room_AC"]>0).sum()} kos ({(sim_df["fac_room_AC"]>0).mean()*100:.0f}%)' if 'fac_room_AC' in sim_df.columns else '-'],
    ['Kos dengan WiFi', f'{(sim_df["fac_share_WiFi"]>0).sum()} kos ({(sim_df["fac_share_WiFi"]>0).mean()*100:.0f}%)' if 'fac_share_WiFi' in sim_df.columns else '-'],
    ['Kos dengan KM Dalam', f'{(sim_df["fac_bath_K. Mandi Dalam"]>0).sum()} kos ({(sim_df["fac_bath_K. Mandi Dalam"]>0).mean()*100:.0f}%)' if 'fac_bath_K. Mandi Dalam' in sim_df.columns else '-'],
    ['Rata-rata DP', f'{sim_df["dp_percentage"].dropna().mean():.1f}%' if len(sim_df["dp_percentage"].dropna())>0 else '-'],
    ['Estimasi Bulan Pertama', fr(sim_df['first_month'].mean()) if 'first_month' in sim_df.columns else '-'],
    ['3 Rekomendasi Terbaik', f'1. {sim_df.nsmallest(1,"pps")["nama_kost"].values[0][:30]}' if len(sim_df)>0 else '-'],
]
table35 = ax.table(cellText=stats35, colLabels=['Aspek', 'Hasil'], loc='center', cellLoc='left')
table35.auto_set_font_size(False); table35.set_fontsize(11)
table35.scale(1.5, 1.8)
table35[0,0].set_facecolor(C[0]); table35[0,1].set_facecolor(C[0])
table35[0,0].set_text_props(color='white', fontweight='bold')
table35[0,1].set_text_props(color='white', fontweight='bold')
for i in range(len(stats35)):
    if i < 3: table35[i+1,1].set_facecolor('#b7e4c7')
ax.set_title(f'What-If Dashboard: Budget {fr(budget_sim2)}\nApa yang Kamu Dapatkan?', fontsize=14, fontweight='bold', pad=20)
sf('35_whatif_dashboard.png')

# ====================================================================
# POSTER TABLE
# ====================================================================
print('\n' + '='*70)
print('  POSTER COMPARISON TABLE')
print('='*70)

poster_data = []
for t in tier_lbls:
    d = dv[dv['tier']==t]
    n = len(d)
    if n == 0: continue
    ac_pct = f'{d["fac_room_AC"].mean()*100:.0f}%' if 'fac_room_AC' in d.columns else '-'
    wifi_pct = f'{d["fac_share_WiFi"].mean()*100:.0f}%' if 'fac_share_WiFi' in d.columns else '-'
    km_pct = f'{d["fac_bath_K. Mandi Dalam"].mean()*100:.0f}%' if 'fac_bath_K. Mandi Dalam' in d.columns else '-'
    dp_mean = f'{d["dp_percentage"].dropna().mean():.0f}%' if len(d["dp_percentage"].dropna())>0 else '-'
    poster_data.append([t, str(n), fr(d['price'].mean()), fr(d['price'].median()),
                        f'{d["size_area"].mean():.1f}', f'{d["jarak_unud_jimbaran_km"].mean():.2f}',
                        ac_pct, wifi_pct, km_pct, dp_mean])

headers_p = ['Tier', 'n', 'Rata-rata', 'Median', 'Luas(m²)', 'Jarak(km)', 'AC', 'WiFi', 'KM Dalam', 'DP']
fig,ax = plt.subplots(figsize=(18,8))
ax.axis('off')
tbl = ax.table(cellText=poster_data, colLabels=headers_p, loc='center', cellLoc='center')
tbl.auto_set_font_size(False); tbl.set_fontsize(10)
tbl.scale(1.3, 1.8)
for j in range(len(headers_p)):
    tbl[0,j].set_facecolor('#2E86AB'); tbl[0,j].set_text_props(color='white', fontweight='bold')
for i in range(len(poster_data)):
    for j in range(len(headers_p)):
        cell = poster_data[i][j]
        if cell.endswith('%'):
            val = int(cell.replace('%',''))
            if val >= 90: tbl[i+1,j].set_facecolor('#b7e4c7')
            elif val >= 50: tbl[i+1,j].set_facecolor('#ffe5b4')
            else: tbl[i+1,j].set_facecolor('#ffcccc')
ax.set_title('📊 TABEL PERBANDINGAN: Semua Tier Harga untuk Poster', fontsize=16, fontweight='bold', pad=20)
sf('poster_tabel_perbandingan.png')

# ====================================================================
# SUMMARY
# ====================================================================
print('\n' + '='*70)
print('  RINGKASAN ANGKA')
print('='*70)

summary = f'''
{"="*60}
  35 INSIGHT KOS UNTUK MAHASISWA - RINGKASAN
{"="*60}

1. GAMBARAN HARGA
   Rata-rata: {fr(p.mean())}  |  Median: {fr(p.median())}
   Termurah: {fr(p.min())}  |  Termahal: {fr(p.max())}

2. BUDGET KUMULATIF
    <={fr(budgets[1])}: {bcnt[1]} kos ({bpct[1]:.1f}%)
    <={fr(budgets[2])}: {bcnt[2]} kos ({bpct[2]:.1f}%)
    <={fr(budgets[3])}: {bcnt[3]} kos ({bpct[3]:.1f}%) ★
    <={fr(budgets[4])}: {bcnt[4]} kos ({bpct[4]:.1f}%)

3. BIAYA BULAN PERTAMA
   Rata-rata: {fr(fm.mean())}  |  Median: {fr(fm.median())}

4. DP
   Rata-rata: {dp.mean():.1f}%  |  Median: {dp.median():.1f}%

5. JARAK ZONA
   <1km: {fr(z_stats.loc["<1km","mean"])} (n={z_stats.loc["<1km","count"]:.0f})
   1-2km: {fr(z_stats.loc["1-2km","mean"])} (n={z_stats.loc["1-2km","count"]:.0f})
   >5km: {fr(z_stats.loc[">5km","mean"])} (n={z_stats.loc[">5km","count"]:.0f})

6. HEMAT JALAN JAUH
   <1km vs >5km: hemat {fr(diff)}/bulan

7. PREDIKSI HARGA
   Harga = {inter:,.0f} + {sl:.0f} × Luas(m²)  (R²={r_val**2:.3f})

8. PREDIKSI MULTI-FAKTOR
   R² = {r2_multi:.3f} ({r2_multi*100:.1f}%)

9. AC vs TANPA AC
   Selisih: {fr(ac_diff)}

10. KM DALAM vs LUAR
    Selisih: {fr(km_diff)}

11. FASILITAS UMUM:
     Kamar: AC ({tier_fac[tier_lbls[2]].get("fac_room_AC","-")}% tier standar)
     Umum: WiFi ({tier_fac[tier_lbls[2]].get("fac_share_WiFi","-")}% tier standar)
     Mandi: KM Dalam ({tier_fac[tier_lbls[2]].get("fac_bath_K. Mandi Dalam","-")}% tier standar)

12. KATEGORI HARGA
    Murah: {tier_counts.get(tier_lbls[0],0)} kos
    Terjangkau: {tier_counts.get(tier_lbls[1],0)} kos
    Standar: {tier_counts.get(tier_lbls[2],0)} kos
    Mahal: {tier_counts.get(tier_lbls[3],0)} kos
    Premium: {tier_counts.get(tier_lbls[4],0)} kos

13. GENDER
    Campur: {fr(g32.mean().get("Campur",0))} (n={g32.count().get("Campur",0)})
    Putri: {fr(g32.mean().get("Putri",0))} (n={g32.count().get("Putri",0)})

14. TAHUN BANGUNAN
    Rata-rata: {by_df["building_year"].mean():.0f}  |  Range: {int(by_df["building_year"].min())}-{int(by_df["building_year"].max())}

15. KAMAR KOSONG
    Total: {int(avail.sum())} kamar  |  Rata-rata: {avail.mean():.1f}/kos

16. RATING & HARGA: r = {r_r:.3f} ({"signifikan" if p_r<0.05 else "tidak"})

17. FASILITAS vs HARGA: r = {r_f:.3f}

18. VIEWS vs HARGA: Inverse relationship

19. KENAIKAN TAHUNAN (estimasi 5%): {fr(future_price.mean()-dv["price"].mean())}

20. FILTER SIMULASI ({fr(budget_sim)} + ≤{max_dist:.1f}km + AC+WiFi+KM Dalam): {len(filtered)} kos cocok

'''
try:
    print(summary)
except UnicodeEncodeError:
    print(summary.encode('ascii', 'replace').decode('ascii'))
with open(os.path.join(OUT, 'ringkasan.txt'), 'w', encoding='utf-8') as f:
    f.write(summary)
print(f'\n  [OK] Semua file di: {OUT}/')
print(f'  Total: 35 PNG + 1 Poster Table + Ringkasan')
