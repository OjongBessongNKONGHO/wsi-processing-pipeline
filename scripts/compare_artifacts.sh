#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=1:00:00
#$ -l gpu_type=A100
#$ -pe omp 8
#$ -N seg_artifacts
#$ -o seg_artifacts.log
#$ -j y

module load miniconda
conda activate trident

cd ~/trident

echo "wsi" > /tmp/slide_test2.csv
echo "test2.svs" >> /tmp/slide_test2.csv

WSI_DIR=/restricted/projectnb/luadfrp
OUTPUT=/restricted/projectnb/luadfrp/trident_output

# HEST with artifact removal
echo "=== HEST + remove_artifacts ==="
python run_batch_of_slides.py --task seg --wsi_dir $WSI_DIR --job_dir $OUTPUT/comparison_hest_artifacts --custom_list_of_wsis /tmp/slide_test2.csv --segmenter hest --remove_artifacts

# GrandQC with artifact removal
echo "=== GrandQC + remove_artifacts ==="
python run_batch_of_slides.py --task seg --wsi_dir $WSI_DIR --job_dir $OUTPUT/comparison_grandqc_artifacts --custom_list_of_wsis /tmp/slide_test2.csv --segmenter grandqc --remove_artifacts

echo "Done: $(date)"
