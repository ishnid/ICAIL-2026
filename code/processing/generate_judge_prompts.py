#!/usr/bin/env python

import os
import csv
import sys

from pprint import pprint
path = '.'

import persuasion_utils as util

use_arguments = False

scenarios_path = os.path.join( path, 'scenarios.csv' )


def process_advocate_arguments( dirname ):

	ret = {}

	for filename in os.listdir( dirname ):
		if filename.endswith( ".csv" ):
			# print( "Processing file: ", filename )

			model = filename.rsplit( ".", 1 )[0]

			with open( os.path.join( dirname, filename ), 'r' ) as f:
				reader = csv.reader(f)

				next(reader) # skip header

				# CSV contents: caseid, parrtyid, argumentid, model, argument
				for row in reader:
					
					case_id = int( row[0] )
					party_id = int( row[1] )
					argument_id = int( row[2] )
					# model = row[3]
					argument = row[4]

					if case_id not in ret:
						ret[ case_id ] = {}
					if model not in ret[ case_id ]:
						ret[ case_id ][ model ] = [[],[]]

					ret[ case_id ][ model ][ int(party_id)-1 ].append( argument ) 
					
	return ret



def generate_judge_prompt( struct, argstring ):

	scenarios = util.load_scenarios(scenarios_path)

	( case_id, model1, arg1, model2, arg2 ) = argstring.split("_")
	courts = ["a US court", "an English court", "an Irish court"]
	court_string = courts[ ( int(case_id)  - 1 ) // 5 ]

	model1 = model1 + ( "_arguments" if use_arguments else "_noarguments" )
	model2 = model2 + ( "_arguments" if use_arguments else "_noarguments" )

	case_id = int( case_id )
	arg1 = int( arg1 ) - 1
	arg2 = int( arg2 ) - 1

	facts = scenarios[ case_id ]['facts']
	legal_issue = scenarios[ case_id ]['legal_issue']
	party_1 = scenarios[ case_id ]['party_1']
	party_2 = scenarios[ case_id ]['party_2']
	party_1_arguments = struct[ case_id ][ model1 ][ 0 ][ arg1 ]
	party_2_arguments = struct[ case_id ][ model2 ][ 1 ][ arg2 ]
	
	return util.judgment_prompt( court_string, facts, legal_issue, party_1_arguments, party_2_arguments, party_1, party_2 )



if __name__ == "__main__":
	struct = process_advocate_arguments( os.path.join( path, 'data', 'advocate_outputs' ) )

	with open( os.path.join( path, 'data', 'judgment_600.txt' ), 'r' ) as f:
		lines = f.readlines()

		writer = csv.writer( sys.stdout )

		counter = 1
		for line in lines:
			argstring = line.strip()
			writer.writerow( [ counter, argstring, generate_judge_prompt( struct, argstring ) ] )
			counter += 1

	