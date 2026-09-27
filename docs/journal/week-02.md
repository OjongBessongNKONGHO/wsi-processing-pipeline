# Week 2 — September 22-27, 2026

## Meeting with Dr. Beane (Sept 22)
- Corrected patch_size: UNI2-h requires 256, TITAN/CONCH requires 512
- Jen wants a flat config file (CSV) where researchers specify parameters
- Config must show available options so users know what to choose
- Jen downloaded NLST data: 286 slides in two zip files (200 GB)

## Work Completed
- Built encoder registry: 33 patch encoders, 12 slide encoders with required params
- Built CSV config validator: checks every parameter against encoder registry
- Built pipeline runner: reads validated config, executes TRIDENT stages in order
- Built single entry point (run_pipeline.py) with two modes: single and batch
- Reran test.svs with correct parameters (256px UNI2-h, 512px TITAN)
- Built batch processor: extracts slides from zip in batches, processes, deletes to manage storage
- Built researcher-facing config (run_config.csv) with parameter/value/options columns
- 33 tests passing (18 validator + 15 config parser)
- GitHub Actions CI running on every push
- Started processing NLST batch 1 (150 slides)

## Problems Encountered
- First batch job killed by SCC process reaper: TRIDENT spawns 8 data workers but we only requested 1 CPU. Fixed by adding -pe omp 8 to SLURM scripts.
- TITAN needs CONCH v1.5 at 512px but pipeline only extracted 256px coords. Fixed runner to auto-detect and extract at both patch sizes.
- Stale lock file from killed job blocked slide 10037. Need to add --clear_dead_locks flag.
- Storage constraint: 948 GB of 1000 GB used, 200 GB zip files on disk. Batch processing with cleanup is essential.

## Storage Analysis
- luadfrp quota: 1000 GB, 948 GB used, 52 GB free
- NLST batch 1: 150 slides, 108 GB unzipped
- NLST batch 2: 136 slides, 97 GB unzipped
- Feature outputs: under 1 MB per slide
- Strategy: extract 2-5 slides, process, delete, repeat
