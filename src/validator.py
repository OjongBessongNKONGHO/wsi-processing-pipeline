"""
Config Validator for WSI Processing Pipeline.

Reads a CSV config file and validates every row against the
encoder registry. Reports all errors before any processing starts
so GPU time is never wasted on bad parameters.
"""

import csv
import os
import sys
from pathlib import Path

from src.encoder_registry import (
    REQUIRED_COLUMNS,
    VALID_SEGMENTERS,
    get_patch_encoder_spec,
    get_slide_encoder_spec,
)


class ValidationError:
    """Stores one validation error with its location."""

    def __init__(self, row: int, column: str, value: str, message: str):
        self.row = row
        self.column = column
        self.value = value
        self.message = message

    def __str__(self):
        return f"Row {self.row} [{self.column}] = '{self.value}': {self.message}"


def validate_config(csv_path: str, wsi_dir: str) -> list[ValidationError]:
    """
    Validate a pipeline config CSV.

    Args:
        csv_path: Path to the CSV config file.
        wsi_dir: Directory where WSI files are located.

    Returns:
        List of ValidationError objects. Empty list means config is valid.
    """
    errors = []

    # Check CSV file exists
    if not os.path.exists(csv_path):
        errors.append(ValidationError(0, "file", csv_path, "Config file not found"))
        return errors

    # Read CSV
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        # Check required columns exist
        if reader.fieldnames is None:
            errors.append(ValidationError(0, "file", csv_path, "Empty CSV file"))
            return errors

        missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing_cols:
            errors.append(
                ValidationError(
                    0, "columns", str(missing_cols),
                    f"Missing required columns: {', '.join(sorted(missing_cols))}"
                )
            )
            return errors

        # Validate each row
        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            errors.extend(_validate_row(i, row, wsi_dir))

    if not errors:
        print(f"Config valid: {csv_path}")

    return errors


def _validate_row(row_num: int, row: dict, wsi_dir: str) -> list[ValidationError]:
    """Validate a single row of the config CSV."""
    errors = []

    # --- WSI file ---
    wsi = row.get("wsi", "").strip()
    if not wsi:
        errors.append(ValidationError(row_num, "wsi", wsi, "WSI filename is empty"))
    else:
        wsi_path = os.path.join(wsi_dir, wsi)
        if not os.path.exists(wsi_path):
            errors.append(
                ValidationError(row_num, "wsi", wsi, f"File not found: {wsi_path}")
            )

    # --- Segmenter ---
    segmenter = row.get("segmenter", "").strip().lower()
    if segmenter not in VALID_SEGMENTERS:
        errors.append(
            ValidationError(
                row_num, "segmenter", segmenter,
                f"Invalid segmenter. Choose from: {', '.join(sorted(VALID_SEGMENTERS))}"
            )
        )

    # --- Boolean flags ---
    for flag in ["remove_artifacts", "remove_penmarks"]:
        value = row.get(flag, "").strip().lower()
        if value not in ("true", "false"):
            errors.append(
                ValidationError(
                    row_num, flag, value,
                    "Must be 'true' or 'false'"
                )
            )

    # --- Patch encoder ---
    patch_encoder = row.get("patch_encoder", "").strip()
    patch_spec = get_patch_encoder_spec(patch_encoder)
    if not patch_spec:
        errors.append(
            ValidationError(
                row_num, "patch_encoder", patch_encoder,
                "Invalid patch encoder. Run: python -c \"from src.encoder_registry import PATCH_ENCODERS; print(list(PATCH_ENCODERS.keys()))\" to see valid options"
            )
        )

    # --- Patch size ---
    patch_size_str = row.get("patch_size", "").strip()
    try:
        patch_size = int(patch_size_str)
        if patch_size <= 0:
            errors.append(
                ValidationError(row_num, "patch_size", patch_size_str, "Must be a positive integer")
            )
        elif patch_spec and patch_size != patch_spec["patch_size"]:
            errors.append(
                ValidationError(
                    row_num, "patch_size", patch_size_str,
                    f"Encoder '{patch_encoder}' requires patch_size={patch_spec['patch_size']}"
                )
            )
    except ValueError:
        errors.append(
            ValidationError(row_num, "patch_size", patch_size_str, "Must be an integer")
        )

    # --- Magnification ---
    mag_str = row.get("mag", "").strip()
    try:
        mag = int(mag_str)
        if mag <= 0:
            errors.append(
                ValidationError(row_num, "mag", mag_str, "Must be a positive integer")
            )
        elif patch_spec and mag != patch_spec["mag"]:
            errors.append(
                ValidationError(
                    row_num, "mag", mag_str,
                    f"Encoder '{patch_encoder}' requires mag={patch_spec['mag']}"
                )
            )
    except ValueError:
        errors.append(
            ValidationError(row_num, "mag", mag_str, "Must be an integer")
        )

    # --- Overlap ---
    overlap_str = row.get("overlap", "").strip()
    try:
        overlap = int(overlap_str)
        if overlap < 0:
            errors.append(
                ValidationError(row_num, "overlap", overlap_str, "Must be zero or positive")
            )
        elif patch_size_str.isdigit() and overlap >= int(patch_size_str):
            errors.append(
                ValidationError(
                    row_num, "overlap", overlap_str,
                    f"Must be less than patch_size ({patch_size_str})"
                )
            )
    except ValueError:
        errors.append(
            ValidationError(row_num, "overlap", overlap_str, "Must be an integer")
        )

    # --- Slide encoder ---
    slide_encoder = row.get("slide_encoder", "").strip()
    if slide_encoder:
        slide_spec = get_slide_encoder_spec(slide_encoder)
        if not slide_spec:
            errors.append(
                ValidationError(
                    row_num, "slide_encoder", slide_encoder,
                    "Invalid slide encoder. Run: python -c \"from src.encoder_registry import SLIDE_ENCODERS; print(list(SLIDE_ENCODERS.keys()))\" to see valid options"
                )
            )
        elif patch_encoder:
            required = slide_spec["requires_patch_encoder"]
            if patch_encoder != required:
                print(
                    f"  Note row {row_num}: Slide encoder '{slide_encoder}' will "
                    f"extract '{required}' features internally (independent of "
                    f"patch_encoder '{patch_encoder}')"
                )

    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m src.validator <config.csv> <wsi_dir>")
        sys.exit(1)

    config_path = sys.argv[1]
    wsi_directory = sys.argv[2]
    validation_errors = validate_config(config_path, wsi_directory)

    if validation_errors:
        print(f"\nValidation failed with {len(validation_errors)} error(s):\n")
        for error in validation_errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    else:
        print("✓ All rows valid. Ready to run.")
        sys.exit(0)
