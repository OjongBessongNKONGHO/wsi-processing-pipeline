"""
Config Parser for WSI Processing Pipeline.

Reads the researcher-facing run_config.csv (parameter/value/options format)
and returns a validated dictionary of pipeline settings.
"""

import csv
import os

from src.encoder_registry import (
    VALID_SEGMENTERS,
    get_patch_encoder_spec,
    get_slide_encoder_spec,
)


class ConfigError:
    """Stores one config error."""

    def __init__(self, parameter: str, value: str, message: str):
        self.parameter = parameter
        self.value = value
        self.message = message

    def __str__(self):
        return f"[{self.parameter}] = '{self.value}': {self.message}"


def parse_config(csv_path: str) -> tuple[dict, list[ConfigError]]:
    """
    Parse the run_config.csv and return settings dict and any errors.

    Args:
        csv_path: Path to the run_config.csv file.

    Returns:
        Tuple of (settings dict, list of errors).
    """
    errors = []
    settings = {}

    if not os.path.exists(csv_path):
        errors.append(ConfigError("file", csv_path, "Config file not found"))
        return settings, errors

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            param = row.get("parameter", "").strip()
            value = row.get("value", "").strip()
            settings[param] = value

    # Validate required parameters exist
    required = [
        "wsi_source", "job_dir", "study_name", "segmenter", "remove_artifacts",
        "remove_penmarks", "patch_encoder", "slide_encoder",
        "batch_size", "cleanup",
    ]
    for param in required:
        if param not in settings or not settings[param]:
            errors.append(ConfigError(param, "", "Required parameter missing"))

    if errors:
        return settings, errors

    # Validate wsi_source
    wsi_source = settings["wsi_source"]
    if not os.path.exists(wsi_source):
        errors.append(ConfigError("wsi_source", wsi_source, "Path does not exist"))

    # Validate job_dir parent exists
    job_parent = os.path.dirname(settings["job_dir"])
    if job_parent and not os.path.exists(job_parent):
        errors.append(ConfigError("job_dir", settings["job_dir"], "Parent directory does not exist"))

    # Validate study_name
    study_name = settings["study_name"]
    if not study_name.replace("_", "").replace("-", "").isalnum():
        errors.append(ConfigError(
            "study_name", study_name,
            "Must contain only letters, numbers, hyphens, or underscores"
        ))

    # Validate segmenter
    segmenter = settings["segmenter"].lower()
    if segmenter not in VALID_SEGMENTERS:
        errors.append(ConfigError(
            "segmenter", segmenter,
            f"Invalid. Choose from: {', '.join(sorted(VALID_SEGMENTERS))}"
        ))

    # Validate booleans
    for flag in ["remove_artifacts", "remove_penmarks", "cleanup"]:
        if settings[flag].lower() not in ("true", "false"):
            errors.append(ConfigError(flag, settings[flag], "Must be 'true' or 'false'"))

    # Validate patch encoder
    patch_encoder = settings["patch_encoder"]
    patch_spec = get_patch_encoder_spec(patch_encoder)
    if not patch_spec:
        errors.append(ConfigError(
            "patch_encoder", patch_encoder,
            "Invalid encoder. See encoder_registry.py for valid options"
        ))

    # Validate slide encoder
    slide_encoder = settings["slide_encoder"]
    if slide_encoder:
        slide_spec = get_slide_encoder_spec(slide_encoder)
        if not slide_spec:
            errors.append(ConfigError(
                "slide_encoder", slide_encoder,
                "Invalid encoder. See encoder_registry.py for valid options"
            ))

    # Validate batch_size
    try:
        batch_size = int(settings["batch_size"])
        if batch_size <= 0:
            errors.append(ConfigError("batch_size", settings["batch_size"], "Must be a positive integer"))
    except ValueError:
        errors.append(ConfigError("batch_size", settings["batch_size"], "Must be an integer"))

    return settings, errors
