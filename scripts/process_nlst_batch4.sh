#!/bin/bash -l
#$ -P luadfrp
#$ -l h_rt=24:00:00
#$ -l gpus=1
#$ -l gpu_memory=40G
#$ -pe omp 8
#$ -N nlst_batch4
#$ -j y
#$ -o /usr2/collab/onkongho/wsi-processing-pipeline/logs/nlst_batch4_$JOB_ID.log

set -euo pipefail

module load miniconda
conda activate trident

export OGR_GEOJSON_MAX_OBJ_SIZE=0

TRIDENT=/restricted/projectnb/luadfrp/trident-src/trident/run_batch_of_slides.py
BATCH_ZIP=/restricted/projectnb/luadfrp/NLST/NLST_pathhe_batch4.zip
OUTPUT_DIR=/restricted/projectnb/luadfrp/trident_output/nlst_batch4
WORK_DIR=/restricted/projectnb/luadfrp/nlst_batch4_working
SLIDE_LIST=/usr2/collab/onkongho/wsi-processing-pipeline/config/nlst_batch4_chunk.csv
CHUNK_SIZE=10

mkdir -p "$OUTPUT_DIR"
mkdir -p "$WORK_DIR"
mkdir -p "$(dirname $SLIDE_LIST)"

echo "============================================"
echo "NLST Batch 4 Processing"
echo "Started: $(date)"
echo "Job ID: $JOB_ID"
echo "Host: $(hostname)"
echo "============================================"

mapfile -t ALL_SLIDES < <(unzip -l "$BATCH_ZIP" | grep -i '\.svs$' | awk '{print $NF}')
TOTAL=${#ALL_SLIDES[@]}
echo "[INFO] Found $TOTAL slides"

PROCESSED=0

for ((i=0; i<TOTAL; i+=CHUNK_SIZE)); do
    CHUNK_END=$((i + CHUNK_SIZE))
    if [ $CHUNK_END -gt $TOTAL ]; then
        CHUNK_END=$TOTAL
    fi
    CHUNK_NUM=$(( (i / CHUNK_SIZE) + 1 ))
    CHUNK_TOTAL=$(( (TOTAL + CHUNK_SIZE - 1) / CHUNK_SIZE ))

    echo ""
    echo "=== CHUNK $CHUNK_NUM / $CHUNK_TOTAL (slides $((i+1)) to $CHUNK_END) ==="
    echo "Time: $(date)"

    rm -f "$WORK_DIR"/*.svs

    CHUNK_SLIDES=("${ALL_SLIDES[@]:$i:$CHUNK_SIZE}")

    echo "[EXTRACT] Extracting ${#CHUNK_SLIDES[@]} slides ..."
    for slide in "${CHUNK_SLIDES[@]}"; do
        unzip -o -j "$BATCH_ZIP" "$slide" -d "$WORK_DIR"
    done

    EXTRACTED_COUNT=$(ls "$WORK_DIR"/*.svs 2>/dev/null | wc -l)
    echo "[EXTRACT] $EXTRACTED_COUNT SVS files ready"

    echo "wsi" > "$SLIDE_LIST"
    for f in "$WORK_DIR"/*.svs; do
        echo "$(basename $f)" >> "$SLIDE_LIST"
    done

    echo "[STAGE 1/6] Segmentation (GrandQC + remove_artifacts) ..."
    python $TRIDENT \
        --task seg \
        --wsi_dir "$WORK_DIR" \
        --job_dir "$OUTPUT_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --segmenter grandqc \
        --remove_artifacts \
        --min_tissue_proportion 0.25

    echo "[STAGE 2/6] Patch coords 256px 20x ..."
    python $TRIDENT \
        --task coords \
        --wsi_dir "$WORK_DIR" \
        --job_dir "$OUTPUT_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --mag 20 \
        --patch_size 256 \
        --overlap 0

    echo "[STAGE 3/6] UNI v2 features ..."
    python $TRIDENT \
        --task feat \
        --wsi_dir "$WORK_DIR" \
        --job_dir "$OUTPUT_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --patch_encoder uni_v2 \
        --mag 20 \
        --patch_size 256

    echo "[STAGE 4/6] Patch coords 512px 20x ..."
    python $TRIDENT \
        --task coords \
        --wsi_dir "$WORK_DIR" \
        --job_dir "$OUTPUT_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --mag 20 \
        --patch_size 512 \
        --overlap 0

    echo "[STAGE 5/6] CONCH v1.5 features ..."
    python $TRIDENT \
        --task feat \
        --wsi_dir "$WORK_DIR" \
        --job_dir "$OUTPUT_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --patch_encoder conch_v15 \
        --mag 20 \
        --patch_size 512

    echo "[STAGE 6/6] TITAN slide features ..."
    python $TRIDENT \
        --task feat \
        --wsi_dir "$WORK_DIR" \
        --job_dir "$OUTPUT_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --slide_encoder titan \
        --mag 20 \
        --patch_size 512

    PROCESSED=$((PROCESSED + EXTRACTED_COUNT))
    echo "[DONE] Chunk $CHUNK_NUM complete. Processed: $PROCESSED / $TOTAL"

    rm -f "$WORK_DIR"/*.svs
    echo "[CLEANUP] SVS files removed"
done

echo ""
echo "============================================"
echo "BATCH 4 COMPLETE"
echo "Finished: $(date)"
echo "Processed: $PROCESSED / $TOTAL"
echo "Output: $OUTPUT_DIR"
echo "============================================"

rmdir "$WORK_DIR" 2>/dev/null || true
