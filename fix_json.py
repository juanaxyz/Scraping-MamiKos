import json

with open('data/raw/mamikos_data_unud_jimbaran.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix index 218
data[218]['fac_bath'] = ['K. Mandi Dalam', 'Kloset Duduk', 'Shower', 'Air panas']

with open('data/raw/mamikos_data_unud_jimbaran.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed fac_bath for Kost Surya 1")