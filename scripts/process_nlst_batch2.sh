#!/bin/bash -l
#$ -P luadfrp
#$ -l gpus=1
#$ -l gpu_memory=48G
#$ -l h_rt=48:00:00
#$ -pe omp 8
#$ -N nlst_batch2
#$ -m ea
#$ -M onkongho@bu.edu

set -e

module load cuda/12.2
conda activate /restricted/projectnb/luadfrp/onkongho/.conda/envs/trident
export OGR_GEOJSON_MAX_OBJ_SIZE=0

ZIP="/restricted/projectnb/luadfrp/NLST/NLST_pathhe_batch2.zip"
WORKING_DIR="/restricted/projectnb/luadfrp/nlst_batch2_working"
JOB_DIR="/restricted/projectnb/luadfrp/trident_output/nlst_batch2"
TRIDENT="/restricted/projectnb/luadfrp/trident-src/trident/run_batch_of_slides.py"
SLIDE_LIST="$WORKING_DIR/current_slides.csv"
TOTAL_SLIDES=136
CHUNK_SIZE=10
NUM_CHUNKS=$(( (TOTAL_SLIDES + CHUNK_SIZE - 1) / CHUNK_SIZE ))

mkdir -p "$WORKING_DIR"
mkdir -p "$JOB_DIR"

echo "============================================"
echo "NLST BATCH 2 PROCESSING"
echo "Started: $(date)"
echo "Total slides: $TOTAL_SLIDES"
echo "Chunk size: $CHUNK_SIZE"
echo "Total chunks: $NUM_CHUNKS"
echo "============================================"

ALL_SLIDES=($(unzip -l "$ZIP" | grep '\.svs$' | awk '{print $NF}' | xargs -I{} basename {} | sort))
ACTUAL_COUNT=${#ALL_SLIDES[@]}
echo "Found $ACTUAL_COUNT slides in zip"

for (( chunk=1; chunk<=NUM_CHUNKS; chunk++ )); do
    START=$(( (chunk - 1) * CHUNK_SIZE + 1 ))
    END=$(( chunk * CHUNK_SIZE ))
    if [ $END -gt $TOTAL_SLIDES ]; then
        END=$TOTAL_SLIDES
    fi

    echo ""
    echo "=== CHUNK $chunk / $NUM_CHUNKS (slides $START to $END) ==="
    echo "Time: $(date)"

    echo "[EXTRACT] Extracting $((END - START + 1)) slides ..."
    for (( i=START-1; i<END; i++ )); do
        SLIDE="${ALL_SLIDES[$i]}"
        unzip -o -j "$ZIP" "*/${SLIDE}" -d "$WORKING_DIR" 2>/dev/null || \
        unzip -o "$ZIP" "${SLIDE}" -d "$WORKING_DIR" 2>/dev/null || \
        echo "WARNING: Could not extract $SLIDE"
    done

    SVS_COUNT=$(ls "$WORKING_DIR"/*.svs 2>/dev/null | wc -l)
    echo "[EXTRACT] $SVS_COUNT SVS files ready"

    if [ "$SVS_COUNT" -eq 0 ]; then
        echo "[SKIP] No SVS files extracted for chunk $chunk, skipping"
        continue
    fi

    echo "wsi" > "$SLIDE_LIST"
    for f in "$WORKING_DIR"/*.svs; do
        basename "$f" >> "$SLIDE_LIST"
    done

    echo "[STAGE 1/6] Segmentation (GrandQC + remove_artifacts) ..."
    python "$TRIDENT" --task seg \
        --wsi_dir "$WORKING_DIR" \
        --job_dir "$JOB_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --segmenter grandqc \
        --remove_artifacts \
        --min_tissue_proportion 0.25

    echo "[STAGE 2/6] Patch coords 256px 20x ..."
    python "$TRIDENT" --task coords \
        --wsi_dir "$WORKING_DIR" \
        --job_dir "$JOB_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --mag 20 --patch_size 256 --overlap 0

    echo "[STAGE 3/6] UNI v2 features ..."
    python "$TRIDENT" --task feat \
        --wsi_dir "$WORKING_DIR" \
        --job_dir "$JOB_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --patch_encoder uni_v2 \
        --mag 20 --patch_size 256

    echo "[STAGE 4/6] Patch coords 512px 20x ..."
    python "$TRIDENT" --task coords \
        --wsi_dir "$WORKING_DIR" \
        --job_dir "$JOB_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --mag 20 --patch_size 512 --overlap 0

    echo "[STAGE 5/6] CONCH v1.5 features ..."
    python "$TRIDENT" --task feat \
        --wsi_dir "$WORKING_DIR" \
        --job_dir "$JOB_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --patch_encoder conch_v15 \
        --mag 20 --patch_size 512

    echo "[STAGE 6/6] TITAN slide features ..."
    python "$TRIDENT" --task feat \
        --wsi_dir "$WORKING_DIR" \
        --job_dir "$JOB_DIR" \
        --custom_list_of_wsis "$SLIDE_LIST" \
        --slide_encoder titan \
        --mag 20 --patch_size 512

    echo "[DONE] Chunk $chunk complete. Processed: $END / $TOTAL_SLIDES"

    rm -f "$WORKING_DIR"/*.svs
    echo "[CLEANUP] SVS files removed"
done

echo ""
echo "============================================"
echo "BATCH 2 COMPLETE"
echo "Finished: $(date)"
echo "Processed: $TOTAL_SLIDES / $TOTAL_SLIDES"
echo "Output: $JOB_DIR"
echo "============================================"
