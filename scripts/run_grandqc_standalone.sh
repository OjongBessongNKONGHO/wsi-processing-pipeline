#!/bin/bash -l

# =============================================================================
# GrandQC Standalone -- Visualization masks (tissue + artifact detection)
# Reads SVS files directly, independent of TRIDENT output
# =============================================================================

#$ -N grandqc_masks
#$ -P luadfrp
#$ -pe omp 4
#$ -l gpus=1
#$ -l gpu_type=L40S
#$ -l h_rt=48:00:00
#$ -m ea
#$ -j y

conda activate grandqc

GRANDQC_DIR="/usr2/collab/onkongho/grandqc/01_WSI_inference_OPENSLIDE_QC"
OUTPUT_BASE="/restricted/projectnb/luadfrp/trident_output"

cd "$GRANDQC_DIR"

for BATCH in 3 4 5 6 7 8 9; do
    SVS_DIR="/restricted/projectnb/luadfrp/batch${BATCH}_svs"
    BATCH_OUTPUT="${OUTPUT_BASE}/grandqc_masks_batch${BATCH}"

    if [ -d "$SVS_DIR" ]; then
        echo "Processing batch ${BATCH}: $(ls "$SVS_DIR"/*.svs 2>/dev/null | wc -l) slides"
        python main.py \
            --slide_folder "$SVS_DIR" \
            --output_dir "$BATCH_OUTPUT" \
            --create_geojson "Y" \
            --mpp_model 1.5
    fi
done
