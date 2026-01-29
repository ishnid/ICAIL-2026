#!/usr/bin/env python

import csv
import sys
import os
import re

import persuasion_utils as util

base_path = '..'

debug = True

csv. field_size_limit(100000000)

def main():
    # Check if an argument was provided
    if len(sys.argv) < 2:
        print("Usage: {} /path/to/judgment_file.csv".format( sys.argv[0] ) )
        sys.exit(1)

    writer = csv.writer( sys.stdout )
    writer.writerow( [ 'judgment_id', 'case_id', 'party1_model', 'party1_variation', 'party2_model', 'party2_variation', 'party_1', 'party_2', 'judge_model_string', 'winner', 'manual_check_required' ] )

    # Read the first command-line argument
    judgment_file = sys.argv[1]
    
    scenarios = util.load_scenarios( os.path.join( base_path, 'data', 'scenarios.csv' ) )

    judgments = util.load_judgments( judgment_file )

    for j in judgments:
        
        chosen = j['chosen_party']
        (party1, party2) = scenarios[ j['case_id' ] ]['party_1'].strip(), scenarios[ j['case_id' ] ]['party_2'].strip()

        # mistral sometimes underlines the answer with ``` on the line below
        chosen = re.sub( "```$", "", chosen.strip() )

        # print( party1 + " " + party2 )
        chosen = chosen.replace( "**", "" ).strip() # Claude wraps last line in **
        chosen = chosen.replace( "- ", "" )
        
        chosen = re.sub( "^(?:The )?(?:Final|End) (?:answer )?line(?: \\((?:as requested|required|separate|per instructions)\\))?: ", "", chosen, flags=re.IGNORECASE ).strip() # many lines from GPT start this way
        if ':' in chosen:
            chosen = chosen.rsplit( ":", 1 )[ -1 ].strip() # sometimes there's a preceding label
        if '?' in chosen:
            chosen = chosen.rsplit( "?", 1 )[ -1 ].strip() # sometimes there's a preceding label
        chosen = re.sub( "^\"", "", chosen )
        chosen = re.sub( "\"$", "", chosen )
        
        chosen = re.sub( " should prevail\\.?$", "", chosen )    
        
        chosen = re.sub( "(?<!Corp)\\.$", "", chosen ) # remove trailing dot except in "Corp." (which is in an actual party name)
        
        if chosen.lower() == party1.lower(): #some have different casing
            winner = j['party1_model']
            manual = ''
        elif chosen.lower() == party2.lower():
            winner = j['party2_model']
            manual = ''
        else:
            if debug:
                print( f"MANUAL CHECK REQUIRED: judgment_id {j['judgment_id']} chosen party '{chosen}' does not match either party '{party1}' or '{party2}'" , file=sys.stderr )
            winner = ""
            manual = "MANUAL_CHECK REQUIRED"
                
        writer.writerow( [ j['judgment_id'], j['case_id'], j['party1_model'], j['party1_variation'], j['party2_model'], j['party2_variation'], party1, party2, j['judge_model_string'], winner, manual ] )

if __name__ == "__main__":
    main()
