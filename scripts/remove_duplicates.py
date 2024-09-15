import csv
import os

def remove_duplicates(input_file, output_file):
    seen = set()
    with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile, delimiter=";")
        writer = csv.writer(outfile, delimiter=";")
        for row in reader:
            if row[0] not in seen:
                writer.writerow(row)
                seen.add(row[0])

if __name__ == "__main__":
    
    current_file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(current_file_path))

    input_path = os.path.join(parent_dir, "src\\en_pl\\test_0001.csv")
    output_path = os.path.join(parent_dir, "src\\en_pl\\test_0001_unique.csv")
    remove_duplicates(input_path, output_path)
    print(f"Unique lines have been written to {output_path}")
