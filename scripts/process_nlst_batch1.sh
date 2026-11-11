#!/bin/bash -l

# NLST Batch 1 (150 slides) -- Standardized Parameters
#$ -N trident_b1
#$ -P luadfrp
#$ -pe omp 4
#$ -l gpus=1
#$ -l gpu_c=8.0
#$ -l h_rt=48:00:00
#$ -j y
#$ -m ea

TRIDENT_DIR="/usr2/collab/onkongho/trident"
WSI_DIR="/restricted/projectnb/luadfrp/nlst_svs/batch1_svs"
JOB_DIR="/restricted/projectnb/luadfrp/trident_output/nlst_batch1_7x"

module load cuda/12.2
conda activate /rprojectnb/luadfrp/onkongho/.conda/envs/trident
cd "$TRIDENT_DIR"

mkdir -p "$JOB_DIR"

echo "=== Batch 1: $(ls "$WSI_DIR"/*.svs 2>/dev/null | wc -l) slides ==="

# Step 1: Full pipeline (seg + coords + CONCH v1.5)
python run_batch_of_slides.py \
    --task all \
    --wsi_dir "$WSI_DIR" --job_dir "$JOB_DIR" \
    --segmenter grandqc --seg_conf_thresh 0.5 \
    --remove_artifacts --artifact_mpp mpp15 \
    --min_tissue_proportion 0.25 --skip_errors \
    --mag 20 --patch_size 256 --max_workers 3 \
    --patch_encoder conch_v15 --wsi_ext .svs

# Step 2: UNI v2 patch features
python run_batch_of_slides.py \
    --task feat \
    --wsi_dir "$WSI_DIR" --job_dir "$JOB_DIR" \
    --mag 20 --patch_size 256 --max_workers 3 \
    --patch_encoder uni_v2 --skip_errors --wsi_ext .svs

# Step 3: TITAN slide-level features
python run_batch_of_slides.py \
    --task feat \
    --wsi_dir "$WSI_DIR" --job_dir "$JOB_DIR" \
    --mag 20 --patch_size 256 --max_workers 3 \
    --slide_encoder titan --skip_errors --wsi_ext .svs

echo "=== Batch 1 complete ==="
