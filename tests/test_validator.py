"""
Tests for WSI Processing Pipeline config validator.

Each test checks one validation rule using fixture CSV files.
Tests run without GPUs, slide files, or TRIDENT installed.
"""

import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validator import validate_config
from src.encoder_registry import (
    PATCH_ENCODERS,
    SLIDE_ENCODERS,
    VALID_SEGMENTERS,
    get_patch_encoder_spec,
    get_slide_encoder_spec,
    is_valid_segmenter,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# Use a real directory for wsi_dir so the file check works
# In CI, test.svs won't exist, so we create a temp one
WSI_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(autouse=True)
def create_fake_wsi(tmp_path):
    """Create a fake test.svs so the file-exists check passes."""
    fake_wsi = os.path.join(FIXTURES, "test.svs")
    if not os.path.exists(fake_wsi):
        with open(fake_wsi, "w") as f:
            f.write("fake")
        yield
        os.remove(fake_wsi)
    else:
        yield


class TestEncoderRegistry:
    """Tests for the encoder registry lookup functions."""

    def test_valid_patch_encoder(self):
        spec = get_patch_encoder_spec("uni_v2")
        assert spec is not None
        assert spec["patch_size"] == 256
        assert spec["mag"] == 20
        assert spec["embed_dim"] == 1536

    def test_invalid_patch_encoder(self):
        assert get_patch_encoder_spec("fake_encoder") is None

    def test_valid_slide_encoder(self):
        spec = get_slide_encoder_spec("titan")
        assert spec is not None
        assert spec["requires_patch_encoder"] == "conch_v15"

    def test_invalid_slide_encoder(self):
        assert get_slide_encoder_spec("fake_slide") is None

    def test_valid_segmenter(self):
        assert is_valid_segmenter("hest") is True
        assert is_valid_segmenter("grandqc") is True
        assert is_valid_segmenter("otsu") is True

    def test_invalid_segmenter(self):
        assert is_valid_segmenter("fake_seg") is False

    def test_all_patch_encoders_have_required_fields(self):
        for name, spec in PATCH_ENCODERS.items():
            assert "patch_size" in spec, f"{name} missing patch_size"
            assert "mag" in spec, f"{name} missing mag"
            assert "embed_dim" in spec, f"{name} missing embed_dim"

    def test_all_slide_encoders_have_required_fields(self):
        for name, spec in SLIDE_ENCODERS.items():
            assert "requires_patch_encoder" in spec, f"{name} missing requires_patch_encoder"

    def test_slide_encoder_references_valid_patch_encoder(self):
        for name, spec in SLIDE_ENCODERS.items():
            required = spec["requires_patch_encoder"]
            assert required in PATCH_ENCODERS, (
                f"Slide encoder '{name}' requires '{required}' which is not in PATCH_ENCODERS"
            )


class TestValidConfig:
    """Tests that valid configs pass validation."""

    def test_valid_config_passes(self):
        errors = validate_config(os.path.join(FIXTURES, "valid_config.csv"), FIXTURES)
        assert len(errors) == 0


class TestInvalidEncoder:
    """Tests that invalid encoder names are caught."""

    def test_invalid_patch_encoder_caught(self):
        errors = validate_config(os.path.join(FIXTURES, "invalid_encoder.csv"), FIXTURES)
        assert len(errors) > 0
        assert any("patch_encoder" in str(e) for e in errors)


class TestInvalidPatchSize:
    """Tests that wrong patch_size for encoder is caught."""

    def test_wrong_patch_size_caught(self):
        errors = validate_config(os.path.join(FIXTURES, "invalid_patch_size.csv"), FIXTURES)
        assert len(errors) > 0
        assert any("patch_size" in str(e) for e in errors)


class TestInvalidSegmenter:
    """Tests that invalid segmenter names are caught."""

    def test_invalid_segmenter_caught(self):
        errors = validate_config(os.path.join(FIXTURES, "invalid_segmenter.csv"), FIXTURES)
        assert len(errors) > 0
        assert any("segmenter" in str(e) for e in errors)


class TestInvalidBoolean:
    """Tests that invalid boolean values are caught."""

    def test_invalid_boolean_caught(self):
        errors = validate_config(os.path.join(FIXTURES, "invalid_boolean.csv"), FIXTURES)
        assert len(errors) > 0
        assert any("remove_artifacts" in str(e) for e in errors)


class TestMissingColumns:
    """Tests that missing required columns are caught."""

    def test_missing_columns_caught(self):
        errors = validate_config(os.path.join(FIXTURES, "missing_columns.csv"), FIXTURES)
        assert len(errors) > 0
        assert any("Missing required columns" in str(e) for e in errors)


class TestInvalidOverlap:
    """Tests that overlap >= patch_size is caught."""

    def test_overlap_too_large_caught(self):
        errors = validate_config(os.path.join(FIXTURES, "invalid_overlap.csv"), FIXTURES)
        assert len(errors) > 0
        assert any("overlap" in str(e) for e in errors)


class TestMissingFile:
    """Tests that missing CSV file is caught."""

    def test_missing_config_file(self):
        errors = validate_config("nonexistent.csv", FIXTURES)
        assert len(errors) > 0
        assert any("not found" in str(e) for e in errors)

    def test_missing_wsi_file(self):
        errors = validate_config(os.path.join(FIXTURES, "valid_config.csv"), "/nonexistent/dir")
        assert len(errors) > 0
        assert any("wsi" in str(e) for e in errors)
