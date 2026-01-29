#!/usr/bin/env python
import sys
import csv
from collections import defaultdict
from scipy.stats import binomtest, chisquare, chi2_contingency

thinking = { 
	'claude-haiku-4-5-20251001_8k-thinking' : 'claude-haiku-4-5-20251001_nothinking',
	'claude-sonnet-4-5-20250929_8k-thinking' : 'claude-sonnet-4-5-20250929_1k-thinking',
	'deepseek-reasoner_defaults' : 'deepseek-chat_defaults',
	'gemini-2.5-flash-lite_reasoning' : 'gemini-2.5-flash-lite_nonreasoning',
	'gemini-3-pro-preview_8k-thinking' : 'gemini-3-pro-preview_1k-thinking',
	'gpt-5-nano_medium-reasoning' : 'gpt-5-nano_minimal-reasoning',
	'gpt-5.1_medium-reasoning' : 'gpt-5.1_low-reasoning',
	'mistralai/Magistral-Small-2506_defaults' : 'mistralai/Mistral-Small-3.2-24B-Instruct-2506_defaults',
	'Qwen/Qwen3-32B_thinking' : 'Qwen/Qwen3-32B_nothinking',
	'QWen/Qwen3-8B_thinking' : 'QWen/Qwen3-8B_nothinking',
	'claude-haiku-4-5-20251001_8k-thinking_noarguments' : 'claude-haiku-4-5-20251001_nothinking_noarguments',
	'claude-sonnet-4-5-20250929_8k-thinking_noarguments' : 'claude-sonnet-4-5-20250929_1k-thinking_noarguments',
	'deepseek-reasoner_defaults_noarguments' : 'deepseek-chat_defaults_noarguments',
	'gemini-2.5-flash-lite_reasoning_noarguments' : 'gemini-2.5-flash-lite_nonreasoning_noarguments',
	'gemini-3-pro-preview_8k-thinking_noarguments' : 'gemini-3-pro-preview_1k-thinking_noarguments',
	'gpt-5-nano_medium-reasoning_noarguments' : 'gpt-5-nano_minimal-reasoning_noarguments',
	'gpt-5.1_medium-reasoning_noarguments' : 'gpt-5.1_low-reasoning_noarguments',
	'mistralai/Magistral-Small-2506_defaults_noarguments' : 'mistralai/Mistral-Small-3.2-24B-Instruct-2506_defaults_noarguments',
	'Qwen/Qwen3-32B_thinking_noarguments' : 'Qwen/Qwen3-32B_nothinking_noarguments',
	'QWen/Qwen3-8B_thinking_noarguments' : 'QWen/Qwen3-8B_nothinking_noarguments',
}

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

	advocates = 	['claude-sonnet-4.5', 'gpt-4o', 'gemini-3-pro-preview', 'gpt-5.1']

	# record wins and losses per judge model
	wins = defaultdict( lambda: defaultdict(lambda: defaultdict(int)) )
	losses = defaultdict( lambda: defaultdict(lambda: defaultdict(int)) )

	# record wins and losses per jurisdiction per model
	j_wins_total = defaultdict(  lambda: defaultdict(lambda: defaultdict(int)) )
	# j_losses = defaultdict( lambda: defaultdict( lambda: defaultdict(lambda: defaultdict(int)) ) )

	j_wins_pairwise = defaultdict( lambda: defaultdict(lambda: defaultdict( lambda: defaultdict(int) ) ) )

	pps = defaultdict(float) # record population persuadability for all judge models

	case_tendencies = defaultdict( lambda: defaultdict( lambda: [0,0]) ) 

	judges = []
	# read data and count things
	with open( '../data/all_outcomes.csv' ) as f:
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
				j_wins_total[ judge_model ][ jurisdiction ][ party1_model ] += 1
				j_wins_pairwise[ judge_model ][ jurisdiction ][ party1_model ][ party2_model ] += 1
				#j_losses[ judge_model ][ jurisdiction ][ party2_model ][ party1_model ] += 1
				case_tendencies[judge_model][ case_id ][0] += 1
			elif ( winner == party2_model ):
				wins[ judge_model ][ party2_model ][ party1_model ] += 1
				losses[ judge_model ][ party1_model ][ party2_model ] += 1
				j_wins_total[ judge_model ][ jurisdiction ][ party2_model ] += 1
				j_wins_pairwise[ judge_model ][ jurisdiction ][ party2_model ][ party1_model ] += 1
				# j_losses[ judge_model ][ jurisdiction ][ party1_model ][ party2_model ] += 1
				case_tendencies[judge_model][ case_id ][1] += 1

	with open( 'stats/judge_model_stats.csv', 'w' ) as out_f:
		writer = csv.writer( out_f )

		header = [ 'Judge model', 'Max persuadability', 'Max CI low', 'Max CI high', 'Population persuadability', 'Chi-2 p-value', 'Significant',
					'claude-gpt4o per', 'claude-gpt4o CI low', 'claude-gpt4o CI high',
					'claude-gemini per', 'claude-gemini CI low', 'claude-gemini CI high',
					'claude-gpt5.1 per', 'claude-gpt5.1 CI low', 'claude-gpt5.1 CI high',
					'gpt4o-gemini per', 'gpt4o-gemini CI low', 'gpt4o-gemini CI high',
					'gpt4o-gpt5.1 per', 'gpt4o-gpt5.1 CI low', 'gpt4o-gpt5.1 CI high',
					'gemini-gpt5.1 per', 'gemini-gpt5.1 CI low', 'gemini-gpt5.1 CI high',
					'Proportion of biased cases', 'Proportion of biased cases favouring Party 1', 'Chi-2 jurisdictions', 'Significant jurisdictions', 'J0 pop', 'J1 pop', 'J2 pop' ]
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
			jurisdiction_population_persuadability = [0,0,0]

			for jurisdiction in range(0,3):
				# win distribution for this jurisdiction
				dist = []

				# denominator variable for the population persuadability calculation for this jurisdiction
				pop_dist_denom = 0

				
				for i in range( 0, len( advocates ) ):
					# add total wins for this model to the distributions for the chi2 test
					dist.append( j_wins_total[ judge ][ jurisdiction ][ advocates[i] ] )

					# pairwise stats for population persuadability
					for j in range( i+1, len( advocates ) ):
						print( 'j{}-{}-{}-{}: {} vs {}'.format( judge, jurisdiction, advocates[i], advocates[j], j_wins_pairwise[judge][ jurisdiction ][ advocates[i] ][ advocates[j] ], j_wins_pairwise[judge][ jurisdiction ][ advocates[j] ][ advocates[i] ] ) )
						jurisdiction_population_persuadability[jurisdiction] += abs( j_wins_pairwise[judge][ jurisdiction ][ advocates[i] ][ advocates[j] ] - j_wins_pairwise[judge][ jurisdiction ][ advocates[j] ][ advocates[i] ] )
						pop_dist_denom += 2 * (j_wins_pairwise[judge][ jurisdiction ][ advocates[i] ][ advocates[j] ] + j_wins_pairwise[judge][ jurisdiction ][ advocates[j] ][ advocates[i]])
				jurisdiction_population_persuadability[jurisdiction] /= pop_dist_denom

	
				jurisdiction_distributions.append( dist )


				# population persuadability by jurisdiction


			chi = chi2_contingency( jurisdiction_distributions )

			outputs += [ '%.4f' % chi.pvalue, bool( chi.pvalue < 0.05 ) ]

			writer.writerow( outputs + [ '%.4f' % p for p in jurisdiction_population_persuadability ] )
		
	
	

	with open( 'stats/argument_vs_noargument_stats.csv', 'w' ) as out_f:
		writer = csv.writer( out_f )

		header = [ 'Argument judge', 'Noargument judge', 'Argument population persuadability', 'Noargument population persuadability', 'Chi-2 p-value', 'Significant' ]
		writer.writerow( header )

		# generate argument/noargument pairs
		for judge in judges:
		
			if not judge.endswith( '_noarguments' ):
				argument_judge = judge
				noargument_judge = judge + '_noarguments'

				argument_distribution = get_win_distribution( wins[ argument_judge ] )
				noargument_distribution = get_win_distribution( wins[ noargument_judge ] )
			
				chi = chi2_contingency( [ argument_distribution, noargument_distribution ] )

				outputs = [ argument_judge, noargument_judge, pps[argument_judge], pps[ noargument_judge], chi.pvalue, bool( chi.pvalue < 0.05 ) ]	

				writer.writerow( outputs )

	
	with open( 'stats/thinking_vs_nothinking_stats.csv', 'w' ) as out_f:
		writer = csv.writer( out_f )

		header = [ 'Thinking judge', 'Nothinking judge', 'Thinking population persuadability', 'Nothinking population persuadability', 'Chi-2 p-value', 'Significant' ]
		writer.writerow( header )

		# generate thinking/nothinking pairs
		for judge in judges:
			if judge in thinking.keys():
				think_judge = judge
				nothink_judge = thinking[judge]

				think_distribution = get_win_distribution( wins[ think_judge ] )
				nothink_distribution = get_win_distribution( wins[ nothink_judge ] )
				
				chi = chi2_contingency( [ think_distribution, nothink_distribution ] )

				outputs = [ think_judge, nothink_judge, pps[think_judge], pps[ nothink_judge], chi.pvalue, bool( chi.pvalue < 0.05 ) ]	

				writer.writerow( outputs )
		