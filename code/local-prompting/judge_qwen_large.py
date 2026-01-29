#!/usr/bin/env python

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
import persuasion_utils as util

# read the scenarios
import csv


# setup
thinking = False
model_string="Qwen/Qwen3-32B_" + ( "thinking" if thinking else "nothinking" ) + "_noarguments"
path = "./"

# end setup

prompt_labels = [ 'prompt_id', 'argstring', 'prompt' ]

prompts = util.get_judge_prompts( 'judge_prompts_noarguments.csv' )


# load the model

model = model_string[:model_string.index("_")] if "_" in model_string else model_string

tokenizer = AutoTokenizer.from_pretrained( model ) # for QWen

# Configure the sampling parameters (for thinking mode) - default per docs
if thinking:
  sampling_params = SamplingParams(temperature=0.6, top_p=0.95, top_k=20, min_p=0, max_tokens=32768) # for QWen thinking
else:
  sampling_params = SamplingParams(temperature=0.7, top_p=0.8, top_k=20, min_p=0, max_tokens=32768) # for QWen nothinking

# Initialize the vLLM engine.
#llm = LLM(model="facebook/opt-125m")

llm = LLM(model=model,max_model_len=18000) 

total = len( prompts )

with open( path + model_string.replace("/","-") + "_judgments.csv", 'a' ) as f:
  writer = csv.writer(f)

  while( len( prompts ) > 0 ):
    ( prompt_id, argstring, prompt_text ) = prompts[0]
    messages = [ { "role": "user", "content": prompt_text } ]
    
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=thinking,
    )
    
    response = llm.generate([text], sampling_params)
        
    writer.writerow( [ prompt_id, argstring, model_string, response ] )
    print( "Finished {} of {}".format( prompt_id, total ) )
    prompts.pop(0) #only remove from the list once it's completed successfully



