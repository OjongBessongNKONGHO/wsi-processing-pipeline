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
ZIP="/restricted/projectnb/luadfrp/NLST/NLST_pathhe_batch6.zip"
TOTAL_SLIDES=106
CHUNK_SIZE=10
NUM_CHUNKS=$(( (TOTAL_SLIDES + CHUNK_SIZE - 1) / CHUNK_SIZE ))

mkdir -p "$WORKING_DIR"
mkdir -p "$JOB_DIR"

# Unzip all slides first
echo "=== Unzipping slides ==="
unzip -n -j "$ZIP" "*.svs" -d "$WORKING_DIR"
echo "Unzipped slides: $(ls "$WORKING_DIR"/*.svs 2>/dev/null | wc -l)"

# Build slide list
ls "$WORKING_DIR"/*.svs > "$WORKING_DIR/all_slides.csv"

for (( i=0; i<NUM_CHUNKS; i++ )); do
    START=$(( i * CHUNK_SIZE + 1 ))
    END=$(( (i+1) * CHUNK_SIZE ))
    if [ $END -gt $TOTAL_SLIDES ]; then END=$TOTAL_SLIDES; fi
    
    echo ""
    echo "=== Processing chunk $((i+1))/$NUM_CHUNKS (slides $START-$END) ==="
    
    sed -n "${START},${END}p" "$WORKING_DIR/all_slides.csv" > "$WORKING_DIR/current_slides.csv"
    
    python "$TRIDENT" \
        --job_dir "$JOB_DIR" \
        --slide_list "$WORKING_DIR/current_slides.csv" \
        --segmentation \
        --coords_256 \
        --features_uni_v2 \
        --coords_512 \
        --features_conch_v15 \
        --features_titan
    
    echo "Contours so far: $(ls "$JOB_DIR/contours/" 2>/dev/null | wc -l)"
done

echo ""
echo "=== BATCH 6 COMPLETE ==="
echo "Total contours: $(ls "$JOB_DIR/contours/" | wc -l)"
echo "Total UNI v2: $(ls "$JOB_DIR/20x_256px_0px_overlap/features_uni_v2/" 2>/dev/null | wc -l)"
echo "Total CONCH v1.5: $(ls "$JOB_DIR/20x_512px_0px_overlap/features_conch_v15/" 2>/dev/null | wc -l)"
echo "Total TITAN: $(ls "$JOB_DIR/20x_512px_0px_overlap/slide_features_titan/" 2>/dev/null | wc -l)"
