#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=1:00:00
#$ -l gpu_type=A100
#$ -pe omp 8
#$ -N fix_10037
#$ -o fix_10037.log
#$ -j y

module load miniconda
conda activate trident

cd ~/trident

# Create slide list
echo "wsi" > /tmp/slide_10037.csv
echo "10037.svs" >> /tmp/slide_10037.csv

WSI_DIR=/restricted/projectnb/luadfrp/trident_output/_temp_10037/batch1
JOB_DIR=/restricted/projectnb/luadfrp/trident_output

# 512px coords
python run_batch_of_slides.py --task coords --wsi_dir $WSI_DIR --job_dir $JOB_DIR --custom_list_of_wsis /tmp/slide_10037.csv --mag 20 --patch_size 512 --overlap 0 --clear_dead_locks

# CONCH v1.5 features
python run_batch_of_slides.py --task feat --wsi_dir $WSI_DIR --job_dir $JOB_DIR --custom_list_of_wsis /tmp/slide_10037.csv --patch_encoder conch_v15 --mag 20 --patch_size 512 --clear_dead_locks

# TITAN
python run_batch_of_slides.py --task feat --wsi_dir $WSI_DIR --job_dir $JOB_DIR --custom_list_of_wsis /tmp/slide_10037.csv --slide_encoder titan --patch_size 512 --mag 20 --clear_dead_locks

# Cleanup
rm -rf /restricted/projectnb/luadfrp/trident_output/_temp_10037

echo "Done: $(date)"
