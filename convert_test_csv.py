#!/usr/bin/env python3
"""
Convert test.csv to a format that can be used as mock data in the frontend.
"""
import csv
import json
import sys
import os

def convert_csv_to_mock_data(csv_file_path, output_file_path):
    """
    Convert a CSV file to a JSON file that can be used as mock data.
    """
    # Read the CSV file
    data = []
    headers = []
    
    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Get the headers
        
        for i, row in enumerate(reader):
            if i >= 1000:  # Limit to 1000 rows
                break
                
            # Convert values to numbers where possible
            row_data = {}
            for j, value in enumerate(row):
                try:
                    # Try to convert to float
                    if value.lower() == 'nan':
                        row_data[headers[j]] = None
                    else:
                        row_data[headers[j]] = float(value)
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    row_data[headers[j]] = value
            
            # Add index
            row_data['index'] = i
            
            data.append(row_data)
    
    # Create the mock data structure
    mock_data = {
        "data": data,
        "columns": ["index"] + headers
    }
    
    # Write to JSON file
    with open(output_file_path, 'w') as f:
        json.dump(mock_data, f, indent=2)
    
    print(f"Converted {len(data)} rows from {csv_file_path} to {output_file_path}")
    
    # Print a sample of the data that can be used in the frontend code
    print("\nSample data for frontend mockData.js:")
    print("const sampleData = [")
    for i, row in enumerate(data[:5]):
        print(f"  {json.dumps(row)},")
    print("  // ... more data")
    print("];")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_test_csv.py <csv_file_path> [output_file_path]")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    output_file_path = sys.argv[2] if len(sys.argv) > 2 else "mock_data.json"
    
    convert_csv_to_mock_data(csv_file_path, output_file_path)
