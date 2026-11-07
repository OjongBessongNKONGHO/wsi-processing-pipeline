# WSI Processing Pipeline

Config-driven pipeline for processing whole-slide pathology images on BU's Shared Computing Cluster. Takes raw .svs tissue scans and produces feature embeddings for lung cancer classification.

A single whole-slide image can exceed 100,000 x 100,000 pixels and run several gigabytes. No model processes that directly. This pipeline breaks the problem into stages: segment the tissue, remove artifacts, extract patches, encode each patch into a feature vector, and aggregate patch vectors into a single slide-level embedding. The user edits a CSV config file and runs one command. The pipeline validates every parameter against the encoder registry before touching a GPU.

Built during a Data Engineering internship at Boston University School of Medicine, Section of Computational Biomedicine, supervised by Dr. Jennifer Beane.

## Pipeline
Raw .svs slide
-> Tissue Segmentation (GrandQC: 8-class UNet)
-> Artifact Removal (pen marks, folds, dark spots, OOF regions excluded)
-> Patch Extraction (256x256 px at 20x magnification)
-> Patch Features: CONCH v1.5 (N x 768) + UNI v2 (N x 1,536)
-> Slide Features: TITAN (1 x 768 per slide)


Three encoders run in sequence. CONCH v1.5 and UNI v2 produce one vector per patch. TITAN aggregates the CONCH patch embeddings into a single slide-level vector. All three use 256px patches at 20x magnification.

## Artifact Removal

Tissue slides contain artifacts that contaminate downstream features: pen marks from pathologists, tissue folds, air bubbles, out-of-focus regions, and dark spots. Without artifact removal, the pipeline extracts patches from these regions and produces vectors that encode noise instead of tissue.

TRIDENT's `--remove_artifacts` flag activates a second segmentation pass using GrandQC's 8-class artifact model. This pass overwrites the initial tissue contours, keeping only Normal Tissue (class 1) and excluding all artifact classes. The artifact model runs at configurable magnification via `--artifact_mpp`:

| Flag | Magnification | Model file | Source |
|------|--------------|------------|--------|
| `mpp1` | 10x | `GrandQC_MPP1_state_dict.pth` | HuggingFace |
| `mpp15` | 7x | `GrandQC_MPP15_state_dict.pth` | Zenodo 14041538 |
| `mpp2` | 5x | `GrandQC_MPP2_state_dict.pth` | Zenodo 14041538 |

We patched TRIDENT to support configurable artifact magnification. The upstream codebase only supports `mpp1` (10x). The patch adds `--artifact_mpp` to the CLI and routes the flag through to `GrandQCArtifactSegmenter`.

## Standardized Parameters

Agreed with the supervising professor after iterating through four pipeline versions:

```
--segmenter grandqc
--seg_conf_thresh 0.5
--remove_artifacts
--artifact_mpp mpp15 # 7x GrandQC artifact model
--min_tissue_proportion 0.25
--skip_errors
--mag 20
--patch_size 256


## Three-Step TRIDENT Process

Each batch runs three sequential TRIDENT commands in one SGE job:

```bash
# Step 1: Segmentation + coordinates + CONCH v1.5 features
python run_batch_of_slides.py --task all \
    --patch_encoder conch_v15 --segmenter grandqc \
    --remove_artifacts --artifact_mpp mpp15 \
    --seg_conf_thresh 0.5 --min_tissue_proportion 0.25 \
    --mag 20 --patch_size 256 --skip_errors --wsi_ext .svs

# Step 2: UNI v2 patch features (reuses step 1 segmentation)
python run_batch_of_slides.py --task feat \
    --patch_encoder uni_v2 \
    --mag 20 --patch_size 256 --skip_errors --wsi_ext .svs

# Step 3: TITAN slide features (reuses step 1 CONCH embeddings)
python run_batch_of_slides.py --task feat \
    --slide_encoder titan \
    --mag 20 --patch_size 256 --skip_errors --wsi_ext .svs
```

Step 1 uses `--task all` (segmentation + coordinates + features). Steps 2 and 3 use `--task feat` (features only, reusing step 1 output).

## Config

The pipeline is driven by a CSV file. Each row is a slide. Each column is a parameter:

| wsi | segmenter | remove_artifacts | remove_penmarks | patch_encoder | patch_size | mag | overlap | slide_encoder |
|-----|-----------|-----------------|-----------------|---------------|------------|-----|---------|---------------|
| test.svs | grandqc | true | false | conch_v15 | 256 | 20 | 0 | titan |

The validator checks every cell before anything runs:
- Encoder name must exist in the registry (33 patch encoders, 12 slide encoders)
- patch_size and mag must match what the encoder was trained on
- Slide encoder's dependency on a specific patch encoder is verified
- Boolean flags must be true or false
- WSI file must exist in the specified directory
- Overlap must be less than patch_size

Wrong parameters produce embeddings that look normal but are scientifically useless. The validator exists to prevent that.

## Usage

```bash
# Validate only (no GPU needed)
python -m src.validator config/pipeline_config.csv /path/to/wsi/dir

# Run full pipeline
python run_pipeline.py config/pipeline_config.csv /path/to/wsi/dir /path/to/output/dir

# Submit as SGE batch job on SCC
qsub scripts/submit_pipeline.sh
```

## Penmark Fix

TRIDENT's default hole-detection settings miss pen marks drawn by pathologists on slides. We adjusted two parameters in the TRIDENT source:

- `min_hole_area`: 4000 to 1000 (IO.py) -- smaller holes now detected
- `max_nb_holes`: 20 to 2000 (WSI.py) -- more holes allowed per contour

Verified on test slide: detected holes increased from 29 to 166, carving out pen-mark regions that were previously included as tissue.

## Output Structure

```
trident_output/nlst_batchN_7x/20x_256px_0px_overlap/
+-- features_conch_v15/ # N x 768 per slide (.h5)
+-- features_uni_v2/ # N x 1,536 per slide (.h5)
+-- slide_features_titan/ # 1 x 768 per slide (.h5)
+-- patches/ # Patch coordinate files
+-- visualization/ # Segmentation overlay images
```


## Project Structure

```
wsi-processing-pipeline/
+-- run_pipeline.py # Single entry point: validate then run
+-- src/
| +-- encoder_registry.py # 33 patch encoders, 12 slide encoders, required params
| +-- config_parser.py # CSV config parsing
| +-- batch_processor.py # Batch orchestration with storage management
| +-- validator.py # CSV validation against encoder registry
| +-- runner.py # Builds and executes TRIDENT commands per stage
+-- config/
| +-- pipeline_config.csv # Active config (edit this)
| +-- example_config.csv # Example with test slide
| +-- OPTIONS.md # All valid values per column
+-- scripts/
| +-- submit_pipeline.sh # SGE batch wrapper (L40S GPU, luadfrp project)
+-- tests/
| +-- test_validator.py # 18 validator tests
| +-- test_config_parser.py # 15 config parser tests
| +-- fixtures/ # Valid and invalid CSV configs for testing
+-- docs/
| +-- journal/ # Weekly engineering logs
+-- .github/
+-- workflows/
+-- ci.yml # Runs 33 tests on every push


## Encoder Registry

Every encoder has a required patch_size and magnification. Using the wrong combination does not crash -- it produces bad science. The registry enforces correct pairings.

## Tests

33 tests covering config parsing, validation rules, and encoder registry consistency. CI runs on every push via GitHub Actions.

```bash
pytest tests/ -v
```
