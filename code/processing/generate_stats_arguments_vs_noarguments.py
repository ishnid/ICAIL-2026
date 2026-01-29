#!/usr/bin/env python

import csv
from collections import defaultdict
from scipy.stats import binomtest, chisquare, chi2_contingency


def get_win_distribution( win_dict ):
	distribution = []
	for i in range( 0, len( advocates ) ):
		wins = 0
		for j in range( 0, len( advocates ) ):
			if i != j:
				wins += win_dict[ advocates[i] ][ advocates[j] ]
		distribution.append( wins )
	return distribution

def get_expected_distribution( win_dict ):
	distribution = []
	for i in range( 0, len( advocates ) ):
		trials = 0
		for j in range( 0, len( advocates ) ):
			if i != j:
				trials += win_dict[ advocates[i] ][ advocates[j] ] + win_dict[ advocates[j] ][ advocates[i] ]
		distribution.append( trials / 2 ) # expect to win half the trials
	return distribution

def get_persuadability_stats( win_dict ):
	( max_p, pop_p, p_count, max_ci_low, max_ci_high ) = (0,0,0,0,0)

	intervals = []

	for i in range( 0, len( advocates ) - 1):
		
		for j in range( i + 1, len( advocates ) ):

			if advocates[j] in win_dict[ advocates[i] ]:

				p = abs( win_dict[ advocates[i] ][ advocates[j] ] - win_dict[ advocates[j] ][ advocates[i] ] ) / ( 2 * ( win_dict[ advocates[i] ][ advocates[j] ] + win_dict[ advocates[j] ][ advocates[i] ] ) )

				binom = binomtest( max( win_dict[ advocates[i] ][ advocates[j] ], win_dict[ advocates[j] ][ advocates[i] ] ), win_dict[ advocates[i] ][ advocates[j] ] + win_dict[ advocates[j] ][ advocates[i] ] )
				ci = binom.proportion_ci()
				ci_low = ci.low - 0.5 # TODO: need to discuss whether to add max(ci.low - 0.5, 0) or not
				ci_high = ci.high - 0.5

				intervals += [ p, ci_low, ci_high ]

				if p > max_p:
					max_p = p
					max_ci_low = ci_low
					max_ci_high = ci_high	

			
				
			pop_p += abs( win_dict[ advocates[i] ][ advocates[j] ] - win_dict[ advocates[j] ][ advocates[i] ] )
			p_count += 2 * ( win_dict[ advocates[i] ][ advocates[j] ] + win_dict[ advocates[j] ][ advocates[i] ] )
			
	actual_wins = get_win_distribution( wins[ judge ] )
	expected_wins = get_expected_distribution( wins[ judge ] )

	chi = chisquare( actual_wins, expected_wins )

	return [max_p, max_ci_low, max_ci_high, pop_p / p_count, chi.pvalue, bool( chi.pvalue < 0.05 )] + intervals

