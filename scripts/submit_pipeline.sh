#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=2:00:00
#$ -l gpu_type=A100
#$ -N wsi_pipeline
#$ -o pipeline_run.log
#$ -j y

module load miniconda
conda activate trident

cd ~/wsi-processing-pipeline

python run_pipeline.py config/pipeline_config.csv /restricted/projectnb/luadfrp /restricted/projectnb/luadfrp/trident_output
