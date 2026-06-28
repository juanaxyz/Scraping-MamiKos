import json
with open('data/raw/mamikos_data_unud_jimbaran.json') as f:
    data = json.load(f)
for i, record in enumerate(data):
    if isinstance(record.get('fac_bath'), dict):
        print(f'Found at index {i}: {record["nama_kost"]}')
        print(record['fac_bath'])
        break