if __name__ == "__main__":

	advocates = 	[ 'gpt-5.1-arguments', 'gpt-5.1-noarguments', 'gpt-4o-arguments', 'gpt-4o-noarguments' ]

	# record wins and losses per judge model
	wins = defaultdict( lambda: defaultdict(lambda: defaultdict(int)) )
	losses = defaultdict( lambda: defaultdict(lambda: defaultdict(int)) )

	# record wins and losses per jurisdiction per model
	j_wins = defaultdict(  lambda: defaultdict(lambda: defaultdict(int)) )
	# j_losses = defaultdict( lambda: defaultdict( lambda: defaultdict(lambda: defaultdict(int)) ) )

	pps = defaultdict(float) # record population persuadability for all judge models

	case_tendencies = defaultdict( lambda: defaultdict( lambda: [0,0]) ) 

	judges = []
	# read data and count things
	with open( '../data/all_outcomes_arguments_vs_noarguments.csv' ) as f:
		reader = csv.reader( f )

		for row in reader:
			( judgment_id, case_id, party1_model, party1_variation, party2_model, party2_variation, party_1, party_2, judge_model, winner ) = row[:10]
			
			if winner != "" and winner not in advocates:
				print( f"Unknown winner model: {winner}" )
				exit(1)

			jurisdiction = ( int( case_id)  - 1 ) // 5

			if judge_model not in judges:
				judges.append( judge_model )

			if ( winner == party1_model ):
				wins[ judge_model ][ party1_model ][ party2_model ] += 1
				losses[ judge_model ][ party2_model ][party1_model ] += 1
				j_wins[ judge_model ][ jurisdiction ][ party1_model ] += 1
				#j_losses[ judge_model ][ jurisdiction ][ party2_model ][ party1_model ] += 1
				case_tendencies[judge_model][ case_id ][0] += 1
			elif ( winner == party2_model ):
				wins[ judge_model ][ party2_model ][ party1_model ] += 1
				losses[ judge_model ][ party1_model ][ party2_model ] += 1
				j_wins[ judge_model ][ jurisdiction ][ party2_model ] += 1
				#j_losses[ judge_model ][ jurisdiction ][ party1_model ][ party2_model ] += 1
				case_tendencies[judge_model][ case_id ][1] += 1

	with open( 'stats/judge_model_stats_arguments_vs_noarguments.csv', 'w' ) as out_f:
		writer = csv.writer( out_f )

		header = [ 'Judge model', 'Max persuadability', 'Max CI low', 'Max CI high', 'Population persuadability', 'Chi-2 p-value', 'Significant',
					'gpt-5.1 per', 'gpt-5.1 CI low', 'gpt-5.1 CI high',
					'gpt-4o per', 'gpt-4o CI low', 'gpt-4o CI high',
					'Proportion of biased cases', 'Proportion of biased cases favouring Party 1', 'Chi-2 jurisdictions', 'Significant jurisdictions' ]
		writer.writerow( header )

		for judge in judges:
			outputs = [ judge ]

			stats =  get_persuadability_stats( wins[ judge ] )

			# ( max_persuadabilty, ci_low, ci_high, pop_persuadabilty, chi_p, chi_sig, ci_low0, ci_high0, ci_low1, ci_high1, ci_low2, ci_high2 ) = get_persuadability_stats( wins[ judge ] )
			

			#outputs = outputs + [ '%.4f' % v for v in ( max_persuadabilty, ci_low, ci_high , pop_persuadabilty, chi_p ) ] + [ chi_sig ]
			pps[ judge ] = '%.4f' % stats[3]
			for i in range(0,len(stats)):
				if isinstance( stats[i], float ):
					stats[i] = '%.4f' % stats[i]
				
			outputs = outputs + stats

			# work out the case tendencies. Count how many have a significant bias and what proportion of those are Party 1

			( biases, party1_bias_rate ) = (0,0)

			for case_id in case_tendencies[ judge ].keys():
				counts = case_tendencies[ judge ][ case_id ]
				binom = binomtest( max( counts ), sum( counts ) )
				if binom.pvalue < 0.05:
					biases += 1
					if counts[0] > counts[1]:
						party1_bias_rate += 1
			party1_bias_rate = party1_bias_rate / biases if biases > 0 else 0

			outputs += [ '%.4f' % ( biases / 15 ), '%.4f' % party1_bias_rate ]

			# figure out if the jurisdictions distributions are significantly different
			jurisdiction_distributions = []
			for jurisdiction in range(0,3):
				dist = []
				for advocate in advocates:
					dist.append( j_wins[ judge ][ jurisdiction ][ advocate ] )
				jurisdiction_distributions.append( dist )

			chi = chi2_contingency( jurisdiction_distributions )

			outputs += [ '%.4f' % chi.pvalue, bool( chi.pvalue < 0.05 ) ]

			writer.writerow( outputs )
		