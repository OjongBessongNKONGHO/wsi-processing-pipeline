"""
Batch Processor for WSI Processing Pipeline.

Handles the storage-constrained processing of slides from zip files.
Extracts N slides at a time, runs the pipeline, deletes the .svs files,
and repeats until all slides are processed.
"""

import csv
import os
import subprocess
import zipfile
from datetime import datetime

from src.config_parser import parse_config
from src.encoder_registry import get_patch_encoder_spec, get_slide_encoder_spec


TRIDENT_SCRIPT = os.path.expanduser("~/trident/run_batch_of_slides.py")


def get_slides_from_zip(zip_path: str) -> list[str]:
    """List all .svs files inside a zip archive."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        return [f for f in zf.namelist() if f.endswith(".svs")]


def get_slides_from_dir(dir_path: str) -> list[str]:
    """List all .svs files in a directory."""
    return [f for f in os.listdir(dir_path) if f.endswith(".svs")]


def extract_slides(zip_path: str, slide_names: list[str], extract_dir: str) -> list[str]:
    """
    Extract specific slides from a zip to a directory.
    Returns list of extracted file paths.
    """
    os.makedirs(extract_dir, exist_ok=True)
    extracted = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in slide_names:
            zf.extract(name, extract_dir)
            full_path = os.path.join(extract_dir, name)
            extracted.append(full_path)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"  Extracted: {name} ({size_mb:.0f} MB)")

    return extracted


def create_slide_list(slide_filenames: list[str], output_path: str):
    """Create a CSV listing slides for TRIDENT."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["wsi"])
        for name in slide_filenames:
            writer.writerow([name])


def run_trident_stage(cmd: list[str], stage: str) -> bool:
    """Run a TRIDENT command and return True if successful."""
    print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] {stage}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"  FAILED: {stage}")
        return False
    print(f"  COMPLETE: {stage}")
    return True


def process_batch(settings: dict, slide_filenames: list[str], wsi_dir: str) -> dict:
    """
    Run the full pipeline on a batch of slides.

    Args:
        settings: Parsed config settings.
        slide_filenames: List of .svs filenames (just names, not paths).
        wsi_dir: Directory where the .svs files are located.

    Returns:
        Dict with success/failed counts.
    """
    base_job_dir = settings["job_dir"]
    study_name = settings.get("study_name", "").strip()
    if study_name:
        job_dir = os.path.join(base_job_dir, study_name)
    else:
        job_dir = base_job_dir
    os.makedirs(job_dir, exist_ok=True)

    # Create slide list CSV
    slide_list_path = os.path.join(job_dir, "_batch_slide_list.csv")
    create_slide_list(slide_filenames, slide_list_path)

    patch_encoder = settings["patch_encoder"]
    patch_spec = get_patch_encoder_spec(patch_encoder)
    patch_size = str(patch_spec["patch_size"])
    mag = str(patch_spec["mag"])

    # Stage 1: Segmentation
    seg_cmd = [
        "python", TRIDENT_SCRIPT,
        "--task", "seg",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", slide_list_path,
        "--segmenter", settings["segmenter"].lower(),
    ]
    if settings["remove_artifacts"].lower() == "true":
        seg_cmd.append("--remove_artifacts")
    if settings["remove_penmarks"].lower() == "true":
        seg_cmd.append("--remove_penmarks")

    if not run_trident_stage(seg_cmd, "Tissue Segmentation"):
        return {"success": 0, "failed": len(slide_filenames)}

    # Stage 2: Patch Extraction
    coords_cmd = [
        "python", TRIDENT_SCRIPT,
        "--task", "coords",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", slide_list_path,
        "--mag", mag,
        "--patch_size", patch_size,
        "--overlap", "0",
    ]
    if not run_trident_stage(coords_cmd, f"Patch Extraction ({patch_size}px)"):
        return {"success": 0, "failed": len(slide_filenames)}

    # Stage 3: Patch Feature Extraction
    feat_cmd = [
        "python", TRIDENT_SCRIPT,
        "--task", "feat",
        "--wsi_dir", wsi_dir,
        "--job_dir", job_dir,
        "--custom_list_of_wsis", slide_list_path,
        "--patch_encoder", patch_encoder,
        "--mag", mag,
        "--patch_size", patch_size,
    ]
    if not run_trident_stage(feat_cmd, f"Patch Features ({patch_encoder})"):
        return {"success": 0, "failed": len(slide_filenames)}

    # Stage 4: Slide Feature Extraction (if slide_encoder specified)
    slide_encoder = settings.get("slide_encoder", "").strip()
    if slide_encoder:
        slide_spec = get_slide_encoder_spec(slide_encoder)
        required_patch_encoder = slide_spec["requires_patch_encoder"]
        required_spec = get_patch_encoder_spec(required_patch_encoder)
        req_patch_size = str(required_spec["patch_size"])
        req_mag = str(required_spec["mag"])

        # Extract coords at slide encoder's patch_size if different
        if req_patch_size != patch_size:
            coords_slide_cmd = [
                "python", TRIDENT_SCRIPT,
                "--task", "coords",
                "--wsi_dir", wsi_dir,
                "--job_dir", job_dir,
                "--custom_list_of_wsis", slide_list_path,
                "--mag", req_mag,
                "--patch_size", req_patch_size,
                "--overlap", "0",
            ]
            if not run_trident_stage(coords_slide_cmd, f"Patch Extraction ({req_patch_size}px for {slide_encoder})"):
                return {"success": 0, "failed": len(slide_filenames)}

            # Extract patch features with required encoder
            feat_slide_cmd = [
                "python", TRIDENT_SCRIPT,
                "--task", "feat",
                "--wsi_dir", wsi_dir,
                "--job_dir", job_dir,
                "--custom_list_of_wsis", slide_list_path,
                "--patch_encoder", required_patch_encoder,
                "--mag", req_mag,
                "--patch_size", req_patch_size,
            ]
            if not run_trident_stage(feat_slide_cmd, f"Patch Features ({required_patch_encoder} for {slide_encoder})"):
                return {"success": 0, "failed": len(slide_filenames)}

        # Run slide encoder
        slide_feat_cmd = [
            "python", TRIDENT_SCRIPT,
            "--task", "feat",
            "--wsi_dir", wsi_dir,
            "--job_dir", job_dir,
            "--custom_list_of_wsis", slide_list_path,
            "--slide_encoder", slide_encoder,
            "--patch_size", req_patch_size,
            "--mag", req_mag,
        ]
        if not run_trident_stage(slide_feat_cmd, f"Slide Features ({slide_encoder})"):
            return {"success": 0, "failed": len(slide_filenames)}

    # Cleanup temp slide list
    if os.path.exists(slide_list_path):
        os.remove(slide_list_path)

    return {"success": len(slide_filenames), "failed": 0}


