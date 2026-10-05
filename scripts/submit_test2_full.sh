#!/bin/bash -l
#$ -P luadfrp
#$ -l h_rt=6:00:00
#$ -l gpus=1
#$ -l gpu_memory=40G
#$ -N test2_full_pipeline
#$ -j y
#$ -o /usr2/collab/onkongho/wsi-processing-pipeline/logs/test2_full_pipeline.log

module load miniconda
conda activate trident

TRIDENT=/restricted/projectnb/luadfrp/trident-src/trident/run_batch_of_slides.py
WSI_DIR=/restricted/projectnb/luadfrp
JOB_DIR=/restricted/projectnb/luadfrp/trident_output/comparison_grandqc_penmarkfix
SLIDE_LIST=/usr2/collab/onkongho/wsi-processing-pipeline/config/test2_list.csv

echo "wsi" > $SLIDE_LIST
echo "test2.svs" >> $SLIDE_LIST

echo "=========================================="
echo "Stage 1: Segmentation (should skip — already done)"
echo "=========================================="
python $TRIDENT \
    --task seg \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --segmenter grandqc \
    --remove_artifacts

echo "=========================================="
echo "Stage 2: Patch Extraction (256px, 20x)"
echo "=========================================="
python $TRIDENT \
    --task coords \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --mag 20 \
    --patch_size 256 \
    --overlap 0

echo "=========================================="
echo "Stage 3: Patch Features (uni_v2)"
echo "=========================================="
python $TRIDENT \
    --task feat \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --patch_encoder uni_v2 \
    --mag 20 \
    --patch_size 256

echo "=========================================="
echo "Stage 4a: Patch Extraction (512px for TITAN)"
echo "=========================================="
python $TRIDENT \
    --task coords \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --mag 20 \
    --patch_size 512 \
    --overlap 0

echo "=========================================="
echo "Stage 4b: Patch Features (conch_v15 for TITAN)"
echo "=========================================="
python $TRIDENT \
    --task feat \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --patch_encoder conch_v15 \
    --mag 20 \
    --patch_size 512

echo "=========================================="
echo "Stage 4c: Slide Features (TITAN)"
echo "=========================================="
python $TRIDENT \
    --task feat \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --slide_encoder titan \
    --mag 20 \
    --patch_size 512

echo "=========================================="
echo "PIPELINE COMPLETE"
echo "=========================================="
