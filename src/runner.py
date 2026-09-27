"""
Pipeline Runner for WSI Processing Pipeline.

Takes a validated CSV config and executes TRIDENT stages in order
for each slide: segmentation → patch extraction → patch features → slide features.
"""

import csv
import subprocess
import sys
import os
from datetime import datetime

from src.encoder_registry import get_slide_encoder_spec


TRIDENT_SCRIPT = os.path.expanduser("~/trident/run_batch_of_slides.py")


def build_seg_command(row: dict, wsi_dir: str, job_dir: str) -> list[str]:
    """Build the TRIDENT segmentation command from a config row."""
    cmd = [
        "python", TRIDENT_SCRIPT,
        "--task", "seg",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", "",  # placeholder, set by caller
        "--segmenter", row["segmenter"].strip().lower(),
    ]

    if row["remove_artifacts"].strip().lower() == "true":
        cmd.append("--remove_artifacts")

    if row["remove_penmarks"].strip().lower() == "true":
        cmd.append("--remove_penmarks")

    return cmd


def build_coords_command(row: dict, wsi_dir: str, job_dir: str) -> list[str]:
    """Build the TRIDENT patch extraction command from a config row."""
    return [
        "python", TRIDENT_SCRIPT,
        "--task", "coords",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", "",  # placeholder, set by caller
        "--mag", row["mag"].strip(),
        "--patch_size", row["patch_size"].strip(),
        "--overlap", row["overlap"].strip(),
    ]


def build_patch_feat_command(row: dict, wsi_dir: str, job_dir: str) -> list[str]:
    """Build the TRIDENT patch feature extraction command from a config row."""
    return [
        "python", TRIDENT_SCRIPT,
        "--task", "feat",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", "",  # placeholder, set by caller
        "--patch_encoder", row["patch_encoder"].strip(),
        "--mag", row["mag"].strip(),
        "--patch_size", row["patch_size"].strip(),
    ]


def build_slide_feat_command(row: dict, wsi_dir: str, job_dir: str) -> list[str]:
    """Build the TRIDENT slide feature extraction command from a config row."""
    slide_encoder = row["slide_encoder"].strip()
    slide_spec = get_slide_encoder_spec(slide_encoder)
    required_patch_encoder = slide_spec["requires_patch_encoder"]

    # TITAN needs CONCH v1.5 patches, so we use CONCH's patch_size and mag
    from src.encoder_registry import get_patch_encoder_spec
    required_spec = get_patch_encoder_spec(required_patch_encoder)

    return [
        "python", TRIDENT_SCRIPT,
        "--task", "feat",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", "",  # placeholder, set by caller
        "--slide_encoder", slide_encoder,
        "--patch_size", str(required_spec["patch_size"]),
        "--mag", str(required_spec["mag"]),
    ]


def create_slide_list(wsi_filename: str, output_path: str) -> str:
    """Create a temporary CSV file listing one slide for TRIDENT."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["wsi"])
        writer.writerow([wsi_filename])
    return output_path


def run_command(cmd: list[str], stage: str, wsi: str) -> bool:
    """Execute a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {stage}: {wsi}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"\n✗ FAILED: {stage} for {wsi} (exit code {result.returncode})")
        return False

    print(f"\n✓ COMPLETE: {stage} for {wsi}")
    return True