def cleanup_slides(file_paths: list[str]):
    """Delete extracted .svs files to free storage."""
    for path in file_paths:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            os.remove(path)
            print(f"  Deleted: {os.path.basename(path)} ({size_mb:.0f} MB freed)")


def run_batch_pipeline(config_path: str):
    """
    Main entry point for batch processing.

    Reads the config, determines if source is zip or directory,
    processes slides in batches with storage management.
    """
    # Parse and validate config
    settings, errors = parse_config(config_path)
    if errors:
        print(f"Config errors:")
        for e in errors:
            print(f"  {e}")
        return

    wsi_source = settings["wsi_source"]
    job_dir = settings["job_dir"]
    batch_size = int(settings["batch_size"])
    cleanup = settings["cleanup"].lower() == "true"
    is_zip = wsi_source.endswith(".zip")

    # Get list of all slides
    if is_zip:
        all_slides = get_slides_from_zip(wsi_source)
        print(f"Found {len(all_slides)} slides in {os.path.basename(wsi_source)}")
    else:
        all_slides = get_slides_from_dir(wsi_source)
        print(f"Found {len(all_slides)} slides in {wsi_source}")

    if not all_slides:
        print("No .svs files found.")
        return

    # Process in batches
    total_success = 0
    total_failed = 0
    total_batches = (len(all_slides) + batch_size - 1) // batch_size
    start_time = datetime.now()

    print(f"\nProcessing {len(all_slides)} slides in {total_batches} batches of {batch_size}")
    print(f"Output: {job_dir}")
    print(f"Cleanup after processing: {cleanup}")

    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(all_slides))
        batch_slides = all_slides[batch_start:batch_end]

        print(f"\n{'='*60}")
        print(f"BATCH {batch_num + 1}/{total_batches} ({len(batch_slides)} slides)")
        print(f"{'='*60}")

        if is_zip:
            # Extract slides from zip
            extract_dir = os.path.join(job_dir, "_temp_extracted")
            print(f"Extracting {len(batch_slides)} slides...")
            extracted_paths = extract_slides(wsi_source, batch_slides, extract_dir)

            # The slides might be in a subdirectory inside the zip (e.g. batch1/)
            # Find the actual directory containing the .svs files
            wsi_dir = extract_dir
            for root, dirs, files in os.walk(extract_dir):
                if any(f.endswith(".svs") for f in files):
                    wsi_dir = root
                    break

            # Get just the filenames for the slide list
            slide_filenames = [os.path.basename(p) for p in extracted_paths]

            # Process
            result = process_batch(settings, slide_filenames, wsi_dir)
            total_success += result["success"]
            total_failed += result["failed"]

            # Cleanup extracted files
            if cleanup:
                print(f"\nCleaning up extracted slides...")
                cleanup_slides(extracted_paths)
                # Remove temp directory if empty
                import shutil
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
        else:
            # Process directly from directory
            slide_filenames = [os.path.basename(s) for s in batch_slides]
            result = process_batch(settings, slide_filenames, wsi_source)
            total_success += result["success"]
            total_failed += result["failed"]

            if cleanup:
                print(f"\nCleaning up processed slides...")
                full_paths = [os.path.join(wsi_source, s) for s in batch_slides]
                cleanup_slides(full_paths)

    # Final summary
    elapsed = datetime.now() - start_time
    print(f"\n{'='*60}")
    print(f"ALL BATCHES COMPLETE")
    print(f"{'='*60}")
    print(f"Total slides:  {len(all_slides)}")
    print(f"Successful:    {total_success}")
    print(f"Failed:        {total_failed}")
    print(f"Time elapsed:  {elapsed}")
    print(f"{'='*60}")

    # Save run report
    report_path = os.path.join(job_dir, f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_path, "w") as f:
        f.write(f"Batch Processing Report\n")
        f.write(f"Source: {wsi_source}\n")
        f.write(f"Total slides: {len(all_slides)}\n")
        f.write(f"Successful: {total_success}\n")
        f.write(f"Failed: {total_failed}\n")
        f.write(f"Batch size: {batch_size}\n")
        f.write(f"Time elapsed: {elapsed}\n")
        f.write(f"Config: {config_path}\n")
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m src.batch_processor config/run_config.csv")
        sys.exit(1)
    run_batch_pipeline(sys.argv[1])
