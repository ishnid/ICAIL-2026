#!/usr/bin/env python
import re
import sys
import csv
import re

judgment = True # True for judgment file, False for advocate files

csv. field_size_limit(100000000)

output_column = 3 if judgment else 4 # 4th col for the judge outputs, 5th col for the advocate outputs

def extract_completion_texts_simple(raw_text):
    """
    Extract 'text' fields from CompletionOutput objects in a raw text dump.
    Returns a list of strings exactly as they appear in the text, without quotes or brackets.
    """
    # Regex matches text='...' or text="...", captures inner content
    pattern = r'text=(["\'])(.*?)(?<!\\)\1'
    
    matches = re.findall(pattern, raw_text, re.DOTALL)
    
    # Return just the captured text
    completion_texts = [txt for _, txt in matches]
    
    # return completion_texts[0].split("</think>\\n\\n", 1)[-1].strip() if "</think>" in completion_texts[0] else completion_texts[0]

    
    return re.sub( "</?think>", " ", completion_texts[0] )

def load_and_parse_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        writer = csv.writer(sys.stdout)
        
        if not judgment:
            header = next(reader)

            # Add the new column name
            output_header = header

            # Write header to stdout        
            writer.writerow(output_header)

        # Process rows
        for row in reader:
            raw = row[output_column]
            
            parsed = extract_completion_texts_simple(raw)

            parsed = parsed.replace( "\\n", "\n" )

            # Append parsed object as a string
            row[output_column] = parsed

            writer.writerow(row)


if __name__ == "__main__":
    # Check if an argument was provided
    if len(sys.argv) < 2:
        print("Usage: {} /path/to/judgment_file.csv".format( sys.argv[0] ) )
        sys.exit(1)

    load_and_parse_csv(sys.argv[1])
