#!/bin/bash
#SBATCH --partition=gpus48       
#SBATCH --gres=gpu:1             
#SBATCH --output=/vol/biomedic3/bglocker/mscproj24/fz221/cxr-fmkd/models/knowledge_distillation/multiruns_slurm_scripts/multiruns_slurm_logs/cxrfmkd_kdinit_cosinesim/%x.%N.%j.log  
#SBATCH --time=1-00:00:00  
#SBATCH --nodelist=luna       

# Accepts multirun_seed from the command line; --job-name replaces the %x in --output above
#SBATCH --job-name=cxrfmkd_kdinit_cosinesim_multirun

# Activate the Python virtual environment (fmkd_venv)
source /vol/bitbucket/fz221/fmkd_venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=/vol/biomedic3/bglocker/mscproj24/fz221/cxr-fmkd/:$PYTHONPATH

# Set wandb directories
export WANDB_CACHE_DIR=/vol/biomedic3/bglocker/mscproj24/fz221/.wandb_storage/cache
export WANDB_CONFIG_DIR=/vol/biomedic3/bglocker/mscproj24/fz221/.wandb_storage/config

# Run the Python script
python /vol/biomedic3/bglocker/mscproj24/fz221/cxr-fmkd/models/knowledge_distillation/kd_initialisation__CXR_FMKD__CosineSim.py --multirun_seed "$1" --config "$2"
