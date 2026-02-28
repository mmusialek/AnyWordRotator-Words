import csv
import os
import sys

def remove_duplicates(input_file: str, output_file: str):
    """
    Reads a CSV file with ';' delimiter and removes duplicates based on the first column.
    Handles empty rows and ensures UTF-8 encoding for reliable Polish character support.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return

    seen: set[str] = set()
    rows_to_keep: list[list[str]] = []
    # Using a list to track duplicates to avoid += increment 
    # and satisfy experimental type checkers like Red Knot/Pyre2
    duplicates_found: list[str] = []
    
    try:
        # Use encoding='utf-8' to handle Polish characters correctly
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile, delimiter=";")
            
            # Read first row as header
            header = next(reader, None)
            if header is None:
                return # Empty file
            
            rows_to_keep.append(header)
            # Keep track of the first column header so it doesn't get treated as data later
            if header:
                seen.add(header[0].strip().lower())
            
            for row in reader:
                # 1. SKIP EMPTY ROWS to prevent IndexError
                if not row:
                    continue
                
                # 2. Key comparison (stripped for safety)
                key = row[0].strip()
                
                if key not in seen:
                    rows_to_keep.append(row)
                    seen.add(key)
                else:
                    duplicates_found.append(key)
        
        # Write unique rows to output
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter=";")
            writer.writerows(rows_to_keep)
        
        print(f"Successfully removed {len(duplicates_found)} duplicates.")
        print(f"Unique lines have been written to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Better path construction
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    input_path = os.path.join(repo_root, "src/en_pl/test_0001.csv")
    output_path = os.path.join(repo_root, "src/en_pl/test_0001_unique.csv")
    
    remove_duplicates(input_path, output_path)
