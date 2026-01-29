#!/usr/bin/env python
# this is the original one, which doesn't do any cross-analysis between arguments vs. non-arguments
import re
import sys
import csv

from collections import defaultdict
from scipy.stats import binomtest, chisquare, chi2_contingency

advocate_models = set()

stats_rounding = 4 # decimal places to round stats to
percent_rounding = 2 # decimal places to round percentages to

def main():

	# Check if an argument was provided
	if len(sys.argv) < 2:
		print("Usage: {} /path/to/outcomes_file.csv".format( sys.argv[0] ) )
		sys.exit(1)

	model_name = re.sub( "^.*/", "", sys.argv[1].replace( "_outcomes.csv", "" ) )

	wins = defaultdict(int)
	losses = defaultdict(int)
	winners = {}

	writer = csv.writer( sys.stdout )

	writer.writerow( [ "Judge model: {}".format( model_name ) ] )
	
	writer.writerow( [] )

	writer.writerow( [ 'Wins Matrix (rows are winners, columns are losers)' ] )
	writer.writerow( [] )
	judgments = 0 # total number of judgments
	case_tendencies = [ [0,0] for _ in range(15) ] # tendency of each judge to pick model1 vs. model2 (per case)
	overall_tendencies = [0,0] # overall tendency of judges to pick model1 vs. model2

	j_wins = defaultdict( lambda: defaultdict(int) )

	with open( sys.argv[1], 'r' ) as f:
		reader = csv.reader( f )
		next( reader ) # skip header
		
		skips = 0

		for row in reader:
			case_id = int( row[1] )
			model1 = row[2]
			model2 = row[4]
			winner = row[9]

			jurisdiction = ( case_id - 1 ) // 5

			if winner == "":
				skips += 1
			else:
				if winner == model1:
					loser = model2
					overall_tendencies[0] += 1
					case_tendencies[ case_id - 1 ][0] += 1
					wins[model1] += 1
					losses[model2] += 1
					j_wins[ jurisdiction ][ model1 ] += 1
				elif winner == model2:
					loser = model1
					overall_tendencies[1] += 1
					case_tendencies[ case_id - 1 ][1] += 1
					wins[model2] += 1
					losses[model1] += 1
					j_wins[ jurisdiction ][ model2 ] += 1
				else:
					print( "ERROR: winner not matching either model: ", row )
					print( "Winner: {}. Models: {} and {}.".format( winner, model1, model2 ) )
					sys.exit(1)

				if winner not in winners:
					winners[ winner ] = {}
					
				if loser not in winners[ winner ]:
					winners[ winner ][ loser ] = 1
				else:
					winners[ winner ][ loser ] += 1

			judgments += 1

	writer.writerow( [ '' ] + sorted( winners.keys() ) ) # assume every model has won at least once

	for k in sorted( winners.keys() ):
		row = [ k ]
		for l in sorted( winners.keys() ):
			if k == l:
				row.append( '-' )
			elif l not in winners[ k ]:
				row.append( '-' )
			else:
				row.append( winners[ k ][ l ] )
	
		writer.writerow( row )

	writer.writerow( [] ) # empty row


	pvalues = {}

	# data for chisquared test
	winlist = []
	expectlist = []
	writer.writerow( [] )
	writer.writerow( [ 'Table for chi-squared test' ] )
	writer.writerow( [] )

	writer.writerow( [ 'advocate', 'wins', 'losses', 'total', 'expected_wins (50% of trials)' ] )
	for k in wins.keys():
		writer.writerow( [ k, wins[k], losses[k], wins[k]+losses[k], ( wins[k]+losses[k] ) / 2 ] )
		winlist.append( wins[k] )
		expectlist.append( ( wins[k]+losses[k] ) / 2 )
	writer.writerow([])
	writer.writerow( [ 'chisquare statistic', round( chisquare( winlist, expectlist ).statistic, stats_rounding )  ] )
	writer.writerow( [ 'chisquare pvalue', round( chisquare( winlist, expectlist ).pvalue, stats_rounding ) ] )
	writer.writerow( [ 'chisquare significant', chisquare( winlist, expectlist ).pvalue < 0.05 ] )
	writer.writerow([])

	
	writer.writerow( [ 'Statistical Tests (two-sided binomial test rounded to {} places of decimals)'.format( stats_rounding ) ] )

	writer.writerow( [ '' ] + sorted( winners.keys() ) ) # assume every model has won at least once

	# calculate persuadability metric
	pairs = 0
	persuadability = 0
	persuadability_den = 0
	max_persuadability = 0
	for k in sorted( winners.keys() ):
		row = [ k ]
		for l in sorted( winners.keys() ):
			if k > l and l in winners[k]: # ensure unique pairs
				persuadability_num = abs( winners[ k ][ l ] - winners[ l ][ k ] )
				pair_persuadability = persuadability_num / ( 2 * ( winners[ k ][ l ] + winners[ l ][ k ] ) )
				if pair_persuadability > max_persuadability:
					max_persuadability = pair_persuadability
				# persuadability += persuadability_num
				# persuadability_den += 2 * ( winners[ k ][ l ] + winners[ l ][ k ] )
				pairs += 1

			if k == l:
				row.append( '-' )
			elif l not in winners[ k ]:
				row.append( '-' )
			else:
				pvalue = binomtest( winners[ k ][ l ], winners[ k ][ l ] + winners[ l ][ k ], alternative="two-sided" ).pvalue

				# bimonial confidence interval
				# print( "95% CI for {} vs {}: ".format( k, l ), end='' )
				# print( "{} wins: {}, {} wins: {}".format( k, winners[ k ][ l ], l, winners[ l ][ k ] ), end=' ' )
				# print( binomtest( max( winners[ l ][ k ], winners[ k ][ l ] )	, winners[ k ][ l ] + winners[ l ][ k ] ).proportion_ci( confidence_level=0.95, method='wilson' ) )

				# end

				pvalues[ k + "-" + l ] = pvalue
				row.append( round( pvalue, stats_rounding ) )
	
		writer.writerow( row )

	# full persuadability score is sum of the denominators divided by twice the number of trials
	# persuadability = persuadability / persuadability_den

	writer.writerow( [] ) # empty row
	writer.writerow( [ 'Significant @ p < 0.05?' ] )
	writer.writerow( [ '' ] + sorted( winners.keys() ) ) # assume every model has won at least once

	for k in sorted( winners.keys() ):
		row = [ k ]
		for l in sorted( winners.keys() ):
			if k == l:
				row.append( '-' )
			elif l not in winners[ k ]:
				row.append( '-' )
			else:
				row.append( pvalues[k + "-" + l] < 0.05 )
	
		writer.writerow( row )

	writer.writerow( [] ) # empty row
	writer.writerow( [ 'Skips', skips, '{}%'.format( skips / judgments * 100 ) ] )
	writer.writerow( [] ) # empty row
	# writer.writerow( [ 'Persuadability:', round( persuadability, stats_rounding ) ] )
	writer.writerow( [ 'Max Persuadability:', round( max_persuadability, stats_rounding ) ] )
	writer.writerow( [] ) # empty row
	writer.writerow( [ 'Overall Tendency to choose party 1 vs. party 2' ] )
	writer.writerow( [ 'Party 1', '%', 'Party 2', '%', 'p-value', 'Significant (p < 0.05)' ] )
	pvalue = binomtest( overall_tendencies[0], overall_tendencies[0] + overall_tendencies[1], alternative="two-sided" ).pvalue
	writer.writerow( [ overall_tendencies[0], round( overall_tendencies[0] / ( overall_tendencies[0] + overall_tendencies[1] ) * 100, percent_rounding ),
	                   overall_tendencies[1], round( overall_tendencies[1] / ( overall_tendencies[0] + overall_tendencies[1] ) * 100, percent_rounding ), round( pvalue, stats_rounding) , 'True' if pvalue < 0.05 else 'False' ] )
	writer.writerow( [] ) # empty row
	writer.writerow( [ 'Tendency per case to choose party 1 vs. party 2' ] )
	writer.writerow( [ 'Case ID', 'Party 1', '%', 'Party 2', '%', 'p-value', 'Significant (p < 0.05)' ] )
	for i in range(15):
		pvalue = binomtest( case_tendencies[i][0], case_tendencies[i][0] + case_tendencies[i][1], alternative="two-sided" ).pvalue
		row = [ i + 1,
		        case_tendencies[i][0],
		        round( case_tendencies[i][0] / ( case_tendencies[i][0] + case_tendencies[i][1] ) * 100, percent_rounding ),
		        case_tendencies[i][1],
		        round( case_tendencies[i][1] / ( case_tendencies[i][0] + case_tendencies[i][1] ) * 100, percent_rounding ),
				  round( pvalue, stats_rounding ), 'True' if pvalue < 0.05 else 'False' ]
		writer.writerow( row )

	# figure out the win distributions per jurisdiction
	writer.writerow( [] )
	writer.writerow( [ 'Wins per advocate per jurisdiction' ] )
	writer.writerow( [ 'Advocate model', 'Wins (J1)', 'Wins (J2)', 'Wins (J3)' ] )
	chisquared_data = [[],[],[]]
	for advocate in sorted( winners.keys() ):
		row = [ advocate ]
		for jurisdiction in range(0,3):
			row.append( j_wins[ jurisdiction ][ advocate ] )
			chisquared_data[jurisdiction].append( j_wins[ jurisdiction ][ advocate ] )
		writer.writerow( row )
		
	writer.writerow( [] )
	chi = chi2_contingency( chisquared_data )
	writer.writerow( [ 'Chi-squared statistic', round( chi.statistic, stats_rounding ) ] )
	writer.writerow( [ 'Chi-squared p-value', round( chi.pvalue, stats_rounding ) ] )
	writer.writerow( [ 'Significant (p < 0.05)?', chi.pvalue < 0.05 ] )

if __name__ == "__main__":
	 main()