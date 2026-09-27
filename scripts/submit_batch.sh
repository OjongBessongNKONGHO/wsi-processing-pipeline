#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=12:00:00
#$ -l gpu_type=A100
#$ -pe omp 8
#$ -N wsi_batch
#$ -o batch_run.log
#$ -j y

module load miniconda
conda activate trident

cd ~/wsi-processing-pipeline

python run_pipeline.py batch config/run_config.csv
