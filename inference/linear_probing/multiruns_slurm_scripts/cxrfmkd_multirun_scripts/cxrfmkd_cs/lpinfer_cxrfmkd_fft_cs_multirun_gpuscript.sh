#!/bin/bash
#SBATCH --partition=gpus48       
#SBATCH --gres=gpu:1             
#SBATCH --output=/vol/biomedic3/bglocker/mscproj24/fz221/cxr-fmkd/inference/linear_probing/multiruns_slurm_scripts/multiruns_slurm_logs/lpinfer_cxrfmkd/cxrfmkd_cs/cxrfmkd_fft_cs/%x.%N.%j.log  
#SBATCH --time=0-05:00:00
# #SBATCH --nodelist=luna 

# Accepts multirun_seed from the command line; --job-name replaces the %x in --output above
#SBATCH --job-name=lpinfer_cxrfmkd_fft_cs_multirun

# Activate the Python virtual environment (fmkd_venv)
source /vol/bitbucket/fz221/fmkd_venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=/vol/biomedic3/bglocker/mscproj24/fz221/cxr-fmkd/:$PYTHONPATH

# Set wandb directories
export WANDB_CACHE_DIR=/vol/biomedic3/bglocker/mscproj24/fz221/.wandb_storage/cache
export WANDB_CONFIG_DIR=/vol/biomedic3/bglocker/mscproj24/fz221/.wandb_storage/config

# Run the Python script
python /vol/biomedic3/bglocker/mscproj24/fz221/cxr-fmkd/inference/linear_probing/linear_probing_inference__CXR_FMKD__full_finetuning.py --kd_type 'CS' --multirun_seed "$1" --inference_on "$2"
