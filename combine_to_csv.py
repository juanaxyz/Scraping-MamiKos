import json
import csv
import os
from pathlib import Path

def get_all_facilities(data_list, facility_keys):
    """Collect all unique facilities across all records."""
    all_facilities = {key: set() for key in facility_keys}
    for record in data_list:
        for key in facility_keys:
            if key in record and record[key]:
                all_facilities[key].update(record[key])
    return {key: sorted(val) for key, val in all_facilities.items()}

def one_hot_encode(record, all_facilities, facility_keys):
    """Add one-hot encoded columns for facilities."""
    result = {}
    for key in facility_keys:
        facilities = record.get(key, []) or []
        for facility in all_facilities[key]:
            col_name = f"{key}_{facility}"
            result[col_name] = 1 if facility in facilities else 0
    return result

def combine_json_to_csv():
    facility_keys = ['fac_room', 'fac_share', 'fac_bath', 'top_facilities', 'booking_type']
    
    # Load all data first
    all_records = []
    files = [
        ('data/raw/mamikos_data_unud_jimbaran.json', 'jimbaran'),
        ('data/raw/mamikos_data_unud_sudirman.json', 'sudirman')
    ]
    
    for filepath, source in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for record in data:
            record['source_file'] = source
            all_records.append(record)
    
    # Get all unique facilities
    all_facilities = get_all_facilities(all_records, facility_keys)
    
    # Build final records with one-hot encoding
    final_records = []
    base_fields = set()
    
    for record in all_records:
        # Copy non-facility fields
        flat_record = {k: v for k, v in record.items() if k not in facility_keys}
        
        # Add one-hot encoded facilities
        ohe = one_hot_encode(record, all_facilities, facility_keys)
        flat_record.update(ohe)
        
        final_records.append(flat_record)
        base_fields.update(flat_record.keys())
    
    # Ensure consistent ordering: source_file first, then base fields, then facility columns
    fieldnames = sorted(base_fields)
    if 'source_file' in fieldnames:
        fieldnames.remove('source_file')
        fieldnames = ['source_file'] + fieldnames
    
    # Output
    output_path = 'data/mamikos_all.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_records)
    
    print(f"Combined {len(final_records)} records into {output_path}")
    print(f"Columns: {len(fieldnames)}")
    for key in facility_keys:
        print(f"  {key}: {len(all_facilities[key])} unique facilities")

if __name__ == '__main__':
    combine_json_to_csv()