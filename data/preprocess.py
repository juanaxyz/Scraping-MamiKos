"""
PREPROCESSING: RAW CSV → CLEAN
================================
Input : data/mamikos_all.csv
Output: data/processed/mamikos_clean.csv
"""

import os, re, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mamikos_all.csv')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed', 'mamikos_clean.csv')

print('=' * 60)
print('  PREPROCESSING')
print('=' * 60)

# ── 1. LOAD ──
df = pd.read_csv(SRC)
n_raw = len(df)
print(f'  Loaded: {n_raw} rows x {len(df.columns)} cols')

# ── 2. PARSE PRICE (string → float) ──
def parse_price(s):
    if pd.isna(s):
        return None
    n = re.findall(r'\d+', str(s).replace('.', '').replace('Rp', '').replace('/bulan', ''))
    return float(n[0]) if n else None

df['price'] = df['harga_real_detail'].apply(parse_price)

# ── 3. CAST DISTANCE COLUMNS TO FLOAT ──
dist_cols = [c for c in df.columns if c.startswith('dist_to_') or c.startswith('jarak_')]
for c in dist_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# ── 4. PARSE SIZE ──
def parse_size(s):
    if pd.isna(s):
        return np.nan, np.nan
    m = re.match(r'([\d.]+)\s*x\s*([\d.]+)', str(s))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)

df[['sw', 'sl']] = df['size'].apply(lambda x: pd.Series(parse_size(x)))
df['size_area'] = df['sw'] * df['sl']
df['pps'] = df['price'] / df['size_area']

# ── 5. NORMALIZE CITY NAMES ──
CITY_MAP = {
    'Kabupaten Badung': 'Badung',
    'Badung Regency': 'Badung',
    'Kota Denpasar': 'Denpasar',
}
df['area_city'] = df['area_city'].replace(CITY_MAP)

# ── 6. NORMALIZE SUBDISTRICT NAMES ──
SUBDISTRICT_MAP = {
    'Kecamatan Kuta Selatan': 'Kuta Selatan',
    'South Kuta': 'Kuta Selatan',
    'Kecamatan Denpasar Selatan': 'Denpasar Selatan',
    'Kecamatan Denpasar Barat': 'Denpasar Barat',
    'Kecamatan Kuta': 'Kuta',
    'Kecamatan Denpasar Timur': 'Denpasar Timur',
    'Kecamatan Denpasar Utara': 'Denpasar Utara',
}
df['area_subdistrict'] = df['area_subdistrict'].replace(SUBDISTRICT_MAP)

# ── 7. CLEAN SUBDISTRICT (tambah alias pendek) ──
df['sub'] = df['area_subdistrict']

# ── 8. MAP GENDER ──
df['gen'] = df['gender'].map({0: 'Campur', 1: 'Putri', 2: 'Putri'})

# ── 9. FACILITY COUNTS ──
bc = [c for c in df.columns if c.startswith('fac_bath_')]
rc = [c for c in df.columns if c.startswith('fac_room_')]
sc = [c for c in df.columns if c.startswith('fac_share_')]

df['fb'] = df[bc].sum(axis=1)
df['fr'] = df[rc].sum(axis=1)
df['fs'] = df[sc].sum(axis=1)
df['ft'] = df['fb'] + df['fr'] + df['fs']

# ── 10. FIRST MONTH (as float — fixes the LossySetitemError) ──
df['first_month'] = df['price'].astype(float)
dp_mask = df['dp_percentage'].notna()
df.loc[dp_mask, 'first_month'] = (
    df.loc[dp_mask, 'price'].astype(float) *
    (1 + df.loc[dp_mask, 'dp_percentage'] / 100)
)

# ── 11. PRICE TIER (quantile-based) & ZONE ──
valid_p = df['price'].dropna()
qt = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
tier_bins = [0] + [valid_p.quantile(q) for q in qt[1:-1]] + [float('inf')]

def fmt_tier(v):
    if v == 0 or v == float('inf'): return v
    s = f'{v/1e6:.1f}'.replace('.', ',')
    return s + 'jt'

tier_lbls = [
    f'<Rp{fmt_tier(tier_bins[1])}',
    f'Rp{fmt_tier(tier_bins[1])}-{fmt_tier(tier_bins[2])}',
    f'Rp{fmt_tier(tier_bins[2])}-{fmt_tier(tier_bins[3])}',
    f'Rp{fmt_tier(tier_bins[3])}-{fmt_tier(tier_bins[4])}',
    f'>Rp{fmt_tier(tier_bins[4])}',
]
df['tier'] = pd.cut(df['price'], bins=tier_bins, labels=tier_lbls)

zone_bins = [0, 1, 2, 3, 5, 10]
zone_lbls = ['<1km', '1-2km', '2-3km', '3-5km', '>5km']
df['zone'] = pd.cut(df['jarak_unud_jimbaran_km'], bins=zone_bins, labels=zone_lbls)

# ── 12. FILTER VALID & SAVE ──
dv = df.dropna(subset=['price']).copy()
print(f'  Valid: {len(dv)} kos')
print(f'  Saving to: {OUT}')

dv.to_csv(OUT, index=False)

print(f'  Columns exported: {len(dv.columns)}')
print(f'  City variants: {dv["area_city"].nunique()}')
print(f'  Subdistrict variants: {dv["area_subdistrict"].nunique()}')
print('  [OK] Preprocessing complete')
