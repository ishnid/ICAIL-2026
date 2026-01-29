#!/usr/bin/env python
import re
import sys
import csv
import ast


judgment = True # True for judgment file, False for advocate files

csv. field_size_limit(100000000)

output_column = 3 if judgment else 4 # 4th col for the judge outputs, 5th col for the advocate outputs

def extract(raw_text):
    match = re.search(r"content=['\"](.*?)['\"] additional_kwargs=", raw_text, re.DOTALL)
    if match is not None:
        return match.group(1)
    else: # probably from thinking mode - different regext
        match = re.search(r"'text': ['\"](.*?)['\"], 'type': 'text'}", raw_text, re.DOTALL)
        return match.group(1)

def load_and_parse_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        writer = csv.writer(sys.stdout)


        if not judgment:
            header = next(reader)

            # Add the new column name
            output_header = header

            writer.writerow(output_header)

        # Process rows
        for row in reader:
            raw = row[output_column]                      # 5th column
            # parsed = ast.literal_eval(raw)    # safe parse


            parsed = extract(raw).replace( "\\n", "\n" )
            
            # Append parsed object as a string
            row[output_column] = parsed
            writer.writerow(row)

if __name__ == "__main__":
    # Check if an argument was provided
    if len(sys.argv) < 2:
        print("Usage: {} /path/to/judgment_file.csv".format( sys.argv[0] ) )
        sys.exit(1)

    load_and_parse_csv(sys.argv[1])