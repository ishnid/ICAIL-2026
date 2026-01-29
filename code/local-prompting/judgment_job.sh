#!/bin/bash -l
#SBATCH --job-name=judgment
# speficity number of nodes 
#SBATCH -N 1
# specify the gpu queue

#SBATCH --partition=csgpu
# Request 2 gpus
#SBATCH --gres=gpu:1

# specify number of tasks/cores per node required
##-#SBATCH --ntasks-per-node=35

#SBATCH --error=err.txt

# specify the walltime e.g 20 mins
#SBATCH -t 12:00:00

# set to email at start,end and failed jobs
#SBATCH --mail-type=ALL
#SBATCH --mail-user=an-onymouse@example.com

# load python later version
module load python/3.13

source ~/vllm_env/bin/activate

# run from current directory
cd $SLURM_SUBMIT_DIR

# command to use
# stdbuf -oL -eL python judge_qwen.py
# stdbuf -oL -eL python judge_qwen_large.py
# stdbuf -oL -eL python judge_magistral.py
stdbuf -oL -eL python judge_mistral.py

