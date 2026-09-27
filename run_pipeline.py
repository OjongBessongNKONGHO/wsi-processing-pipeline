"""
WSI Processing Pipeline — Entry Point.

Single command to validate a config CSV and run the full TRIDENT
pipeline for every slide listed in it.

Usage:
    python run_pipeline.py <config.csv> <wsi_dir> <job_dir>

Example:
    python run_pipeline.py config/pipeline_config.csv /restricted/projectnb/luadfrp /restricted/projectnb/luadfrp/trident_output
"""

import sys

from src.validator import validate_config
from src.runner import run_pipeline


def main():
    if len(sys.argv) != 4:
        print("Usage: python run_pipeline.py <config.csv> <wsi_dir> <job_dir>")
        print()
        print("Arguments:")
        print("  config.csv  Path to the CSV config file defining slides and parameters")
        print("  wsi_dir     Directory containing the .svs slide files")
        print("  job_dir     Output directory for pipeline results")
        print()
        print("Example:")
        print("  python run_pipeline.py config/pipeline_config.csv /restricted/projectnb/luadfrp /restricted/projectnb/luadfrp/trident_output")
        sys.exit(1)

    config_path = sys.argv[1]
    wsi_dir = sys.argv[2]
    job_dir = sys.argv[3]

    # Step 1: Validate
    print("Validating config...")
    errors = validate_config(config_path, wsi_dir)

    if errors:
        print(f"\nValidation failed with {len(errors)} error(s):\n")
        for error in errors:
            print(f"  ✗ {error}")
        print("\nFix the errors above and try again.")
        sys.exit(1)

    print("✓ Config valid.\n")

    # Step 2: Run
    summary = run_pipeline(config_path, wsi_dir, job_dir)

    if summary["failed"] > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
