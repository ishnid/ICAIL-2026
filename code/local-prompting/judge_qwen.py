#!/usr/bin/env python

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
import persuasion_utils as util

# read the scenarios
import csv


# setup
model_string = "QWen/Qwen3-8B_thinking_arguments"
path = "./"

# end setup

prompt_labels = [ 'prompt_id', 'argstring', 'prompt' ]

prompts = util.get_judge_prompts( 'judge_prompts_arguments.csv' )


# load the model

model = model_string[:model_string.index("_")] if "_" in model_string else model_string

tokenizer = AutoTokenizer.from_pretrained( model ) # for QWen

# Configure the sampling parameters (for thinking mode) - default per docs
sampling_params = SamplingParams(temperature=0.6, top_p=0.95, top_k=20, max_tokens=32768) # for QWen

# Initialize the vLLM engine.
llm = LLM(model=model) # successful test for QWen3-8B

output = []
total = len( prompts )

with open( path + model_string.replace("/","-") + "_judgments.csv", 'a' ) as f:
  writer = csv.writer(f)

  while( len( prompts ) > 0 ):
    ( prompt_id, argstring, prompt_text ) = prompts[0]
    messages = [ { "role": "user", "content": prompt_text } ]
    
    # QWen/Qwen3-8B_thinking
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,  # Set to False to strictly disable thinking
    )
    
    # # QWen/QWen3-8B_nothinking
    # text = tokenizer.apply_chat_template(
    #     messages,
    #     tokenize=False,
    #     add_generation_prompt=True,
    #     enable_thinking=False,  # Set to False to strictly disable thinking
    # )
    
    response = llm.generate([text], sampling_params) # for qwen
        
    writer.writerow( [ prompt_id, argstring, model_string, response ] )
    print( "Finished {} of {}".format( prompt_id, total ) )
    prompts.pop(0) #only remove from the list once it's completed successfully


