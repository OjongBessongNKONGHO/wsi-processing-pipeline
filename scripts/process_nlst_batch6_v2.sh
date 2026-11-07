#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l gpu_memory=48G
#$ -l h_rt=48:00:00
#$ -pe omp 8
#$ -N nlst_batch6
#$ -m ea
#$ -M onkongho@bu.edu

set -e
module load cuda/12.2
conda activate /restricted/projectnb/luadfrp/onkongho/.conda/envs/trident
export OGR_GEOJSON_MAX_OBJ_SIZE=0

WORKING_DIR="/restricted/projectnb/luadfrp/nlst_batch6_working"
JOB_DIR="/restricted/projectnb/luadfrp/trident_output/nlst_batch6"
TRIDENT="/restricted/projectnb/luadfrp/trident-src/trident/run_batch_of_slides.py"

echo "=== Slides: $(ls "$WORKING_DIR"/*.svs 2>/dev/null | wc -l) ==="

# Stage 1: Segmentation + coords + UNI v2 features (20x, 256px)
echo ""
echo "=== Stage 1: seg + coords + UNI v2 (256px) ==="
python "$TRIDENT" \
    --job_dir "$JOB_DIR" \
    --wsi_dir "$WORKING_DIR" \
    --wsi_ext .svs \
    --task all \
    --mag 20 \
    --patch_size 256 \
    --patch_encoder uni_v2

echo "Contours: $(ls "$JOB_DIR/contours/" 2>/dev/null | wc -l)"
echo "UNI v2: $(ls "$JOB_DIR/20x_256px_0px_overlap/features_uni_v2/" 2>/dev/null | wc -l)"

# Stage 2: coords + CONCH v1.5 features (20x, 512px)
echo ""
echo "=== Stage 2: coords + CONCH v1.5 (512px) ==="
python "$TRIDENT" \
    --job_dir "$JOB_DIR" \
    --wsi_dir "$WORKING_DIR" \
    --wsi_ext .svs \
    --task all \
    --mag 20 \
    --patch_size 512 \
    --patch_encoder conch_v15

echo "CONCH v1.5: $(ls "$JOB_DIR/20x_512px_0px_overlap/features_conch_v15/" 2>/dev/null | wc -l)"

# Stage 3: TITAN slide features (uses 512px coords)
echo ""
echo "=== Stage 3: TITAN slide features ==="
python "$TRIDENT" \
    --job_dir "$JOB_DIR" \
    --wsi_dir "$WORKING_DIR" \
    --wsi_ext .svs \
    --task feat \
    --mag 20 \
    --patch_size 512 \
    --slide_encoder titan

echo "TITAN: $(ls "$JOB_DIR/20x_512px_0px_overlap/slide_features_titan/" 2>/dev/null | wc -l)"

echo ""
echo "=== BATCH 6 COMPLETE ==="
echo "Total contours: $(ls "$JOB_DIR/contours/" 2>/dev/null | wc -l)"
echo "Total UNI v2: $(ls "$JOB_DIR/20x_256px_0px_overlap/features_uni_v2/" 2>/dev/null | wc -l)"
echo "Total CONCH v1.5: $(ls "$JOB_DIR/20x_512px_0px_overlap/features_conch_v15/" 2>/dev/null | wc -l)"
echo "Total TITAN: $(ls "$JOB_DIR/20x_512px_0px_overlap/slide_features_titan/" 2>/dev/null | wc -l)"