def run_pipeline(csv_path: str, wsi_dir: str, job_dir: str) -> dict:
    """
    Run the full TRIDENT pipeline for each slide in the config CSV.

    Args:
        csv_path: Path to validated CSV config.
        wsi_dir: Directory containing WSI files.
        job_dir: Output directory for results.

    Returns:
        Summary dict with counts of successful and failed slides.
    """
    # Create job directory if it doesn't exist
    os.makedirs(job_dir, exist_ok=True)

    # Read config
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    success = 0
    failed = 0
    results = []

    print(f"\nPipeline starting: {total} slide(s) to process")
    print(f"WSI directory: {wsi_dir}")
    print(f"Output directory: {job_dir}")
    start_time = datetime.now()

    for i, row in enumerate(rows, start=1):
        wsi = row["wsi"].strip()
        print(f"\n{'#'*60}")
        print(f"Slide {i}/{total}: {wsi}")
        print(f"{'#'*60}")

        # Create temporary slide list for TRIDENT
        slide_list_path = os.path.join(job_dir, f"_temp_slide_list_{wsi}.csv")
        create_slide_list(wsi, slide_list_path)

        slide_success = True

        # Stage 1: Segmentation
        seg_cmd = build_seg_command(row, wsi_dir, job_dir)
        seg_cmd[seg_cmd.index("")] = slide_list_path
        if not run_command(seg_cmd, "Tissue Segmentation", wsi):
            slide_success = False
            failed += 1
            results.append({"wsi": wsi, "status": "FAILED", "stage": "segmentation"})
            continue

        # Stage 2: Patch Extraction
        coords_cmd = build_coords_command(row, wsi_dir, job_dir)
        coords_cmd[coords_cmd.index("")] = slide_list_path
        if not run_command(coords_cmd, "Patch Extraction", wsi):
            slide_success = False
            failed += 1
            results.append({"wsi": wsi, "status": "FAILED", "stage": "coords"})
            continue

        # Stage 3: Patch Feature Extraction
        patch_feat_cmd = build_patch_feat_command(row, wsi_dir, job_dir)
        patch_feat_cmd[patch_feat_cmd.index("")] = slide_list_path
        if not run_command(patch_feat_cmd, "Patch Feature Extraction", wsi):
            slide_success = False
            failed += 1
            results.append({"wsi": wsi, "status": "FAILED", "stage": "patch_features"})
            continue

        # Stage 4: Slide Feature Extraction (if slide_encoder specified)
        slide_encoder = row.get("slide_encoder", "").strip()
        if slide_encoder:
            slide_spec = get_slide_encoder_spec(slide_encoder)
            required_patch_encoder = slide_spec["requires_patch_encoder"]

            from src.encoder_registry import get_patch_encoder_spec
            required_spec = get_patch_encoder_spec(required_patch_encoder)
            req_patch_size = str(required_spec["patch_size"])
            req_mag = str(required_spec["mag"])

            # Only run extra steps if slide encoder needs different patch_size
            if req_patch_size != row["patch_size"].strip():
                # Stage 4a: Extract coords at slide encoder's required patch_size
                coords_512_cmd = [
                    "python", TRIDENT_SCRIPT,
                    "--task", "coords",
                    "--wsi_dir", wsi_dir,
                    "--job_dir", job_dir,
                    "--custom_list_of_wsis", slide_list_path,
                    "--mag", req_mag,
                    "--patch_size", req_patch_size,
                    "--overlap", "0",
                ]
                if not run_command(coords_512_cmd, f"Patch Extraction ({req_patch_size}px for {slide_encoder})", wsi):
                    slide_success = False
                    failed += 1
                    results.append({"wsi": wsi, "status": "FAILED", "stage": "slide_coords"})
                    continue

                # Stage 4b: Extract patch features with required patch encoder
                patch_feat_512_cmd = [
                    "python", TRIDENT_SCRIPT,
                    "--task", "feat",
                    "--wsi_dir", wsi_dir,
                    "--job_dir", job_dir,
                    "--custom_list_of_wsis", slide_list_path,
                    "--patch_encoder", required_patch_encoder,
                    "--mag", req_mag,
                    "--patch_size", req_patch_size,
                ]
                if not run_command(patch_feat_512_cmd, f"Patch Features ({required_patch_encoder} for {slide_encoder})", wsi):
                    slide_success = False
                    failed += 1
                    results.append({"wsi": wsi, "status": "FAILED", "stage": "slide_patch_features"})
                    continue

            # Stage 4c: Run slide encoder
            slide_feat_cmd = build_slide_feat_command(row, wsi_dir, job_dir)
            slide_feat_cmd[slide_feat_cmd.index("")] = slide_list_path
            if not run_command(slide_feat_cmd, "Slide Feature Extraction", wsi):
                slide_success = False
                failed += 1
                results.append({"wsi": wsi, "status": "FAILED", "stage": "slide_features"})
                continue

        if slide_success:
            success += 1
            results.append({"wsi": wsi, "status": "SUCCESS"})

        # Clean up temp file
        if os.path.exists(slide_list_path):
            os.remove(slide_list_path)

    # Summary
    elapsed = datetime.now() - start_time
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Total slides: {total}")
    print(f"Successful:   {success}")
    print(f"Failed:       {failed}")
    print(f"Time elapsed: {elapsed}")
    print(f"{'='*60}")

    # Write run report
    report_path = os.path.join(job_dir, f"run_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(report_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wsi", "status", "stage"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"Run report saved: {report_path}")

    return {"total": total, "success": success, "failed": failed, "elapsed": str(elapsed)}
