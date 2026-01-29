#!/usr/bin/env python

import csv
import sys
from collections import defaultdict
import persuasion_utils as util

advocates = [
	'gpt-4o_arguments',
	'gpt-4o_noarguments',
	'gpt-5.1_arguments',
	'gpt-5.1_noarguments'
]

scenarios_path = '../data/scenarios.csv'

def generate_judge_prompt( argstring, arguments ):

	scenarios = util.load_scenarios(scenarios_path)

	( case_id, model1, arg1, model2, arg2 ) = argstring.split("_")

	courts = ["a US court", "an English court", "an Irish court"]
	court_string = courts[ ( int(case_id)  - 1 ) // 5 ]

	case_id = int( case_id )
	arg1 = int( arg1 )
	arg2 = int( arg2 )

	facts = scenarios[ case_id ]['facts']
	legal_issue = scenarios[ case_id ]['legal_issue']
	party_1 = scenarios[ case_id ]['party_1']
	party_2 = scenarios[ case_id ]['party_2']
	party_1_arguments = arguments[ model1 ][ '_'.join( [ str(_) for _ in ( case_id, 1, arg1 ) ] ) ]
	party_2_arguments = arguments[ model2 ][ '_'.join( [ str(_) for _ in ( case_id, 2, arg2 ) ] ) ]
	
	return util.judgment_prompt( court_string, facts, legal_issue, party_1_arguments, party_2_arguments, party_1, party_2 )

def main():

	# read the 200 scenarios
	combinations = []
	with open( '../data/judgment_arguments_200.txt', 'r' ) as f:
		for line in f:
			# create a list: caseid, advocate1, argumentid1, advocate2, argumentid2
			combinations.append( line.strip().split( '_' ) )

	arguments = defaultdict(lambda: {})

	# get all the arguments 
	for a in advocates:
		with open( '../data/advocate_outputs/{}.csv'.format( a ), 'r' ) as f:
			next(f) # skip header
			r = csv.reader(f)
			for row in r:
				# creates a string: caseid_partyid_argumentid -> argument text
				arguments[ a.replace( '_', '-' ) ][ '_'.join( row[:3] ) ] = row[ 4 ]
	
	writer = csv.writer( sys.stdout )

	counter = 0
	for c in combinations:
		argstring = '_'.join( c )		
		writer.writerow( [ counter, argstring, generate_judge_prompt( argstring, arguments ) ] )
		counter += 1

if __name__ == "__main__":
	main()