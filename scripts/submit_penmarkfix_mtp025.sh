#!/bin/bash -l
#$ -P luadfrp
#$ -l h_rt=6:00:00
#$ -l gpus=1
#$ -l gpu_memory=40G
#$ -N penmarkfix_mtp025
#$ -j y
#$ -o /usr2/collab/onkongho/wsi-processing-pipeline/logs/penmarkfix_mtp025.log

module load miniconda
conda activate trident

TRIDENT=/restricted/projectnb/luadfrp/trident-src/trident/run_batch_of_slides.py
WSI_DIR=/restricted/projectnb/luadfrp
JOB_DIR=/restricted/projectnb/luadfrp/trident_output/penmarkfix_mtp025
SLIDE_LIST=/usr2/collab/onkongho/wsi-processing-pipeline/config/test_both_list.csv

echo "=========================================="
echo "Stage 1: Segmentation (GrandQC + remove_artifacts)"
echo "=========================================="
python $TRIDENT \
    --task seg \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --segmenter grandqc \
    --remove_artifacts

echo "=========================================="
echo "Stage 2: Patch coords (256px, 20x, mtp=0.25)"
echo "=========================================="
python $TRIDENT \
    --task coords \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --mag 20 \
    --patch_size 256 \
    --overlap 0 \
    --min_tissue_proportion 0.25

echo "=========================================="
echo "Stage 3: Patch features (UNI v2, 256px)"
echo "=========================================="
python $TRIDENT \
    --task feat \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --patch_encoder uni_v2 \
    --mag 20 \
    --patch_size 256 \
    --min_tissue_proportion 0.25

echo "=========================================="
echo "Stage 4: Patch coords (512px, 20x, mtp=0.25)"
echo "=========================================="
python $TRIDENT \
    --task coords \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --mag 20 \
    --patch_size 512 \
    --overlap 0 \
    --min_tissue_proportion 0.25

echo "=========================================="
echo "Stage 5: Patch features (CONCH v1.5, 512px)"
echo "=========================================="
python $TRIDENT \
    --task feat \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --patch_encoder conch_v15 \
    --mag 20 \
    --patch_size 512 \
    --min_tissue_proportion 0.25

echo "=========================================="
echo "Stage 6: Slide features (TITAN)"
echo "=========================================="
python $TRIDENT \
    --task feat \
    --wsi_dir $WSI_DIR \
    --job_dir $JOB_DIR \
    --custom_list_of_wsis $SLIDE_LIST \
    --slide_encoder titan \
    --mag 20 \
    --patch_size 512 \
    --min_tissue_proportion 0.25

echo "=========================================="
echo "PIPELINE COMPLETE"
echo "=========================================="
