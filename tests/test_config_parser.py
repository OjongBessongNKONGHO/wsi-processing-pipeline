"""
Tests for WSI Processing Pipeline config parser.

Tests the researcher-facing run_config.csv parsing and validation.
"""

import os
import sys
import csv
import pytest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_parser import parse_config


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def write_config(tmp_path, rows):
    """Helper to write a config CSV from parameter/value pairs."""
    path = os.path.join(str(tmp_path), "test_config.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value", "options"])
        for param, value in rows:
            writer.writerow([param, value, ""])
    return path


VALID_PARAMS = [
    ("wsi_source", os.path.join(FIXTURES, "test.svs")),
    ("job_dir", "/tmp/trident_output"),
    ("study_name", "NLST"),
    ("segmenter", "hest"),
    ("remove_artifacts", "false"),
    ("remove_penmarks", "false"),
    ("patch_encoder", "uni_v2"),
    ("slide_encoder", "titan"),
    ("batch_size", "5"),
    ("cleanup", "true"),
]


class TestValidConfig:
    """Tests that valid configs parse correctly."""

    def test_valid_config_parses(self, tmp_path):
        path = write_config(tmp_path, VALID_PARAMS)
        settings, errors = parse_config(path)
        assert len(errors) == 0
        assert settings["patch_encoder"] == "uni_v2"
        assert settings["segmenter"] == "hest"
        assert settings["batch_size"] == "5"

    def test_all_segmenters_valid(self, tmp_path):
        for seg in ["hest", "grandqc", "otsu"]:
            params = [(k, v) if k != "segmenter" else (k, seg) for k, v in VALID_PARAMS]
            path = write_config(tmp_path, params)
            _, errors = parse_config(path)
            seg_errors = [e for e in errors if e.parameter == "segmenter"]
            assert len(seg_errors) == 0, f"Segmenter '{seg}' should be valid"

    def test_all_boolean_values(self, tmp_path):
        for flag in ["remove_artifacts", "remove_penmarks", "cleanup"]:
            for val in ["true", "false"]:
                params = [(k, v) if k != flag else (k, val) for k, v in VALID_PARAMS]
                path = write_config(tmp_path, params)
                _, errors = parse_config(path)
                flag_errors = [e for e in errors if e.parameter == flag]
                assert len(flag_errors) == 0


class TestInvalidSegmenter:
    """Tests that invalid segmenters are caught."""

    def test_invalid_segmenter(self, tmp_path):
        params = [(k, v) if k != "segmenter" else (k, "fake_seg") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "segmenter" for e in errors)


class TestInvalidEncoder:
    """Tests that invalid encoders are caught."""

    def test_invalid_patch_encoder(self, tmp_path):
        params = [(k, v) if k != "patch_encoder" else (k, "fake_encoder") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "patch_encoder" for e in errors)

    def test_invalid_slide_encoder(self, tmp_path):
        params = [(k, v) if k != "slide_encoder" else (k, "fake_slide") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "slide_encoder" for e in errors)


class TestInvalidBoolean:
    """Tests that invalid boolean values are caught."""

    def test_invalid_remove_artifacts(self, tmp_path):
        params = [(k, v) if k != "remove_artifacts" else (k, "yes") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "remove_artifacts" for e in errors)

    def test_invalid_cleanup(self, tmp_path):
        params = [(k, v) if k != "cleanup" else (k, "maybe") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "cleanup" for e in errors)


class TestInvalidBatchSize:
    """Tests that invalid batch sizes are caught."""

    def test_zero_batch_size(self, tmp_path):
        params = [(k, v) if k != "batch_size" else (k, "0") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "batch_size" for e in errors)

    def test_negative_batch_size(self, tmp_path):
        params = [(k, v) if k != "batch_size" else (k, "-1") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "batch_size" for e in errors)

    def test_non_integer_batch_size(self, tmp_path):
        params = [(k, v) if k != "batch_size" else (k, "abc") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "batch_size" for e in errors)


class TestMissingParameters:
    """Tests that missing required parameters are caught."""

    def test_missing_patch_encoder(self, tmp_path):
        params = [(k, v) for k, v in VALID_PARAMS if k != "patch_encoder"]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "patch_encoder" for e in errors)

    def test_missing_segmenter(self, tmp_path):
        params = [(k, v) for k, v in VALID_PARAMS if k != "segmenter"]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "segmenter" for e in errors)


class TestMissingFile:
    """Tests that missing config file is caught."""

    def test_missing_config_file(self):
        _, errors = parse_config("nonexistent.csv")
        assert len(errors) > 0
        assert any("not found" in str(e) for e in errors)

    def test_invalid_wsi_source(self, tmp_path):
        params = [(k, v) if k != "wsi_source" else (k, "/fake/path.zip") for k, v in VALID_PARAMS]
        path = write_config(tmp_path, params)
        _, errors = parse_config(path)
        assert any(e.parameter == "wsi_source" for e in errors)
