#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=2:00:00
#$ -l gpu_type=A100
#$ -N trident_test
#$ -o trident_test.log
#$ -j y

module load miniconda
conda activate trident

cd ~/trident

python run_batch_of_slides.py \
  --task seg \
  --wsi_dir /restricted/projectnb/luadfrp \
  --job_dir /restricted/projectnb/luadfrp/trident_output \
  --custom_list_of_wsis ~/wsi-processing-pipeline/test_slides.csv

echo "Done: $(date)"
