#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=2:00:00
#$ -l gpu_type=A100
#$ -N trident_titan
#$ -o trident_step4_titan.log
#$ -j y

module load miniconda
conda activate trident

cd ~/trident

python run_batch_of_slides.py \
  --task feat \
  --wsi_dir /restricted/projectnb/luadfrp \
  --job_dir /restricted/projectnb/luadfrp/trident_output \
  --custom_list_of_wsis ~/wsi-processing-pipeline/test_slides.csv \
  --slide_encoder titan \
  --patch_size 224 \
  --mag 20

echo "Done: $(date)"
