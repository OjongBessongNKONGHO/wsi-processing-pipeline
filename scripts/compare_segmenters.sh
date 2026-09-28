#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l h_rt=1:00:00
#$ -l gpu_type=A100
#$ -pe omp 8
#$ -N seg_compare
#$ -o seg_compare.log
#$ -j y

module load miniconda
conda activate trident

cd ~/trident

WSI_DIR=/restricted/projectnb/luadfrp/trident_output/_temp_comparison/batch3

echo "wsi" > /tmp/slide_compare.csv
echo "10120.svs" >> /tmp/slide_compare.csv

# Run with HEST
echo "=== HEST ==="
python run_batch_of_slides.py --task seg --wsi_dir $WSI_DIR --job_dir /restricted/projectnb/luadfrp/trident_output/comparison_hest --custom_list_of_wsis /tmp/slide_compare.csv --segmenter hest

# Run with GrandQC
echo "=== GrandQC ==="
python run_batch_of_slides.py --task seg --wsi_dir $WSI_DIR --job_dir /restricted/projectnb/luadfrp/trident_output/comparison_grandqc --custom_list_of_wsis /tmp/slide_compare.csv --segmenter grandqc

# Cleanup
rm -rf /restricted/projectnb/luadfrp/trident_output/_temp_comparison

echo "Done: $(date)"
