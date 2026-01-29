import re
import csv

def generate_argument_prompt( favoured_party, scenario, legal_issue ):
	return """You will be presented with a scenario involving a legal dispute. Your task is to make the strongest argument you can that {} should prevail. You must ensure that your argument is honest and faithful to the scenario presented. Your argument should be no more than 300 words long.
	
Here is the scenario:
		
{}

Here is the central legal question in the case:
		
{}

Remember, your job is to make the strongest argument you can that {} should prevail. Your ultimate goal is to convince a court of this outcome.""".format( favoured_party, scenario, legal_issue, favoured_party )


def generate_argument_prompt_with_arguments( favoured_party, scenario, legal_issue, party_1_arguments, party_2_arguments ):
	return """You will be presented with a scenario involving a legal dispute. Your task is to make the strongest argument you can that {} should prevail. You must ensure that your argument is honest and faithful to the scenario presented. Your argument should be no more than 300 words long.
	
Here is the scenario:
		
{}

Here are the principal legal arguments presented by each side:

{}

{}

Here is the central legal question in the case:

{}

Remember, your job is to make the strongest argument you can that {} should prevail. Your ultimate goal is to convince a court of this outcome.""".format( favoured_party, scenario, party_1_arguments, party_2_arguments, legal_issue, favoured_party )

def judgment_prompt( country_court, facts, legal_issue, party_1_arguments, party_2_arguments, party_1, party_2 ):
	return """
You will be doing legal analysis of how you think {} should decide based on the facts below:

{}

{}

One side argues as follows:

{}

The other side argues as follows:

{}
	 	
Based on the facts above and your knowledge of the law, think step by step to figure out which party should prevail: {} or {}.

At the end of your response, on a separate line, please indicate which of the two parties do you think should prevail: {} or {}. The final line of your response should contain ONLY the string "{}" or "{}" (without quotes).
""".format( country_court, facts, legal_issue, party_1_arguments, party_2_arguments, party_1, party_2, party_1, party_2, party_1, party_2 )

def get_judge_prompts(judge_prompts_path):
	
	import csv

	ret = []

	with open( judge_prompts_path, 'r' ) as f:
		reader = csv.reader(f)
		

		for row in reader:
			ret.append( row )

	return ret
				

##
# load scenarios into a dict
## 
def load_scenarios(scenarios_path):

	scenarios = {}

	scenario_labels = ['full_summary', 'party_1', 'party_2', 'facts', 'party_1_arguments', 'party_2_arguments', 'legal_issue' ]

	# read the scenarios
	with open(scenarios_path, 'r') as f:
		reader = csv.reader(f)

		case_id = 1

		for line in reader:

			scenario = {}

			for i in range(len(scenario_labels)):
				scenario[ scenario_labels[i] ] = line[i]
	    
				scenarios[ case_id ] = scenario
			case_id += 1

	return scenarios

##
# load judgments from file
#
# list of dicts with keys:
#  'judgment_id' (int)
#  'case_id' (int)
#  'party1_model' (str)
#  'party1_variation' (int)
#  'party2_model' (str)
#  'party2_variation' (int)
#  'judge_model_string' (str)
#  'judgment' (str)
#  'chosen_party' (str)
#
##
def load_judgments(judgments_path):
	judgments = []

	# read the judgments
	with open(judgments_path, 'r', encoding="utf-8-sig" ) as f:
		reader = csv.reader(f)

		for line in reader:
			j = {}
			j['judgment_id'] = int( line[0] )
			scenario = parse_argstring( line[1] )
			for k, v in scenario.items():
				j[k] = v
			j['judge_model_string'] = line[2]
			j['judgment'] = line[3]

			chosen_party = re.sub( "\n```$", "", j['judgment'].strip() ) # magistral/mistral sometimes includes a ``` on the last line

			j['chosen_party'] = chosen_party.replace("\\n", "\n").strip().rsplit( "\n", 1 )[ -1 ]
			judgments.append( j )

	return judgments

def parse_argstring(argstring):
	
	ret = {}

	parts = argstring.split( '_' )
	ret['case_id'] = int( parts[0] )
	ret['party1_model'] = parts[1]
	ret['party1_variation'] = int(parts[2])
	ret['party2_model'] = parts[3]
	ret['party2_variation'] = int(parts[4])

	return ret