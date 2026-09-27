"""
Encoder Registry for WSI Processing Pipeline.

Defines valid patch and slide encoders with their required parameters.
The validator checks user configs against this registry to catch
parameter mismatches before consuming GPU time.

Source: https://github.com/mahmoodlab/TRIDENT
"""

# Valid segmentation methods
VALID_SEGMENTERS = {"hest", "grandqc", "otsu"}

# Each patch encoder maps to its required patch_size, mag, and embedding dimension
PATCH_ENCODERS = {
    "conch_v1":         {"patch_size": 256, "mag": 20, "embed_dim": 512},
    "conch_v15":        {"patch_size": 512, "mag": 20, "embed_dim": 768},
    "uni_v1":           {"patch_size": 256, "mag": 20, "embed_dim": 1024},
    "uni_v2":           {"patch_size": 256, "mag": 20, "embed_dim": 1536},
    "ctranspath":       {"patch_size": 256, "mag": 20, "embed_dim": 768},
    "phikon":           {"patch_size": 224, "mag": 20, "embed_dim": 768},
    "phikon_v2":        {"patch_size": 224, "mag": 20, "embed_dim": 1536},
    "resnet50":         {"patch_size": 256, "mag": 20, "embed_dim": 1024},
    "keep":             {"patch_size": 224, "mag": 20, "embed_dim": 768},
    "gigapath":         {"patch_size": 256, "mag": 20, "embed_dim": 1536},
    "gigapath-flash":   {"patch_size": 256, "mag": 20, "embed_dim": 1536},
    "virchow":          {"patch_size": 224, "mag": 20, "embed_dim": 2560},
    "virchow2":         {"patch_size": 224, "mag": 20, "embed_dim": 2560},
    "virchow2-cls":     {"patch_size": 224, "mag": 20, "embed_dim": 2560},
    "hoptimus0":        {"patch_size": 224, "mag": 20, "embed_dim": 1536},
    "hoptimus1":        {"patch_size": 224, "mag": 20, "embed_dim": 1536},
    "h0-mini":          {"patch_size": 224, "mag": 20, "embed_dim": 768},
    "musk":             {"patch_size": 384, "mag": 20, "embed_dim": 1024},
    "openmidnight":     {"patch_size": 224, "mag": 20, "embed_dim": 1536},
    "gpfm":             {"patch_size": 224, "mag": 20, "embed_dim": 1536},
    "hibou_l":          {"patch_size": 224, "mag": 20, "embed_dim": 1024},
    "kaiko-vitb8":      {"patch_size": 256, "mag": 20, "embed_dim": 768},
    "kaiko-vitb16":     {"patch_size": 256, "mag": 20, "embed_dim": 768},
    "kaiko-vits8":      {"patch_size": 256, "mag": 20, "embed_dim": 384},
    "kaiko-vits16":     {"patch_size": 256, "mag": 20, "embed_dim": 384},
    "kaiko-vitl14":     {"patch_size": 256, "mag": 20, "embed_dim": 1024},
    "lunit-vits8":      {"patch_size": 256, "mag": 20, "embed_dim": 384},
    "midnight12k":      {"patch_size": 224, "mag": 20, "embed_dim": 1536},
    "phaet":            {"patch_size": 224, "mag": 20, "embed_dim": 1152},
    "mascaret":         {"patch_size": 224, "mag": 20, "embed_dim": 1152},
    "genbio-pathfm":    {"patch_size": 224, "mag": 20, "embed_dim": 768},
    "gemma4-e4b":       {"patch_size": 224, "mag": 20, "embed_dim": 1152},
    "gemma4-26b":       {"patch_size": 224, "mag": 20, "embed_dim": 3584},
}

# Each slide encoder maps to its required patch encoder
SLIDE_ENCODERS = {
    "threads":          {"requires_patch_encoder": "uni_v1"},
    "titan":            {"requires_patch_encoder": "conch_v15"},
    "prism":            {"requires_patch_encoder": "virchow2"},
    "prism2":           {"requires_patch_encoder": "virchow2"},
    "chief":            {"requires_patch_encoder": "ctranspath"},
    "gigapath":         {"requires_patch_encoder": "gigapath"},
    "gigapath-flash":   {"requires_patch_encoder": "gigapath-flash"},
    "madeleine":        {"requires_patch_encoder": "conch_v15"},
    "feather":          {"requires_patch_encoder": "conch_v15"},
    "feather_uni_v2":   {"requires_patch_encoder": "uni_v2"},
    "care":             {"requires_patch_encoder": "uni_v2"},
    "abmil":            {"requires_patch_encoder": "conch_v15"},
}

# Required CSV columns
REQUIRED_COLUMNS = [
    "wsi",
    "segmenter",
    "remove_artifacts",
    "remove_penmarks",
    "patch_encoder",
    "patch_size",
    "mag",
    "overlap",
    "slide_encoder",
]


def get_patch_encoder_spec(encoder_name: str) -> dict | None:
    """Return the spec for a patch encoder, or None if invalid."""
    return PATCH_ENCODERS.get(encoder_name)


def get_slide_encoder_spec(encoder_name: str) -> dict | None:
    """Return the spec for a slide encoder, or None if invalid."""
    return SLIDE_ENCODERS.get(encoder_name)


def is_valid_segmenter(segmenter: str) -> bool:
    """Check if a segmenter name is valid."""
    return segmenter in VALID_SEGMENTERS
