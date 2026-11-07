#!/bin/bash -l
#$ -P luadfrp
#$ -pe omp 4
#$ -l gpus=1
#$ -l gpu_c=8.0
#$ -l h_rt=48:00:00
#$ -N wsi_pipeline
#$ -j y
#$ -o pipeline_run.log

module load cuda/12.2
conda activate /rprojectnb/luadfrp/onkongho/.conda/envs/trident

cd ~/wsi-processing-pipeline

python run_pipeline.py config/pipeline_config.csv /restricted/projectnb/luadfrp /restricted/projectnb/luadfrp/trident_output
