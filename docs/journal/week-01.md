# Week 1 — September 15-19, 2026

## Meeting with Dr. Beane (Sept 15)
- Discussed project scope: TRIDENT pipeline deployment on SCC
- Agreed on UNI2-h (patch encoder) and TITAN (slide encoder)
- Config-driven approach for lab usability
- Weekly meetings every Tuesday at 18:00 CET

## Work Completed
- Set up SCC access: SSH, Duo 2FA, conda environment on luadfrp project space
- Installed TRIDENT with patch and slide encoder support
- Created HuggingFace account, obtained gated access for UNI2-h, TITAN, CONCH v1.5
- Ran full pipeline on test.svs (incorrect patch_size 224, later corrected to 256)
- Created GitHub repo (wsi-processing-pipeline)

## Problems Encountered
- Conda environment not visible across login nodes (scc1 vs scc4) due to different filesystem mounts. Pinned workflow to scc4.
- Tesla K40m GPUs too old for PyTorch CUDA. Solved by requesting A100 nodes in SLURM scripts.
- Interactive SSH sessions dropping mid-job from Paris. Switched to batch jobs.
- TRIDENT encoder name mismatch: UNI2-h is called "uni_v2" internally, not "uni2h".
- TITAN silently requires CONCH v1.5 access. First run failed until access was approved.
