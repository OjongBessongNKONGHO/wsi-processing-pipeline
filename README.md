# WSI Processing Pipeline

Config-driven pipeline for processing whole-slide pathology images on BU's Shared Computing Cluster. Takes raw .svs tissue scans and produces feature embeddings for lung cancer classification.

A single whole-slide image can exceed 100,000 x 100,000 pixels and run several gigabytes. No model processes that directly. This pipeline breaks the problem into stages: segment the tissue, extract patches, encode each patch into a feature vector, and aggregate patch vectors into a single slide-level embedding. The user edits a CSV config file and runs one command. The pipeline validates every parameter against the encoder registry before touching a GPU.

Built during a Data Engineering internship at Boston University School of Medicine, Section of Computational Biomedicine, supervised by Dr. Jennifer Beane.

## Pipeline

```
Raw .svs slide
  → Tissue Segmentation (hest | grandqc | otsu)
  → Patch Extraction (configurable mag, patch_size, overlap)
  → Patch Feature Extraction (UNI2-h: 11,505 patches → 11,505 × 1,536 embeddings)
  → Slide Feature Extraction (TITAN: 2,993 patches → 1 × 768 embedding)
```

TITAN requires CONCH v1.5 at 512px internally. The runner detects this from the encoder registry, extracts 512px coordinates and CONCH features automatically, then runs TITAN. The user does not need to know this.

## Config

The pipeline is driven by a CSV file. Each row is a slide. Each column is a parameter:

| wsi | segmenter | remove_artifacts | remove_penmarks | patch_encoder | patch_size | mag | overlap | slide_encoder |
|-----|-----------|-----------------|-----------------|---------------|------------|-----|---------|---------------|
| test.svs | hest | false | false | uni_v2 | 256 | 20 | 0 | titan |

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

# Submit as SLURM batch job on SCC
qsub scripts/submit_pipeline.sh
```

## Project Structure

```
wsi-processing-pipeline/
├── run_pipeline.py              # Single entry point: validate then run
├── src/
│   ├── encoder_registry.py      # 33 patch encoders, 12 slide encoders, required params
│   ├── validator.py             # CSV validation against encoder registry
│   └── runner.py                # Builds and executes TRIDENT commands per stage
├── config/
│   ├── pipeline_config.csv      # Active config (edit this)
│   ├── example_config.csv       # Example with test slide
│   └── OPTIONS.md               # All valid values per column
├── scripts/
│   └── submit_pipeline.sh       # SLURM batch wrapper (A100, 2hr, luadfrp project)
├── tests/
│   ├── test_validator.py        # 18 tests covering every validation rule
│   └── fixtures/                # Valid and invalid CSV configs for testing
├── docs/
│   └── journal/                 # Weekly engineering logs
└── .github/
    └── workflows/
        └── ci.yml               # Runs tests on every push
```

## Encoder Registry

Every encoder has a required patch_size and magnification. Using the wrong combination does not crash — it produces bad science. The registry enforces correct pairings.

Selected entries:

| Encoder | Type | patch_size | mag | Embedding Dim |
|---------|------|------------|-----|---------------|
| uni_v2 (UNI2-h) | patch | 256 | 20 | 1,536 |
| conch_v15 | patch | 512 | 20 | 768 |
| virchow2 | patch | 224 | 20 | 2,560 |
| titan | slide | 512 (via conch_v15) | 20 | 768 |
| prism | slide | 224 (via virchow2) | 20 | — |

Full list: 33 patch encoders and 12 slide encoders in `src/encoder_registry.py`.

## Test Slide Results

Pipeline output for test.svs (285 MB, lung tissue H&E):

| Stage | Output | Shape |
|-------|--------|-------|
| Segmentation | contours/test.jpg | tissue boundary mask |
| Patch Extraction (256px) | patches/test_patches.h5 | 11,505 patch coordinates |
| UNI2-h Features | features_uni_v2/test.h5 | (11,505, 1,536) float32 |
| Patch Extraction (512px) | patches/test_patches.h5 | 2,993 patch coordinates |
| CONCH v1.5 Features | features_conch_v15/test.h5 | (2,993, 768) float32 |
| TITAN Slide Features | slide_features_titan/test.h5 | (768,) float32 |

285 MB raw image → under 1 MB of AI-ready data.

## Tests

18 tests covering config validation, encoder registry integrity, and error detection.

```bash
pytest tests/ -v
```

Tests run without GPUs, slide files, or TRIDENT installed. CI runs on every push via GitHub Actions.

## Requirements

- Python 3.10
- TRIDENT (cloned separately, not bundled)
- HuggingFace access for gated models (UNI2-h, TITAN, CONCH v1.5)
- SCC access with SLURM and GPU nodes

## Infrastructure

- **Cluster:** Boston University Shared Computing Cluster (SCC)
- **GPU:** NVIDIA A100
- **Scheduler:** SLURM (SGE on SCC)
- **Storage:** /restricted/projectnb/luadfrp (shared project space)
- **Environment:** conda (trident, Python 3.10)

## Stack

Python, SLURM, HPC, TRIDENT, Patho-Bench, pytest, GitHub Actions, conda, Git

## References

- [TRIDENT — Mahmood Lab, Harvard](https://github.com/mahmoodlab/TRIDENT)
- [UNI2-h](https://huggingface.co/MahmoodLab/UNI2-h) — Chen et al., Nature Medicine 2024
- [TITAN](https://huggingface.co/MahmoodLab/TITAN) — arXiv:2411.19666
- [Patho-Bench](https://github.com/mahmoodlab/Patho-Bench) — Zhang et al., arXiv:2502.06750
