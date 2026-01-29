#!/usr/bin/env python

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
import persuasion_utils as util

# read the scenarios
import csv

to_repeat = [279,540]

def main():

  # setup
  model_string = "mistralai/Magistral-Small-2506_defaults"
  path = "./"

  # end setup

  prompt_labels = [ 'prompt_id', 'argstring', 'prompt' ]
  prompts = util.get_judge_prompts( 'judge_prompts_arguments.csv' )

  # load the model
  model_name = model_string[:model_string.index("_")] if "_" in model_string else model_string

  # Configure the sampling parameters (for thinking mode) - default per docs
  sampling_params = SamplingParams(temperature=0.7,top_p=0.95,max_tokens=40960) # huggingface defaults for magistral

  # Initialize the vLLM engine.
  llm = LLM(model=model_name, tokenizer_mode="mistral", config_format="mistral", load_format="mistral") # for magistral (despite how it looks)

  if to_repeat is not None and len( to_repeat ) > 0:
     prompts = [ prompts[ p - 1 ] for p in to_repeat ]

  output = []
  total = len( prompts )

  with open( path + model_string.replace("/","-") + "_judgments.csv", 'a' ) as f:
    writer = csv.writer(f)

    while( len( prompts ) > 0 ):
      ( prompt_id, argstring, prompt_text ) = prompts[0]
      
      responses = llm.generate(prompt_text, sampling_params=sampling_params)
      response = responses[0].outputs[0].text
      
      writer.writerow( [ prompt_id, argstring, model_string, response ] )
      print( "Finished {} of {}".format( prompt_id, total ) )
      prompts.pop(0) #only remove from the list once it's completed successfully

# for output in outputs:
#     prompt = output.prompt
#     generated_text = output.outputs[0].text
#     print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")


if __name__ == "__main__":
    main()